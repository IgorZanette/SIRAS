"""
Executa os casos de testes/casos/casos_recomendacao.json contra o motor real
(siras/motor/calagem.py e siras/motor/adubacao.py). Liga o oráculo calculado pelo autor
à implementação — não são só exemplos, são a prova de que o motor bate com o Manual.

Escopo: resolução cultura -> critério ainda não passa por resolver_criterio_id() aqui
(decisão A2, docs/ROADMAP.md — os condicao_area dos casos são atalhos que não batem com
o texto completo guardado em criterios_calagem.json). Os testes chamam calcular_calagem()
direto com o criterio_id correspondente, testando o cálculo, não a resolução.
"""

import json
from pathlib import Path

import pytest

from siras.dominio.analise import AnaliseSolo, Camada, Contexto
from siras.motor.adubacao import calcular_fosforo_potassio, calcular_nitrogenio
from siras.motor.calagem import calcular_calagem
from siras.motor.trace import Trace

_CAMINHO_CASOS = Path(__file__).parent.parent / "casos" / "casos_recomendacao.json"

_CRITERIO_POR_CASO = {
    "CAL-01": "graos_convencional",
    "CAL-02": "graos_pd_consolidado",
    "CAL-03": "graos_convencional",
    "CAL-04": "graos_pd_consolidado",
    "CAL-05": "graos_convencional",
    "CAL-06": "graos_convencional",
    "CAL-07": "macieira_oliveira",
    "CAL-08": "erva_mate_e_florestais",
    "CAL-09": "erva_mate_e_florestais",
    "CAL-10": "graos_pd_com_restricoes",
    "CAL-11": "graos_pd_com_restricoes",
    "ADU-01": "graos_convencional",
}

_CAMPOS_ANALISE_PADRAO = dict(
    ph_agua=7.0, indice_smp=6.0, argila=0.0, mo=0.0, p=0.0, k=0.0, ctc_ph7=0.0,
    al=0.0, ca=0.0, mg=0.0, v_percent=0.0, saturacao_al=None,
)


def _carregar_casos():
    dados = json.loads(_CAMINHO_CASOS.read_text(encoding="utf-8"))
    return dados["casos"]


def _construir_analise(entrada: dict) -> AnaliseSolo:
    campos = dict(_CAMPOS_ANALISE_PADRAO)
    for chave, valor in entrada.items():
        if chave in campos:
            campos[chave] = valor
    if "subsuperficie" in entrada:
        campos["subsuperficie"] = Camada(**entrada["subsuperficie"])
    return AnaliseSolo(**campos)


def _construir_contexto(entrada: dict) -> Contexto:
    return Contexto(
        cultura_id=entrada["cultura"],
        sistema_manejo=entrada["sistema_manejo"],
        condicao_area=entrada.get("condicao_area", "nao se aplica (teste chama calcular_calagem direto)"),
        prnt=entrada["prnt"],
        profundidade_incorporacao_cm=entrada["profundidade_incorporacao_cm"],
    )


@pytest.mark.parametrize("caso", _carregar_casos(), ids=lambda c: c["id"])
def test_caso_bate_com_referencia_e_verificacao_cruzada(caso):
    assert caso["conferido_por_autor_em"] is not None, (
        f"{caso['id']}: conferido_por_autor_em ainda é null — não vale como validação "
        f"(ver instrucoes em casos_recomendacao.json)"
    )
    assert caso["referencia"] == caso["verificacao_cruzada"], (
        f"{caso['id']}: referencia diverge de verificacao_cruzada — investigar qual dos "
        f"dois está errado antes de confiar no caso"
    )

    entrada = caso["entrada"]
    criterio_id = _CRITERIO_POR_CASO[caso["id"]]
    analise = _construir_analise(entrada)
    contexto = _construir_contexto(entrada)
    trace = Trace()

    resultado = calcular_calagem(analise, criterio_id, contexto, trace)

    assert resultado["nc_t_ha"] == caso["referencia"]["nc_t_ha"], (
        f"{caso['id']}: nc_t_ha esperado {caso['referencia']['nc_t_ha']}, "
        f"obtido {resultado['nc_t_ha']}"
    )
    if "motivo_sem_calagem" in caso["referencia"]:
        assert resultado["motivo"] == caso["referencia"]["motivo_sem_calagem"], (
            f"{caso['id']}: motivo esperado {caso['referencia']['motivo_sem_calagem']}, "
            f"obtido {resultado['motivo']}"
        )


def test_adu_01_adubacao_completa():
    casos = {c["id"]: c for c in _carregar_casos()}
    caso = casos["ADU-01"]
    entrada = caso["entrada"]
    referencia = caso["referencia"]

    resultado_n = calcular_nitrogenio(entrada["cultura"], mo=entrada["mo"])
    resultado_pk = calcular_fosforo_potassio(
        cultura_id=entrada["cultura"],
        argila=entrada["argila"],
        p_solo=entrada["p"],
        ctc_ph7=entrada["ctc_ph7"],
        k_solo=entrada["k"],
        cultivo=entrada["cultivo"],
        expectativa_rendimento=entrada.get("expectativa_rendimento"),
    )

    assert resultado_n["n"] == referencia["n"]
    assert resultado_pk["classe_p"] == referencia["classe_p"]
    assert resultado_pk["classe_k"] == referencia["classe_k"]
    assert resultado_pk["p2o5"] == referencia["p2o5"]
    assert resultado_pk["k2o"] == referencia["k2o"]
