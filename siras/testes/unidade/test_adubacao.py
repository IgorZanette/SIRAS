"""
Testes de siras/motor/adubacao.py.

Caso oficial ADU-01 (testes/casos/casos_recomendacao.json): soja, argila 32%, P 6,0,
K 80, CTC 9,5, cultivo 1 -> classe_p=muito_baixo, classe_k=medio, n=0, p2o5=155, k2o=105.
"""

import pytest

from siras.conhecimento.carregador import carregar_dados_graos
from siras.motor.adubacao import ErroAdubacao, calcular_fosforo_potassio, calcular_nitrogenio


class TestNitrogenioNaoAplica:
    def test_soja_nao_recebe_n_fixacao_biologica(self):
        resultado = calcular_nitrogenio("soja", mo=3.0)
        assert resultado["n"] == 0
        assert resultado["motivo"] == "fixacao_biologica_de_nitrogenio"

    def test_amendoim_nao_recebe_n(self):
        resultado = calcular_nitrogenio("amendoim", mo=3.0)
        assert resultado["n"] == 0


class TestNitrogenioModeloMo:
    def test_arroz_de_sequeiro_mo_ate_2_5(self):
        resultado = calcular_nitrogenio("arroz_de_sequeiro", mo=2.0)
        assert resultado["n"] == 50
        assert resultado["faixa_mo"] == "mo_ate_2_5"

    def test_arroz_de_sequeiro_mo_2_6_a_5_0(self):
        resultado = calcular_nitrogenio("arroz_de_sequeiro", mo=3.5)
        assert resultado["n"] == 40

    def test_arroz_de_sequeiro_mo_acima_5_0(self):
        resultado = calcular_nitrogenio("arroz_de_sequeiro", mo=6.0)
        assert resultado["n"] == 10

    def test_limite_2_5_e_inclusivo_na_faixa_baixa(self):
        resultado = calcular_nitrogenio("arroz_de_sequeiro", mo=2.5)
        assert resultado["faixa_mo"] == "mo_ate_2_5"

    def test_limite_5_0_e_inclusivo_na_faixa_media(self):
        resultado = calcular_nitrogenio("arroz_de_sequeiro", mo=5.0)
        assert resultado["faixa_mo"] == "mo_2_6_a_5_0"


class TestNitrogenioModeloMoXAntecedente:
    def test_milho_apos_leguminosa_mo_baixa(self):
        resultado = calcular_nitrogenio("milho", mo=2.0, antecedente="leguminosa")
        assert resultado["n"] == 70

    def test_milho_apos_graminea_mo_baixa(self):
        resultado = calcular_nitrogenio("milho", mo=2.0, antecedente="graminea")
        assert resultado["n"] == 90

    def test_milho_sem_antecedente_levanta_erro(self):
        with pytest.raises(ErroAdubacao, match="antecedente"):
            calcular_nitrogenio("milho", mo=2.0, antecedente=None)

    def test_milho_antecedente_invalido_levanta_erro(self):
        with pytest.raises(ErroAdubacao, match="antecedente"):
            calcular_nitrogenio("milho", mo=2.0, antecedente="pousio_puro")


class TestNitrogenioCulturaDesconhecida:
    def test_cultura_ausente_levanta_erro_adubacao(self):
        with pytest.raises(ErroAdubacao, match="feijao_magico"):
            calcular_nitrogenio("feijao_magico", mo=3.0)


