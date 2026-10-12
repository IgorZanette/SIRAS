"""
Testes das invariantes de dados/culturas/graos/.

Testa:
- graos_adubacao_n.json: contagem de culturas e por modelo bate com o checksum
- graos_adubacao_pk.json: contagem de culturas e somas de manutenção batem com o checksum
"""

import pytest
from siras.conhecimento.carregador import Carregador


@pytest.fixture
def carregador():
    return Carregador()


@pytest.fixture
def dados_graos(carregador):
    return carregador.carregar_dados_graos()


class TestGraosAdubacaoN:
    """Testes de invariantes de graos_adubacao_n.json."""

    def test_quantidade_de_culturas_bate_com_checksum(self, dados_graos):
        culturas = dados_graos["adubacao_n"]["culturas"]
        checksum = dados_graos["adubacao_n"]["checksum"]
        assert len(culturas) == checksum["culturas"], \
            f"Esperado {checksum['culturas']} culturas, encontrado {len(culturas)}"

    def test_contagem_por_modelo_bate_com_checksum(self, dados_graos):
        culturas = dados_graos["adubacao_n"]["culturas"]
        checksum = dados_graos["adubacao_n"]["checksum"]

        contagem = {}
        for entrada in culturas.values():
            modelo = entrada["modelo"]
            contagem[modelo] = contagem.get(modelo, 0) + 1

        assert contagem == checksum["por_modelo"], \
            f"Esperado {checksum['por_modelo']}, obtido {contagem}"

    def test_todo_modelo_e_um_dos_tres_conhecidos(self, dados_graos):
        culturas = dados_graos["adubacao_n"]["culturas"]
        for cultura, entrada in culturas.items():
            assert entrada["modelo"] in ("nao_aplica", "mo", "mo_x_antecedente"), \
                f"cultura '{cultura}': modelo '{entrada['modelo']}' desconhecido"


class TestGraosAdubacaoPK:
    """Testes de invariantes de graos_adubacao_pk.json."""

    def test_quantidade_de_culturas_bate_com_checksum(self, dados_graos):
        culturas = dados_graos["adubacao_pk"]["manutencao_por_cultura"]["culturas"]
        checksum = dados_graos["adubacao_pk"]["checksum"]
        assert len(culturas) == checksum["culturas"], \
            f"Esperado {checksum['culturas']} culturas, encontrado {len(culturas)}"

    def test_soma_p2o5_manutencao_bate_com_checksum(self, dados_graos):
        culturas = dados_graos["adubacao_pk"]["manutencao_por_cultura"]["culturas"]
        checksum = dados_graos["adubacao_pk"]["checksum"]
        soma = sum(c["p2o5_manutencao"] for c in culturas.values())
        assert soma == checksum["soma_p2o5_manutencao"], \
            f"Esperado {checksum['soma_p2o5_manutencao']}, obtido {soma}"

    def test_soma_k2o_manutencao_bate_com_checksum(self, dados_graos):
        culturas = dados_graos["adubacao_pk"]["manutencao_por_cultura"]["culturas"]
        checksum = dados_graos["adubacao_pk"]["checksum"]
        soma = sum(c["k2o_manutencao"] for c in culturas.values())
        assert soma == checksum["soma_k2o_manutencao"], \
            f"Esperado {checksum['soma_k2o_manutencao']}, obtido {soma}"

    def test_mesmas_culturas_em_manutencao_e_exportacao(self, dados_graos):
        adubacao_pk = dados_graos["adubacao_pk"]
        culturas_manutencao = set(adubacao_pk["manutencao_por_cultura"]["culturas"].keys())
        culturas_exportacao = set(adubacao_pk["exportacao_nos_graos"]["culturas"].keys())
        so_em_manutencao = culturas_manutencao - culturas_exportacao
        so_em_exportacao = culturas_exportacao - culturas_manutencao
        assert not so_em_manutencao, \
            f"Culturas em manutencao_por_cultura sem par em exportacao_nos_graos: {so_em_manutencao}"
        assert not so_em_exportacao, \
            f"Culturas em exportacao_nos_graos sem par em manutencao_por_cultura: {so_em_exportacao}"
