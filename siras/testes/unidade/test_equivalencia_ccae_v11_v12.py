"""
CCAE v1.1 e v1.2 dão o mesmo resultado — débito 5 do roadmap.

A v1.2 mudou a DERIVAÇÃO do F1 no ramo (b), e não a regra: a v1.1 decidia pelo gatilho
(V% abaixo do limiar), a v1.2 decide pela dose (NC > 0). O Apêndice C afirma que o
conjunto de conformidade executado sob a v1.1 continua válido porque as duas derivações
coincidem em todo o domínio, inclusive na fronteira V% = 40 — e registra que isso "é
verificável por execução: rodar o conjunto sob as duas versões e obter saídas iguais
transforma-a de argumento em resultado medido".

Este arquivo é essa execução. Só é possível porque o operador passou a ser dado
(`F1_acidez.sem_ph_referencia.tipo`, débito 1): a troca de versão é trocar um valor numa
cópia da base em memória, sem tocar em `dados/` e sem manter dois motores.

O que se compara é o resultado inteiro, e não só a classe: grau, fator determinante, grau
e evidência de cada um dos sete fatores, e alertas.
"""

import copy
import json
import pathlib

import pytest

import siras.motor.aptidao as modulo_aptidao
from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.aptidao import _MANEJO_PARA_CONTEXTO, avaliar_aptidao, avaliar_aptidao_ccae
from siras.motor.trace import Trace

_CASOS = pathlib.Path(__file__).resolve().parents[1] / "casos"
_V11, _V12 = "v_menor_que", "nc_maior_que_zero"


def _dados_com_regra(tipo: str) -> dict:
    dados = copy.deepcopy(carregar_dados_comum())
    dados["criterios_aptidao"]["F1_acidez"]["sem_ph_referencia"]["tipo"] = tipo
    return dados


def _assinatura(resultado):
    return (
        resultado.classe,
        resultado.grau_final,
        resultado.fator_determinante,
        tuple((f.id, f.grau, f.rotulo, f.evidencia) for f in resultado.fatores),
        tuple(resultado.alertas),
    )


def test_a_regra_vigente_na_base_e_a_da_v12():
    sem = carregar_dados_comum()["criterios_aptidao"]["F1_acidez"]["sem_ph_referencia"]

    assert sem["tipo"] == _V12


def test_o_conjunto_de_conformidade_da_saidas_iguais_sob_v11_e_v12(monkeypatch):
    """Todos os casos do conjunto, nos dois cenários, sob as duas versões."""
    entradas = json.loads(
        (_CASOS / "entradas_aptidao.json").read_text(encoding="utf-8")
    )["casos"]

    saidas = {}
    for tipo in (_V11, _V12):
        dados = _dados_com_regra(tipo)
        monkeypatch.setattr(modulo_aptidao, "carregar_dados_comum", lambda d=dados: d)
        saidas[tipo] = {
            (caso["id_caso"], cenario): _assinatura(
                avaliar_aptidao_ccae(analise=caso["entrada"], cultura=caso["cultura"], cenario=cenario)
            )
            for caso in entradas
            for cenario in ("ATUAL", "POTENCIAL")
        }

    assert len(saidas[_V11]) == 2 * len(entradas)
    divergentes = sorted(chave for chave in saidas[_V11] if saidas[_V11][chave] != saidas[_V12][chave])
    assert not divergentes, f"a v1.1 e a v1.2 divergem em: {divergentes}"


_CULTURAS_RAMO_B = ("erva_mate", "eucalipto", "acacia_negra", "pastagem_natural")
_V = (0.0, 20.0, 39.0, 39.9, 39.99, 39.999999, 40.0, 40.000001, 40.1, 75.0, 100.0)
_CTC = (0.1, 3.8, 10.0, 60.0)
_CA_MG = ((3.0, 0.8), (4.0, 1.0), (4.0, 0.9))


@pytest.mark.parametrize("cultura", _CULTURAS_RAMO_B)
def test_a_fronteira_do_v40_e_a_mesma_nas_duas_derivacoes(cultura):
    """O conjunto de conformidade tem um caso só exatamente em V% = 40. A fronteira merece
    mais que um ponto: logo abaixo, exatamente nela e logo acima, em CTC baixa e alta, com
    a exceção Ca/Mg satisfeita e não satisfeita."""
    sistema_manejo, condicao_area = _MANEJO_PARA_CONTEXTO["convencional"]
    contexto = Contexto(
        cultura_id=cultura, sistema_manejo=sistema_manejo, condicao_area=condicao_area,
        prnt=100.0, profundidade_incorporacao_cm=20.0,
    )
    por_regra = {tipo: _dados_com_regra(tipo) for tipo in (_V11, _V12)}

    pontos = 0
    for v_percent in _V:
        for ctc in _CTC:
            for ca, mg in _CA_MG:
                analise = AnaliseSolo(
                    ph_agua=5.0, indice_smp=5.5, argila=30, mo=3.0, p=12.0, k=80,
                    ctc_ph7=ctc, al=0.2, ca=ca, mg=mg, v_percent=v_percent,
                )
                v11 = avaliar_aptidao(analise, cultura, "ATUAL", contexto, Trace(), dados=por_regra[_V11])
                v12 = avaliar_aptidao(analise, cultura, "ATUAL", contexto, Trace(), dados=por_regra[_V12])
                assert _assinatura(v11) == _assinatura(v12), (
                    f"{cultura}: V% {v_percent}, CTC {ctc}, Ca {ca}, Mg {mg}"
                )
                pontos += 1

    assert pontos == len(_V) * len(_CTC) * len(_CA_MG)
