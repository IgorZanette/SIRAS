"""
Verdes claros no tema claro — débito 9 do roadmap.

`scripts/conferir_contraste.py` mede `--v-200` a `--v-500` abaixo de 3:1 sobre o fundo
claro. O script mede a paleta, não o uso: diz que esses tons reprovam, e não onde a
interface os usa. Este teste faz a outra metade — varre as folhas de estilo e exige que
todo uso desses tons tenha, no tema claro, uma substituição que não seja outro verde claro.

A varredura achou o que importava: os indicadores de foco. O anel global e o do "i"
usavam `--v-400` (1,51:1), e a borda do campo em foco perdia para a regra do tema claro,
de especificidade maior, ficando quase invisível. Foco que não se vê reprova WCAG 2.4.7 e
1.4.11.

O que fica de propósito está em `_PERMITIDOS`, cada item com o motivo. Um uso novo de
verde claro sem substituição no tema claro faz este teste falhar — e a decisão passa a ser
tomada na hora, em vez de descoberta na avaliação de usabilidade.
"""

import re
import sys
from pathlib import Path

import pytest

_RAIZ = Path(__file__).parent.parent.parent
_CSS = _RAIZ / "siras" / "web" / "static" / "css"
_FOLHAS = ("siras-theme.css", "siras-telas.css")

sys.path.insert(0, str(_RAIZ / "scripts"))
from conferir_contraste import contraste  # noqa: E402

_CLARO = ':root[data-tema="claro"]'
_VERDE_CLARO = re.compile(r"var\(--v-(200|300|400|500)\)")

#: Usos de verde claro que continuam no tema claro, e por quê.
_PERMITIDOS = {
    (".btn--primario", "background"):
        "quem identifica o botão é o texto escuro sobre o fundo, e não o contraste do "
        "fundo contra a página",
    (".btn--primario:hover", "background"):
        "mesmo motivo do botão primário; o hover muda o tom sem mudar o que identifica "
        "o botão",
    (".btn[disabled]:hover", "background"):
        "controle desabilitado não é estado de interação (exceção da WCAG 1.4.11)",
}


def _familia(propriedade: str) -> str:
    for base in ("outline", "border", "background", "fill", "stroke", "color"):
        if propriedade == base or propriedade.startswith(base + "-"):
            return base
    return propriedade


def _declaracoes():
    """(seletor, família da propriedade, valor), na ordem em que aparecem."""
    texto = "\n".join((_CSS / nome).read_text(encoding="utf-8") for nome in _FOLHAS)
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    for seletores, corpo in re.findall(r"([^{}@]+)\{([^{}]*)\}", texto):
        for seletor in seletores.split(","):
            seletor = " ".join(seletor.split())
            if not seletor:
                continue
            for declaracao in corpo.split(";"):
                if ":" not in declaracao:
                    continue
                propriedade, valor = (parte.strip() for parte in declaracao.split(":", 1))
                if propriedade.startswith("--"):
                    continue
                yield seletor, _familia(propriedade), valor


def _usos_sem_substituicao():
    finais = {}
    claro = {}
    for seletor, familia, valor in _declaracoes():
        if seletor.startswith(_CLARO):
            alvo = seletor[len(_CLARO):].strip()
            claro.setdefault(alvo, {})[familia] = valor
        elif not seletor.startswith(":root") and not seletor.startswith("body.impressa"):
            finais[(seletor, familia)] = valor   # a última declaração vence

    problemas = []
    for (seletor, familia), valor in finais.items():
        if not _VERDE_CLARO.search(valor):
            continue
        substituicoes = [
            regras[familia] for alvo, regras in claro.items()
            if familia in regras and (alvo == seletor or alvo.endswith(" " + seletor))
        ]
        if any(not _VERDE_CLARO.search(sub) for sub in substituicoes):
            continue
        if (seletor, familia) in _PERMITIDOS:
            continue
        problemas.append(f"{seletor} [{familia}] = {valor}")
    return problemas


def test_todo_verde_claro_tem_substituicao_no_tema_claro():
    problemas = _usos_sem_substituicao()

    assert not problemas, (
        "verde claro sem substituição no tema claro — decida e registre em _PERMITIDOS "
        "ou dê ao seletor um tom que passe 3:1:\n  " + "\n  ".join(problemas)
    )


@pytest.mark.parametrize("seletor", [":focus-visible", ".dica__gatilho:focus-visible"])
def test_o_anel_de_foco_e_visivel_no_tema_claro(seletor):
    """Foco que não se vê reprova WCAG 2.4.7 — e é o que guia quem navega pelo teclado."""
    telas = (_CSS / "siras-telas.css").read_text(encoding="utf-8")

    assert re.search(
        re.escape(f"{_CLARO} {seletor}") + r" \{ outline-color: var\(--v-700\); \}", telas
    )


def test_o_campo_em_foco_tem_borda_visivel_no_tema_claro():
    """A borda de foco perdia para a regra do tema claro, de especificidade maior."""
    telas = (_CSS / "siras-telas.css").read_text(encoding="utf-8")

    assert re.search(r"\.campo__caixa:focus-within \{\s*border-color: var\(--v-700\)", telas)


def test_o_foco_nao_esconde_a_borda_do_campo_invalido():
    """O erro é informação: o foco não pode escondê-lo quando a pessoa volta para corrigir."""
    telas = (_CSS / "siras-telas.css").read_text(encoding="utf-8")

    assert ":not(.campo--invalido):not(.campo--erro) .campo__caixa:focus-within" in telas


@pytest.mark.parametrize("fundo", ["#F6F8F5", "#FFFFFF"])
def test_o_verde_do_foco_passa_o_piso_nos_fundos_claros(fundo):
    """--v-700 é o tom usado no foco: precisa de 3:1 contra o fundo e contra o painel."""
    assert contraste("#34701F", fundo) >= 3.0
