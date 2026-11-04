"""
Correspondências entre culturas do sistema e nomes da Tabela 5.1 (pH de referência).

Dez culturas do escopo saíam com aptidão INDETERMINADA por nome, e não por falta de
dado (ADR 0005, D5.7): o sistema usa o agrupamento do Manual ("melancia_melao") ou a
espécie ("aveia_branca"), e a Tabela 5.1 lista as espécies separadas ou o nome genérico
("melancia", "melão", "aveia"). As correspondências ficam em aliases_culturas.json.

O que estes testes travam é a REGRA, e não um valor: o pH só é aceito quando todos os
nomes correspondentes concordam, e nada que já resolvia muda de resultado.
"""

import json
from pathlib import Path

import pytest

from siras.conhecimento.carregador import Carregador, ErroCarregamento, carregar_dados_comum
from siras.dominio.escopo import no_escopo_de_recomendacao
from siras.dominio.nomes import normalizar_nome_cultura
from siras.motor.aptidao import (
    _CulturaOuDadoIndeterminado,
    _correspondencias_na_tabela_5_1,
    _nomes_candidatos,
    _resolver_ph_referencia,
)

_ALIASES = Path(__file__).parent.parent.parent / "dados" / "comum" / "aliases_culturas.json"


@pytest.fixture(scope="module")
def dados():
    return carregar_dados_comum()


@pytest.fixture(scope="module")
def nomes_da_tabela_5_1(dados):
    return {
        normalizar_nome_cultura(cultura)
        for grupo in dados["ph_referencia"]["grupos"]
        for cultura in grupo["culturas"]
    }


def test_toda_correspondencia_aponta_para_cultura_e_nomes_que_existem(dados, nomes_da_tabela_5_1):
    """Uma correspondência para nome que a Tabela 5.1 não tem seria inerte sem avisar."""
    culturas = set(dados["mapa_culturas"]["culturas"])
    for item in dados["aliases_culturas"]["correspondencias_na_tabela_5_1"]:
        assert item["cultura"] in culturas, item["cultura"]
        for nome in item["nomes_na_tabela"]:
            assert normalizar_nome_cultura(nome) in nomes_da_tabela_5_1, (item["cultura"], nome)


def test_correspondencia_so_existe_para_quem_nao_resolve_sozinho(dados, nomes_da_tabela_5_1):
    """Precedência: se a cultura resolve pelo próprio nome, a correspondência nunca seria
    lida, e declará-la só criaria a impressão de que ela decide alguma coisa."""
    for item in dados["aliases_culturas"]["correspondencias_na_tabela_5_1"]:
        assert normalizar_nome_cultura(item["cultura"]) not in nomes_da_tabela_5_1


def test_nomes_que_concordam_resolvem(dados):
    ph = _resolver_ph_referencia(
        "melancia_melao", dados["ph_referencia"], ("melancia_melao",),
        _correspondencias_na_tabela_5_1("melancia_melao", dados),
    )
    esperado = _resolver_ph_referencia("melancia", dados["ph_referencia"])

    assert ph == esperado == _resolver_ph_referencia("melao", dados["ph_referencia"])


def test_nomes_que_divergem_ficam_indeterminados(dados):
    """Salsa e alface estão em grupos diferentes da Tabela 5.1. Escolher um seria decidir
    pelo Manual: a cultura fica INDETERMINADA, com o motivo."""
    nomes = _correspondencias_na_tabela_5_1("alface_almeirao_chicoria_rucula_salsa", dados)
    assert _resolver_ph_referencia("salsa", dados["ph_referencia"]) != \
        _resolver_ph_referencia("alface", dados["ph_referencia"])

    with pytest.raises(_CulturaOuDadoIndeterminado, match="diferentes"):
        _resolver_ph_referencia(
            "alface_almeirao_chicoria_rucula_salsa", dados["ph_referencia"],
            ("alface_almeirao_chicoria_rucula_salsa",), nomes,
        )


def test_o_nome_proprio_vence_a_correspondencia(dados):
    """Mesmo com uma correspondência para outro grupo de pH, quem resolve pelo próprio
    nome mantém o seu valor."""
    proprio = _resolver_ph_referencia("salsa", dados["ph_referencia"])
    outra = _resolver_ph_referencia("alface", dados["ph_referencia"])
    assert proprio != outra

    assert _resolver_ph_referencia(
        "salsa", dados["ph_referencia"], ("salsa",), ("alface",)
    ) == proprio


def test_sem_correspondencia_o_motivo_continua_o_de_antes(dados):
    with pytest.raises(_CulturaOuDadoIndeterminado, match="não encontrada em ph_referencia"):
        _resolver_ph_referencia("cultura_inexistente", dados["ph_referencia"])


def test_cultura_com_duas_correspondencias_e_recusada_no_carregamento():
    dados = json.loads(_ALIASES.read_text(encoding="utf-8"))
    dados["correspondencias_na_tabela_5_1"].append(
        dict(dados["correspondencias_na_tabela_5_1"][0])
    )

    with pytest.raises(ErroCarregamento, match="mais de uma correspondência"):
        Carregador().validar_aliases_culturas(dados)


def test_no_escopo_so_o_agrupamento_da_salsa_fica_indeterminado(dados):
    """Das 61 culturas, as dez que não resolviam pelo nome passam a ter pH de referência,
    exceto o agrupamento com espécies em grupos diferentes da Tabela 5.1."""
    indeterminadas = []
    for cultura in dados["mapa_culturas"]["culturas"]:
        if not no_escopo_de_recomendacao(cultura):
            continue
        try:
            _resolver_ph_referencia(
                cultura, dados["ph_referencia"], _nomes_candidatos(cultura, dados),
                _correspondencias_na_tabela_5_1(cultura, dados),
            )
        except _CulturaOuDadoIndeterminado:
            indeterminadas.append(cultura)

    assert indeterminadas == ["alface_almeirao_chicoria_rucula_salsa"]
