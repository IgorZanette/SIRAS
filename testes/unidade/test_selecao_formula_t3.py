"""
T3 — regressão da proporção 60:120. ESCRITO ANTES DO CÓDIGO.

O plano v2 determina que este caso seja escrito antes da implementação, e o motivo é o
que ele guarda: uma recomendação em que o potássio pede o dobro do fósforo, com uma
fórmula de teores iguais em P e K. É a situação em que a escolha do ponto de quebra
decide, e em que a regra errada passa despercebida porque o resultado continua
plausível.

Conta à mão, com a fórmula 05-25-25 e a recomendação N 120 · P2O5 60 · K2O 120:

  ponto de quebra pelo P:  60 × 100 / 25 = 240 kg/ha
      entrega P 60 (na medida), K 60 → falta 60
      custo = 0 excesso + 0,2 × 60 de falta + 10 de uma operação = 22

  ponto de quebra pelo K: 120 × 100 / 25 = 480 kg/ha
      entrega K 120 (na medida), P 120 → excesso 60
      custo = 1,0 × 60 de excesso + 0 de falta + 0 operação = 60

Vence 240. O K que falta sai como cloreto de potássio: 60 × 100 / 58 = 103 kg/ha.
O N entregue é 240 × 5% = 12; faltam 108 dos 120, que viram ureia: 108 × 100 / 45 = 240.

Nenhum nutriente fica em excesso.

Este arquivo é separado de test_formulacao.py de propósito, e assim permanece: é o
registro de que o caso existiu antes da implementação que ele verifica.
"""

import pytest

from siras.dominio.laudo import RecomendacaoAdubacao
from siras.motor.formulacao import recomendar_formulacao

_SIMPLES = [
    {"id": "ureia", "n": 45, "p2o5": 0, "k2o": 0, "uso": ["cobertura_n"]},
    {"id": "superfosfato_triplo", "n": 0, "p2o5": 41, "k2o": 0, "uso": ["complemento_p"]},
    {"id": "cloreto_de_potassio", "n": 0, "p2o5": 0, "k2o": 58, "uso": ["complemento_k"]},
]

_CATALOGO = {
    "fontes": {"teste": "fórmula fictícia de teste"},
    "fertilizantes_simples": {"_fonte": "teste", "itens": _SIMPLES},
    "formulas": {"itens": [{
        "id": "05-25-25", "n": 5, "p2o5": 25, "k2o": 25, "uso": ["plantio"],
        "fontes": ["teste"], "origem": "composicao_ilustrativa",
    }]},
}

_RECOMENDACAO = RecomendacaoAdubacao(
    n=120, p2o5=60, k2o=120, classe_p="muito_baixo", classe_k="muito_baixo"
)


@pytest.fixture(scope="module")
def opcao():
    resultado = recomendar_formulacao(_RECOMENDACAO, _CATALOGO)
    return resultado.catalogo[0]


def test_dose_ancora_no_fosforo_e_nao_no_potassio(opcao):
    """240 kg/ha, e não 480: ancorar no K custaria 60 contra 22."""
    assert opcao.dose_kg_ha == pytest.approx(240.0)
    assert opcao.ancora == "p2o5"


def test_o_potassio_que_falta_vira_cloreto_de_potassio(opcao):
    kcl = next(c for c in opcao.complementos if c.produto == "cloreto_de_potassio")

    assert round(kcl.dose_kg_ha) == 103
    assert kcl.momento == "plantio"


def test_o_nitrogenio_restante_vira_ureia_em_cobertura(opcao):
    ureia = next(c for c in opcao.complementos if c.produto == "ureia")

    assert round(ureia.dose_kg_ha) == 240
    assert ureia.momento == "cobertura"


def test_nenhum_nutriente_fica_em_excesso(opcao):
    assert opcao.excesso["n"] == pytest.approx(0.0)
    assert opcao.excesso["p2o5"] == pytest.approx(0.0)
    assert opcao.excesso["k2o"] == pytest.approx(0.0)


def test_o_custo_e_o_da_conta_a_mao(opcao):
    # 0,2 × 60 kg de falta de K, mais 10 da operação do cloreto de potássio.
    assert opcao.custo == pytest.approx(22.0)