class TestFosforoPotassio:
    """Caso oficial ADU-01."""

    def test_adu_01_soja_cultivo_1(self):
        resultado = calcular_fosforo_potassio(
            cultura_id="soja",
            argila=32,
            p_solo=6.0,
            ctc_ph7=9.5,
            k_solo=80,
            cultivo=1,
            expectativa_rendimento=3.0,
        )
        assert resultado["classe_p"] == "muito_baixo"
        assert resultado["classe_k"] == "medio"
        assert resultado["p2o5"] == 155
        assert resultado["k2o"] == 105

    def test_p_no_limite_superior_e_inclusivo_na_faixa_menor(self):
        # Regressão explícita: P=6.0 é o limite superior de muito_baixo (classe_argila 3),
        # e a memória de cálculo do ADU-01 registra que esse limite é inclusivo.
        resultado = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=6.0, ctc_ph7=9.5, k_solo=80, cultivo=1,
        )
        assert resultado["classe_p"] == "muito_baixo"

    def test_p_logo_acima_do_limite_e_classe_seguinte(self):
        resultado = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=6.1, ctc_ph7=9.5, k_solo=80, cultivo=1,
        )
        assert resultado["classe_p"] == "baixo"

    def test_cultivo_2_usa_um_terco_da_correcao_em_classe_muito_baixa(self):
        resultado_1 = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=6.0, ctc_ph7=9.5, k_solo=80, cultivo=1,
        )
        resultado_2 = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=6.0, ctc_ph7=9.5, k_solo=80, cultivo=2,
        )
        # cultivo_1: 2/3*160 -> 110 + manutencao 45 = 155 (classe muito_baixo)
        # cultivo_2: 1/3*160 -> 50 + manutencao 45 = 95
        assert resultado_1["p2o5"] == 155
        assert resultado_2["p2o5"] == 95

    def test_cultivo_invalido_levanta_erro_adubacao(self):
        with pytest.raises(ErroAdubacao, match="cultivo"):
            calcular_fosforo_potassio(
                cultura_id="soja", argila=32, p_solo=6.0, ctc_ph7=9.5, k_solo=80, cultivo=3,
            )

    def test_rendimento_acima_da_referencia_soma_adicional_na_manutencao(self):
        # soja: rendimento_referencia_t_ha=3; K classe medio soma so a manutencao (cultivo 1
        # ja usa correcao + manutencao); expectativa 4.0 (1 t/ha acima) deveria somar
        # k2o_adicional_por_t=25 a mais na manutencao de K.
        sem_excedente = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=80, ctc_ph7=9.5, k_solo=80, cultivo=1,
            expectativa_rendimento=3.0,
        )
        com_excedente = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=80, ctc_ph7=9.5, k_solo=80, cultivo=1,
            expectativa_rendimento=4.0,
        )
        assert com_excedente["k2o"] == sem_excedente["k2o"] + 25

    def test_cultura_sem_manutencao_levanta_erro_adubacao(self):
        with pytest.raises(ErroAdubacao, match="feijao_magico"):
            calcular_fosforo_potassio(
                cultura_id="feijao_magico", argila=32, p_solo=6.0, ctc_ph7=9.5, k_solo=80, cultivo=1,
            )


class TestClasseMuitoAlto:
    """Dois achados sobre a mesma linha da tabela.

    Revisão de 2026-08-23: cultivo 2 na classe muito_alto retornava um escalar, mas a
    tabela (graos_adubacao_pk.json, algoritmo_dose.regras) só dá um TETO, não um valor.
    Sem o qualificador, o SIRAS recomendaria uma dose fixa onde o Manual autoriza não
    aplicar nada, justamente o oposto do que a classe Muito alto significa.

    Caso ADU-27, 2026-10-10: o teto estava na manutenção, e não na reposição. Ver
    docs/decisoes/0010.
    """

    def test_cultivo_1_muito_alto_e_zero_escalar(self):
        # P=50,0 (>36,0) e K=300 (>180), argila 32/CTC 9,5: ambos Muito alto (ADU-05).
        resultado = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=50.0, ctc_ph7=9.5, k_solo=300, cultivo=1,
        )
        assert resultado["classe_p"] == "muito_alto"
        assert resultado["classe_k"] == "muito_alto"
        assert resultado["p2o5"] == 0.0
        assert resultado["k2o"] == 0.0

    def test_cultivo_2_muito_alto_e_teto_nao_escalar(self):
        resultado = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=50.0, ctc_ph7=9.5, k_solo=300, cultivo=2,
            expectativa_rendimento=3.0,
        )
        assert isinstance(resultado["p2o5"], dict)
        assert resultado["p2o5"]["qualificador"] == "ate"
        assert resultado["k2o"]["qualificador"] == "ate"

    def test_cultivo_2_muito_alto_usa_reposicao_e_nao_manutencao(self):
        """Regressão do ADU-27: o teto é a exportação nos grãos x rendimento."""
        pk = carregar_dados_graos()["adubacao_pk"]
        exportacao = pk["exportacao_nos_graos"]["culturas"]["soja"]
        manutencao = pk["manutencao_por_cultura"]["culturas"]["soja"]
        rendimento = manutencao["rendimento_referencia_t_ha"]

        resultado = calcular_fosforo_potassio(
            cultura_id="soja", argila=32, p_solo=50.0, ctc_ph7=9.5, k_solo=300, cultivo=2,
            expectativa_rendimento=rendimento,
        )
        assert resultado["p2o5"]["valor"] == exportacao["p2o5"] * rendimento
        assert resultado["k2o"]["valor"] == exportacao["k2o"] * rendimento
        # Discriminante: se voltar a usar a manutenção, o teste tem de falhar.
        assert resultado["p2o5"]["valor"] != manutencao["p2o5_manutencao"]
        assert resultado["k2o"]["valor"] != manutencao["k2o_manutencao"]

    def test_reposicao_acompanha_a_expectativa_de_rendimento(self):
        exportacao = carregar_dados_graos()["adubacao_pk"]["exportacao_nos_graos"]["culturas"]["soja"]
        comum = dict(cultura_id="soja", argila=32, p_solo=50.0, ctc_ph7=9.5, k_solo=300, cultivo=2)
        baixo = calcular_fosforo_potassio(**comum, expectativa_rendimento=3.0)
        alto = calcular_fosforo_potassio(**comum, expectativa_rendimento=4.0)
        assert alto["p2o5"]["valor"] - baixo["p2o5"]["valor"] == exportacao["p2o5"]
        assert alto["k2o"]["valor"] - baixo["k2o"]["valor"] == exportacao["k2o"]


