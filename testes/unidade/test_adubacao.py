"""
Testes de siras/motor/adubacao.py.

Caso oficial ADU-01 (testes/casos/casos_recomendacao.json): soja, argila 32%, P 6,0,
K 80, CTC 9,5, cultivo 1 -> classe_p=muito_baixo, classe_k=medio, n=0, p2o5=155, k2o=105.
"""

import pytest

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
    """Achado de revisão (2026-08-23): cultivo 2 na classe muito_alto retornava a
    manutenção como escalar, mas a tabela (graos_adubacao_pk.json, algoritmo_dose.regras)
    so da um teto — "<= manutencao (reposicao, a criterio do tecnico)" — nao um valor.
    Sem o qualificador, o SIRAS recomendaria uma dose fixa onde o Manual autoriza nao
    aplicar nada, justamente o oposto do que a classe Muito alto significa."""

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
        )
        # manutencao da soja: p2o5=45, k2o=75 (graos_adubacao_pk.json).
        assert resultado["p2o5"] == {"valor": 45, "qualificador": "ate"}
        assert resultado["k2o"] == {"valor": 75, "qualificador": "ate"}
