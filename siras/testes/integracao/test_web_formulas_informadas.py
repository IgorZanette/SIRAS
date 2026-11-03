"""
As fórmulas que o usuário informa, de ponta a ponta pela web.

Reproduz o piloto de 02/11/2026: a pessoa informou as fórmulas que tinha na revenda, e
(a) o laudo não as mostrava quando o catálogo tinha opção melhor, (b) "5 25 25" era
recusado por formato, e (c) uma fórmula impossível trazia o conselho de conferir "a
unidade no laudo do laboratório", que não se aplica a rótulo de adubo.
"""

import re

import pytest

from siras.web import criar_app
from testes.integracao.test_bancada_cenarios import _montar


@pytest.fixture(scope="module")
def cliente():
    return criar_app({"TESTING": True}).test_client()


@pytest.fixture(scope="module")
def formulario_milho(cliente):
    html = cliente.get("/analise/dados?cultura_id=milho&exemplo=1").get_data(as_text=True)
    return _montar(html, "milho", 1)


def _laudo(cliente, campos, formulas):
    dados = dict(campos)
    dados["formula_usuario"] = list(formulas)
    return cliente.post("/analise/laudo", data=dados)


def test_as_formulas_informadas_aparecem_no_laudo_mesmo_quando_o_catalogo_e_melhor(
    cliente, formulario_milho
):
    resposta = _laudo(cliente, formulario_milho, ["5 25 25", "18 18 18"])
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert "As fórmulas que você informou" in html
    assert "05-25-25" in html and "18-18-18" in html


def test_formula_impossivel_e_recusada_sem_o_conselho_do_laboratorio(cliente, formulario_milho):
    resposta = _laudo(cliente, formulario_milho, ["40-50-60"])
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 422
    assert "soma 150%" in html
    assert "Confira a unidade no laudo do laboratório" not in html


def test_o_campo_carrega_a_mascara(cliente):
    html = cliente.get("/analise/dados?cultura_id=milho").get_data(as_text=True)

    assert re.search(r'src="[^"]*js/formulas\.js"', html)