class TestAdicionalDeNitrogenioPorRendimento:
    """Achado do caso ADU-25 (2026-10-10): `adicional_kg_n_por_t` estava transcrito em 16
    culturas de grãos e nenhuma linha de código o lia. A dose de N não reagia à
    expectativa de rendimento, enquanto P e K reagiam. Ver docs/decisoes/0010.

    Os testes comparam a dose COM e SEM excedente, e leem o adicional do próprio
    `dados/`: assim medem a aritmética sem fixar nenhum número do Manual no teste.
    """

    def _entrada_do_milho(self):
        return carregar_dados_graos()["adubacao_n"]["culturas"]["milho"]

    def test_rendimento_acima_da_referencia_soma_o_adicional(self):
        entrada = self._entrada_do_milho()
        referencia = entrada["rendimento_referencia_t_ha"]
        por_tonelada = entrada["adicional_kg_n_por_t"]

        na_referencia = calcular_nitrogenio(
            "milho", mo=3.5, antecedente="graminea", expectativa_rendimento=referencia
        )
        acima = calcular_nitrogenio(
            "milho", mo=3.5, antecedente="graminea", expectativa_rendimento=referencia + 2
        )
        assert acima["n"] - na_referencia["n"] == 2 * por_tonelada
        assert acima["adicional_kg_n_ha"] == 2 * por_tonelada
        assert na_referencia["adicional_kg_n_ha"] == 0.0

    def test_rendimento_abaixo_da_referencia_nao_desconta(self):
        entrada = self._entrada_do_milho()
        referencia = entrada["rendimento_referencia_t_ha"]
        abaixo = calcular_nitrogenio(
            "milho", mo=3.5, antecedente="graminea", expectativa_rendimento=referencia - 2
        )
        sem_expectativa = calcular_nitrogenio("milho", mo=3.5, antecedente="graminea")
        assert abaixo["n"] == sem_expectativa["n"]
        assert abaixo["adicional_kg_n_ha"] == 0.0

    def test_faixa_de_mo_acima_de_5_0_e_teto_e_nao_soma_adicional(self):
        """Decisão do autor em 2026-10-10: nessa faixa o Manual publica a dose como teto
        (`acima_de_5_0_e_maximo`), e somar o adicional passaria do que o teto admite."""
        entrada = self._entrada_do_milho()
        assert entrada["acima_de_5_0_e_maximo"] is True

        referencia = entrada["rendimento_referencia_t_ha"]
        na_referencia = calcular_nitrogenio(
            "milho", mo=6.0, antecedente="graminea", expectativa_rendimento=referencia
        )
        acima = calcular_nitrogenio(
            "milho", mo=6.0, antecedente="graminea", expectativa_rendimento=referencia + 6
        )
        assert acima["n"] == na_referencia["n"]
        assert acima["teto"] is True
        assert acima["adicional_kg_n_ha"] == 0.0

    def test_leguminosa_nao_recebe_adicional(self):
        # As 5 culturas de modelo 'nao_aplica' são leguminosas e não declaram adicional.
        resultado = calcular_nitrogenio("soja", mo=3.0, expectativa_rendimento=10.0)
        assert resultado["n"] == 0
        assert resultado["adicional_kg_n_ha"] == 0
