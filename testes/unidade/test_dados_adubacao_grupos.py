"""
Testes das invariantes dos arquivos de adubação por grupo de cultura (S3/S4):
hortaliças, tubérculos, outras comerciais (cana/tabaco), frutíferas e erva-mate.

Cada arquivo já é validado na carga (schema + validar_adubacao_por_grupo: classes de MO
contíguas, séries de P/K com as 5 classes de teor, doses em formato válido e não-crescentes
conforme o teor sobe — docs/decisoes/0004, D4.1/D4.4). Este arquivo cobre contagens
esperadas e amarrações pontuais entre arquivos.
"""

import pytest

from siras.conhecimento.carregador import (
    Carregador,
    ErroCarregamento,
    carregar_dados_comum,
)


@pytest.fixture
def carregador():
    return Carregador()


class TestHortalicas:
    def test_carrega_as_18_culturas(self, carregador):
        dados = carregador.carregar_dados_hortalicas()
        assert len(dados["adubacao"]["culturas"]) == 18

    def test_alho_tem_micronutrientes_zn_e_b(self, carregador):
        dados = carregador.carregar_dados_hortalicas()
        alho = dados["adubacao"]["culturas"]["alho"]
        assert "zn" in alho["micronutrientes"]
        assert "b" in alho["micronutrientes"]


class TestTuberculos:
    def test_carrega_as_2_culturas(self, carregador):
        dados = carregador.carregar_dados_tuberculos()
        assert len(dados["adubacao"]["culturas"]) == 2

    def test_mandioca_esta_fora_de_escopo(self, carregador):
        dados = carregador.carregar_dados_tuberculos()
        assert any("mandioca" in item for item in dados["adubacao"]["fora_de_escopo"])


class TestOutrasComerciais:
    def test_carrega_cana_e_tabaco(self, carregador):
        dados = carregador.carregar_dados_outras()
        culturas = dados["adubacao"]["culturas"]
        assert set(culturas.keys()) == {"cana_de_acucar", "tabaco"}

    def test_tabaco_usa_classes_mo_proprias(self, carregador):
        dados = carregador.carregar_dados_outras()
        tabaco = dados["adubacao"]["culturas"]["tabaco"]
        assert tabaco["n"]["classes_mo"] == "tabaco"
        assert len(dados["adubacao"]["classes_mo"]["tabaco"]) == 6

    def test_cana_declara_variavel_adicional_ciclo(self, carregador):
        dados = carregador.carregar_dados_outras()
        cana = dados["adubacao"]["culturas"]["cana_de_acucar"]
        assert cana["variavel_adicional"]["campo"] == "ciclo"
        assert set(cana["variavel_adicional"]["valores"]) == {"cana_planta", "cana_soca"}


class TestFrutiferas:
    def test_carrega_as_17_culturas(self, carregador):
        dados = carregador.carregar_dados_frutiferas()
        assert len(dados["adubacao"]["culturas"]) == 17

    def test_palmeira_jucara_esta_fora_de_escopo(self, carregador):
        dados = carregador.carregar_dados_frutiferas()
        assert any("jucara" in item for item in dados["adubacao"]["fora_de_escopo"])

    @pytest.mark.parametrize("cultura_id", ["ameixeira", "macieira", "pessegueiro_nectarineira"])
    def test_tres_especies_exigem_analise_foliar_e_nao_estao_implementadas(self, carregador, cultura_id):
        dados = carregador.carregar_dados_frutiferas()
        manutencao = dados["adubacao"]["culturas"][cultura_id]["manutencao"]
        assert manutencao["requer_analise_foliar"] is True
        assert manutencao["implementado_no_siras"] is False

    def test_videira_tem_alerta_pendente_para_k(self, carregador):
        dados = carregador.carregar_dados_frutiferas()
        videira = dados["adubacao"]["culturas"]["videira"]
        alerta_k = videira["manutencao"]["correspondencia_solo_tecido"]["k"]["alerta"]
        assert "NAO declara correspondencia" in alerta_k


class TestErvaMate:
    def test_carrega_uma_cultura(self, carregador):
        dados = carregador.carregar_dados_erva_mate()
        assert list(dados["adubacao"]["culturas"].keys()) == ["erva_mate"]

    def test_criterio_de_calagem_existe_em_criterios_calagem(self, carregador):
        dados_erva_mate = carregador.carregar_dados_erva_mate()
        criterio_id = dados_erva_mate["adubacao"]["culturas"]["erva_mate"]["calagem"]["criterio"]

        dados_comuns = carregar_dados_comum()
        ids_conhecidos = {c["id"] for c in dados_comuns["criterios_calagem"]["criterios"]}
        assert criterio_id in ids_conhecidos

    def test_cultura_incluida_bate_com_mapa_culturas(self, carregador):
        dados_erva_mate = carregador.carregar_dados_erva_mate()
        incluidas = dados_erva_mate["adubacao"]["culturas"]["erva_mate"]["culturas_incluidas"]

        dados_comuns = carregar_dados_comum()
        assert set(incluidas) <= set(dados_comuns["mapa_culturas"]["culturas"].keys())


class TestInvarianteMonotonicidadeRegride:
    """Regressão: a invariante I3 (monotonicidade de P/K por classe de teor) precisa
    realmente pegar um valor fora de ordem, não só passar silenciosamente."""

    def test_dose_fora_de_ordem_levanta_erro_carregamento(self, carregador):
        dados = carregador.carregar_dados_hortalicas()
        adubacao = dados["adubacao"]
        # Corrompe deliberadamente: baixo > muito_baixo (deveria ser não-crescente)
        adubacao["culturas"]["alho"]["pk"]["p"]["baixo"] = {"valor": 9999}

        with pytest.raises(ErroCarregamento, match="dose sobe"):
            carregador.validar_adubacao_por_grupo(adubacao, "hortalicas_adubacao.json")

    def test_classe_de_teor_ausente_levanta_erro_carregamento(self, carregador):
        dados = carregador.carregar_dados_tuberculos()
        adubacao = dados["adubacao"]
        del adubacao["culturas"]["batata"]["pk"]["k"]["muito_alto"]

        with pytest.raises(ErroCarregamento, match="classes de teor ausentes"):
            carregador.validar_adubacao_por_grupo(adubacao, "tuberculos_adubacao.json")

    def test_qualificador_desconhecido_levanta_erro_carregamento(self, carregador):
        dados = carregador.carregar_dados_tuberculos()
        adubacao = dados["adubacao"]
        adubacao["culturas"]["batata"]["pk"]["p"]["muito_alto"]["qualificador"] = "pelo_menos"

        with pytest.raises(ErroCarregamento, match="qualificador desconhecido"):
            carregador.validar_adubacao_por_grupo(adubacao, "tuberculos_adubacao.json")
