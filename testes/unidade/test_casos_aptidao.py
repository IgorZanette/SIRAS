"""
Executa os casos de testes/casos/casos_aptidao.json contra o motor real
(siras/motor/aptidao.py) — a verificação de conformidade do CCAE (CCAE-v1.0.md Sec. 9).

Só contam casos com "conferido_por_autor_em" preenchido: é a evidência de que o
"referencia" foi calculado à mão pelo autor a partir do Manual, sem consultar o código
(CLAUDE.md, regra absoluta de dados agronômicos). O arquivo hoje só tem o caso-modelo
(conferido_por_autor_em=null) — nenhum teste real é coletado até o autor preencher casos,
o que é o comportamento esperado, não uma falha.
"""

import json
from pathlib import Path

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.aptidao import avaliar_aptidao
from siras.motor.trace import Trace

_CAMINHO_CASOS = Path(__file__).parent.parent / "casos" / "casos_aptidao.json"

_CAMPOS_ANALISE = (
    "ph_agua", "indice_smp", "argila", "mo", "p", "k", "ctc_ph7", "al", "ca", "mg", "v_percent",
)


def _carregar_casos_conferidos():
    casos = json.loads(_CAMINHO_CASOS.read_text(encoding="utf-8"))
    return [c for c in casos if c.get("conferido_por_autor_em")]


def _construir_analise(entrada: dict) -> AnaliseSolo:
    campos = {chave: entrada[chave] for chave in _CAMPOS_ANALISE if chave in entrada}
    return AnaliseSolo(**campos)


def _construir_contexto(entrada: dict) -> Contexto:
    return Contexto(
        cultura_id=entrada["cultura"],
        sistema_manejo=entrada.get("sistema_manejo", "convencional"),
        condicao_area=entrada.get("condicao_area", "todos os casos"),
        prnt=entrada.get("prnt", 100.0),
        profundidade_incorporacao_cm=entrada.get("profundidade_incorporacao_cm", 20.0),
    )


@pytest.mark.parametrize("caso", _carregar_casos_conferidos(), ids=lambda c: c["id"])
def test_caso_bate_com_a_referencia(caso):
    dados = carregar_dados_comum()
    analise = _construir_analise(caso["entrada"])
    contexto = _construir_contexto(caso["entrada"])
    trace = Trace()

    resultado = avaliar_aptidao(analise, caso["entrada"]["cultura"], caso["cenario"], contexto, trace, dados=dados)

    assert resultado.classe == caso["referencia"]["classe_aptidao"], (
        f"{caso['id']}: esperado {caso['referencia']['classe_aptidao']}, obtido "
        f"{resultado.classe} (determinante: {resultado.fator_determinante})"
    )
    if caso["referencia"].get("fator_determinante"):
        assert resultado.fator_determinante == caso["referencia"]["fator_determinante"], (
            f"{caso['id']}: classe bateu mas pelo fator errado — esperado "
            f"{caso['referencia']['fator_determinante']}, obtido {resultado.fator_determinante}"
        )
