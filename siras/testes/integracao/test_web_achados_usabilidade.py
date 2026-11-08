"""
Correções vindas da avaliação de usabilidade (novembro de 2026, etapa 22 do roadmap).

Os dois relatos que apontaram o mesmo ponto -- o formulário não deixava claro o que
faltava --, e o que cada teste guarda:

- P5: "ao apertar a tecla enter finaliza o laudo mesmo que com informações
  incompletas". Enter num campo de digitação passa ao próximo; o laudo só sai pelo botão.
- P7: errou um valor e recebeu "só um erro", sem dizer o quê. A recusa do domínio chegava
  com o identificador cru ('ph_agua'), ponto duplo e nenhum campo marcado.

A versão avaliada pelos participantes (tag congelamento-v1) não muda.
"""

import re
import sys
from pathlib import Path

import pytest

from siras.web import criar_app

sys.path.insert(0, str(Path(__file__).parent))
from test_bancada_culturas import _campos_da_tela  # noqa: E402

_ENVIO_JS = (
    Path(__file__).parent.parent.parent / "siras" / "web" / "static" / "js" / "envio.js"
).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cliente():
    return criar_app({"TESTING": True}).test_client()


@pytest.fixture(scope="module")
def formulario(cliente):
    tela = cliente.get("/analise/dados?cultura_id=milho&exemplo=1").get_data(as_text=True)
    campos = _campos_da_tela(tela)
    campos["cultura_id"] = "milho"
    return campos


def _envia(cliente, formulario, **muda):
    dados = dict(formulario)
    dados.update(muda)
    resposta = cliente.post("/analise/laudo", data=dados)
    html = resposta.get_data(as_text=True)
    aviso = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    aviso = aviso[aviso.find("O laudo não foi gerado"):][:220]
    marcados = [m.strip() for m in re.findall(
        r'campo--erro[^>]*>\s*<span class="campo__label">\s*([^<]+)', html)]
    return resposta.status_code, aviso, marcados, html


@pytest.mark.parametrize("campo, valor, rotulo", [
    ("ph_agua", "15", "pH em água"),
    ("indice_smp", "8.5", "Índice SMP"),
    ("v_percent", "140", "Saturação por bases"),
])
def test_valor_fora_da_faixa_volta_com_o_nome_do_campo_e_o_campo_marcado(
        cliente, formulario, campo, valor, rotulo):
    status, aviso, marcados, _ = _envia(cliente, formulario, **{campo: valor})

    assert status == 422
    assert f"{rotulo}: fora da faixa física plausível" in aviso
    assert f"'{campo}'" not in aviso, "identificador cru na tela"
    assert ".." not in aviso
    assert rotulo in marcados


def test_erro_na_subsuperficie_abre_o_bloco_e_marca_o_campo(cliente, formulario):
    status, aviso, marcados, html = _envia(cliente, formulario, sub_ph_agua="20")

    assert status == 422
    assert "pH em água (10-20 cm): fora da faixa física plausível" in aviso
    assert "pH em água (10-20 cm)" in marcados
    assert '<details class="painel bloco" open>' in html


def test_enter_passa_ao_proximo_campo_e_nao_envia():
    assert 'evento.key !== "Enter"' in _ENVIO_JS
    bloco = _ENVIO_JS[_ENVIO_JS.index("ENTER PASSA AO PROXIMO CAMPO"):]
    assert "evento.preventDefault()" in bloco
    assert "proximo.focus()" in bloco
    # A composição de acentos não é interrompida, e só campos de digitação mudam.
    assert "evento.isComposing" in bloco
    assert 'alvo.tagName !== "INPUT"' in bloco
