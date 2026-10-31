"""
Consolidação do questionário de usabilidade, lida a partir do CSV que o Google Forms exporta.

Duas armadilhas do formato justificam estes testes:

- o Forms usa o enunciado como nome da coluna. Se as dez heurísticas tivessem a mesma
  pergunta, o CSV teria dez colunas de mesmo nome, e o leitor de CSV guardaria só a
  última — as dez heurísticas virariam uma. Por isso os enunciados levam "H1 —" a "H10 —";
- a severidade é múltipla escolha, e o Forms exporta a opção inteira ("3 — Problema
  grave"), além de "Não observei", que não é nota e não pode virar zero.
"""

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from consolidar_heuristicas import (  # noqa: E402
    ErroConsolidacao,
    _nota,
    carregar,
    colunas_de_perfil,
    consolidar,
)

#: Os enunciados do questionario.md, na ordem em que o Forms os exporta.
_PERFIL = [
    "Código do participante (eu te passo na hora do teste — P1, P2, ...)",
    "Qual a tua formação/atuação?",
    "Há quanto tempo tu trabalhas com análise de solo ou recomendação de adubação?",
    "Como tu fazes a recomendação hoje?",
    "Qual o teu conforto com ferramentas digitais no trabalho?",
    "Como tu usaste o sistema?",
    "Tu já conhecias o SIRAS antes deste teste?",
]
_ABERTAS = [
    "Se tu pudesses mudar uma coisa só no SIRAS, qual seria?",
    "Tu usarias essa ferramenta no teu trabalho? Por quê — ou por que não?",
    "Sobre a ferramenta: ela é confiável, clara, útil?",
    "Sobre a recomendação agronômica que ela gerou: tu concordas com ela? "
    "Recomendarias ao produtor como está?",
    "Falta alguma coisa no sistema para que ele servisse à tua rotina de verdade? O quê?",
]


def _heuristica(n):
    return [
        f"H{n} — Qual a gravidade dos problemas que tu encontraste neste aspecto?",
        f"H{n} — Descreve o que deu errado e em que tela aconteceu.",
        f"H{n} — O que tu farias diferente?",
    ]


def _cabecalho():
    colunas = ["Carimbo de data/hora"] + _PERFIL
    for n in range(1, 11):
        colunas += _heuristica(n)
    return colunas + _ABERTAS


def _gravar(caminho, cabecalho, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)
    return caminho


def _resposta(codigo, severidades, relato_h7=("", "")):
    """Uma linha do CSV: as severidades das dez heurísticas e, opcionalmente, um relato
    na H7. As abertas finais vêm preenchidas — com palavras que não podem confundir a
    detecção das colunas das heurísticas."""
    linha = ["18/10/2026 10:00:00", codigo, "Engenheiro(a) agrônomo(a)", "2 a 5 anos",
             "À mão, com o Manual", "Confortável", "Presencialmente", "Não"]
    for n, severidade in enumerate(severidades, start=1):
        falha, sugestao = relato_h7 if n == 7 else ("", "")
        linha += [severidade, falha, sugestao]
    return linha + ["a trilha", "sim", "clara", "concordo", "nada"]


@pytest.mark.parametrize("valor, esperado", [
    ("0 — Não é problema", 0),
    ("3 — Problema grave: atrapalha muito e atrasa o trabalho", 3),
    ("4", 4),
    ("2,0", 2),
    ("1.0", 1),
    ("Não observei", None),
    ("", None),
    ("5", None),
    ("10", None),
])
def test_nota_le_o_digito_inicial_da_opcao(valor, esperado):
    assert _nota(valor) == esperado


def test_colunas_de_mesmo_nome_sao_recusadas_com_explicacao(tmp_path):
    """Sem o prefixo H1-H10, as dez perguntas teriam o mesmo texto. O erro tem de aparecer
    na hora, e não como uma consolidação silenciosamente errada."""
    repetido = ["Código do participante"]
    for _ in range(10):
        repetido += ["Qual a gravidade dos problemas que tu encontraste neste aspecto?"]
    caminho = _gravar(tmp_path / "r.csv", repetido, [["P1"] + ["2"] * 10])

    with pytest.raises(ErroConsolidacao, match="mesmo nome"):
        carregar(caminho)


def test_consolida_por_heuristica_e_separa_nao_observado(tmp_path):
    graves = ["1 — Problema estético", "0 — Não é problema"] + ["2 — Problema leve"] * 8
    graves[6] = "3 — Problema grave"
    observou_pouco = list(graves)
    observou_pouco[6] = "Não observei"

    caminho = _gravar(tmp_path / "r.csv", _cabecalho(), [
        _resposta("P1", graves, relato_h7=("faltou repetir a análise", "um botão de duplicar")),
        _resposta("P2", observou_pouco),
    ])
    dados = consolidar(carregar(caminho))

    assert dados["respondentes"] == 2
    h = {item["numero"]: item for item in dados["heuristicas"]}

    assert h[1]["notas"] == [1, 1]
    assert h[2]["notas"] == [0, 0]
    # "Não observei" não vira zero: fica fora da média e é contado à parte.
    assert h[7]["notas"] == [3]
    assert h[7]["nao_observado"] == 1
    assert h[1]["nao_observado"] == 0

    assert h[7]["relatos"] == [{
        "codigo": "P1", "nota": "3",
        "falha": "faltou repetir a análise", "sugestao": "um botão de duplicar",
    }]
    # Nenhuma pergunta aberta final foi lida como relato de heurística.
    assert all(not h[n]["relatos"] for n in range(1, 11) if n != 7)


def test_perfil_inclui_a_pergunta_de_conhecimento_previo():
    perfil = colunas_de_perfil(_cabecalho())
    assert "Tu já conhecias o SIRAS antes deste teste?" in perfil
    assert not any("gravidade" in c for c in perfil)
