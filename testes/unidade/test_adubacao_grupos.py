"""
Testes de siras/motor/adubacao.py — grupos hortaliças, tubérculos, outras comerciais
(cana/tabaco), frutíferas e erva-mate (calcular_adubacao_*).

Casos oficiais ADU-08 a ADU-14 (rascunho de oráculo compartilhado pelo autor em
2026-08-23, calculados à mão a partir das Tabelas 6.2-6.10, 6.3, 6.4, 6.5.1, 6.9.2 e
6.6.5): usados aqui como alvo de implementação. O ADU-10 (tabaco) tem um erro plantado
de propósito no rascunho do autor (classe_k e k2o errados) para checar que o motor
recalcula em vez de repetir o valor errado — o teste correspondente afirma o valor
CORRETO (classe alto, 120), não o do rascunho.
"""

import pytest

from siras.motor.adubacao import (
    ErroAdubacao,
    calcular_adubacao_erva_mate,
    calcular_adubacao_frutiferas,
    calcular_adubacao_hortalicas,
    calcular_adubacao_outras,
    calcular_adubacao_tuberculos,
)


class TestHortalicas:
    def test_adu_14_ervilha_leguminosa_sem_n(self):
        resultado = calcular_adubacao_hortalicas(
            "ervilha", mo=2.0, argila=32, p_solo=4.0, k_solo=25, ctc_ph7=9.5,
        )
        assert resultado["classe_p"] == "muito_baixo"
        assert resultado["classe_k"] == "muito_baixo"
        assert resultado["n"] == 0.0
        assert resultado["motivo_n"] == "fixacao_biologica_de_nitrogenio"
        assert resultado["p2o5"] == 240
        assert resultado["k2o"] == 210

    def test_adu_13_cebola_ajuste_expectativa_rendimento(self):
        resultado = calcular_adubacao_hortalicas(
            "cebola", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            expectativa_rendimento=45,
        )
        assert resultado["classe_p"] == "medio"
        assert resultado["classe_k"] == "medio"
        assert resultado["n"] == 160
        assert resultado["p2o5"] == 205
        assert resultado["k2o"] == 165

    def test_cebola_sem_expectativa_nao_soma_incremento(self):
        resultado = calcular_adubacao_hortalicas(
            "cebola", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
        )
        assert resultado["n"] == 100
        assert resultado["p2o5"] == 160
        assert resultado["k2o"] == 120

    def test_aspargo_exige_fase(self):
        with pytest.raises(ErroAdubacao, match="fase"):
            calcular_adubacao_hortalicas(
                "aspargo", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            )

    def test_aspargo_com_fase_calcula(self):
        resultado = calcular_adubacao_hortalicas(
            "aspargo", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5, fase="formacao",
        )
        assert resultado["n"] == 100
        assert resultado["p2o5"] == 0
        assert resultado["k2o"] == 150

    def test_cultura_desconhecida_levanta_erro_adubacao(self):
        with pytest.raises(ErroAdubacao, match="alface_marciana"):
            calcular_adubacao_hortalicas(
                "alface_marciana", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            )


class TestTuberculos:
    def test_adu_08_batata(self):
        resultado = calcular_adubacao_tuberculos(
            "batata", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            expectativa_rendimento=30,
        )
        assert resultado["classe_p"] == "baixo"
        assert resultado["classe_k"] == "baixo"
        assert resultado["n"] == 100
        assert resultado["p2o5"] == 260
        assert resultado["k2o"] == 190

    def test_adu_09_batata_doce_grupos_p_e_k_diferentes(self):
        # Armadilha central do caso: batata-doce e grupo_p=3 e grupo_k=1 (diferentes) —
        # se o motor derivasse um grupo do outro, este teste haveria de falhar.
        resultado = calcular_adubacao_tuberculos(
            "batata_doce", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            expectativa_rendimento=20,
        )
        assert resultado["classe_p"] == "alto"
        assert resultado["classe_k"] == "baixo"
        assert resultado["n"] == 40
        assert resultado["p2o5"] == 60
        assert resultado["k2o"] == 170

    def test_expectativa_no_limiar_nao_soma_incremento(self):
        # Expectativa 30 == limiar (nao > limiar): sem acrescimo (mesmo caso do ADU-08).
        com_30 = calcular_adubacao_tuberculos(
            "batata", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            expectativa_rendimento=30,
        )
        sem_expectativa = calcular_adubacao_tuberculos(
            "batata", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
        )
        assert com_30 == sem_expectativa


class TestOutrasCana:
    def test_cana_planta_exige_ciclo(self):
        with pytest.raises(ErroAdubacao, match="ciclo"):
            calcular_adubacao_outras(
                "cana_de_acucar", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            )

    def test_cana_planta_exige_produtividade(self):
        with pytest.raises(ErroAdubacao, match="produtividade_t_ha"):
            calcular_adubacao_outras(
                "cana_de_acucar", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
                ciclo="cana_planta",
            )

    def test_cana_planta_classe_alta_produtividade_media(self):
        # p=15 (grupo_p=3, argila classe 3): Tab.6.5 alto (9,0-18,0). k=80 (grupo_k=3,
        # CTC faixa b): Tab.6.10 alto (60-120). Produtividade 100 t/ha -> faixa
        # 'de_90_a_120'. Cana-planta, N por classe de MO (sem produtividade).
        resultado = calcular_adubacao_outras(
            "cana_de_acucar", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            ciclo="cana_planta", produtividade_t_ha=100,
        )
        assert resultado["classe_p"] == "alto"
        assert resultado["classe_k"] == "alto"
        assert resultado["n"] == 50
        assert resultado["p2o5"] == 40
        assert resultado["k2o"] == 40

    def test_cana_soca_usa_produtividade_tambem_no_n(self):
        # cana_soca.n e "por_classe_mo_e_produtividade" (diferente de cana_planta.n).
        # Produtividade 100 -> faixa 'maior_90'; mo=3.0 -> 'de_2_6_a_5_0' -> 90.
        resultado = calcular_adubacao_outras(
            "cana_de_acucar", mo=3.0, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            ciclo="cana_soca", produtividade_t_ha=100,
        )
        assert resultado["n"] == 90


class TestOutrasTabaco:
    def test_tabaco_exige_tipo(self):
        with pytest.raises(ErroAdubacao, match="tipo"):
            calcular_adubacao_outras(
                "tabaco", mo=2.5, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            )

    def test_adu_10_tabaco_virginia_recalcula_classe_k_correta(self):
        # O rascunho do autor (oraculo_adubacao.json, ADU-10) planta um erro proposital
        # em classe_k/k2o (diz "medio"/140) para checar que o motor nao repete o valor
        # errado. O correto: K=80 em CTC faixa 'b' (7,5-15,0), grupo_k=3 (Tab.6.10) cai
        # em ALTO (61-120), nao em medio (41-60) — dose 120 (virginia), nao 140.
        resultado = calcular_adubacao_outras(
            "tabaco", mo=2.5, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5, tipo="virginia",
        )
        assert resultado["classe_p"] == "alto"
        assert resultado["classe_k"] == "alto"
        assert resultado["n"] == {"min": 120, "max": 140}
        assert resultado["p2o5"] == 40
        assert resultado["k2o"] == 120

    def test_tabaco_burley_usa_coluna_propria_de_k(self):
        resultado = calcular_adubacao_outras(
            "tabaco", mo=2.5, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5, tipo="burley",
        )
        assert resultado["p2o5"] == 40  # P e comum aos dois tipos
        assert resultado["k2o"] == 130  # K, classe alto, burley (virginia seria 120)


class TestFrutiferasPrePlantioECrescimento:
    def test_pre_plantio_usa_tabela_6_5_1_comum(self):
        resultado = calcular_adubacao_frutiferas(
            "macieira", fase="pre_plantio", argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
        )
        assert resultado["classe_p"] == "medio"
        assert resultado["classe_k"] == "medio"
        assert resultado["p2o5"] == 130
        assert resultado["k2o"] == 60

    def test_crescimento_por_classe_mo_e_ano_exige_ano(self):
        with pytest.raises(ErroAdubacao, match="ano"):
            calcular_adubacao_frutiferas("macieira", fase="crescimento", mo=3.0)

    def test_crescimento_calcula_por_ano(self):
        resultado = calcular_adubacao_frutiferas("macieira", fase="crescimento", mo=3.0, ano=2)
        assert resultado["n"] == 40
        assert resultado["p2o5"] == 0.0
        assert resultado["k2o"] == 0.0


class TestFrutiferasManutencao:
    def test_adu_11_abacateiro_taxa_por_tonelada(self):
        resultado = calcular_adubacao_frutiferas(
            "abacateiro", fase="manutencao", produtividade_estimada=12,
        )
        assert resultado["n"] == {"min": 36.0, "max": 48.0}
        assert resultado["p2o5"] == 12.0
        assert resultado["k2o"] == {"min": 48.0, "max": 60.0}

    def test_manutencao_exige_produtividade_estimada(self):
        with pytest.raises(ErroAdubacao, match="produtividade_estimada"):
            calcular_adubacao_frutiferas("abacateiro", fase="manutencao")

    def test_teor_foliar_sem_correspondencia_levanta_not_implemented(self):
        # ameixeira/macieira/pessegueiro-nectarineira: dados/ ja marca
        # requer_analise_foliar=true, implementado_no_siras=false.
        with pytest.raises(NotImplementedError, match="foliar"):
            calcular_adubacao_frutiferas("ameixeira", fase="manutencao")

    def test_pessegueiro_e_ameixeira_tambem_levantam_not_implemented(self):
        # As tres frutiferas de teor foliar sem correspondencia (ameixeira, macieira,
        # pessegueiro/nectarineira) ficam fora de escopo SO na manutencao — pre_plantio
        # e crescimento continuam plenamente computaveis (ver testes de
        # TestFrutiferasPrePlantioECrescimento, que ja exercitam a macieira).
        with pytest.raises(NotImplementedError, match="foliar"):
            calcular_adubacao_frutiferas("pessegueiro_nectarineira", fase="manutencao")


class TestErvaMate:
    def test_adu_12_producao_formula_por_manejo(self):
        resultado = calcular_adubacao_erva_mate(
            "desde_o_plantio", fase="producao", mo=3.0,
            manejo_galho_grosso="manejo_2_retirado", massa_verde_t_ha=20,
        )
        assert resultado["n"] == 260
        assert resultado["p2o5"] == 24.0
        assert resultado["k2o"] == 170.0

    def test_producao_exige_manejo_e_massa_verde(self):
        with pytest.raises(ErroAdubacao, match="manejo_galho_grosso"):
            calcular_adubacao_erva_mate("desde_o_plantio", fase="producao", mo=3.0)

    def test_formacao_da_copa_por_classe_mo_e_teor(self):
        resultado = calcular_adubacao_erva_mate(
            "desde_o_plantio", fase="formacao_da_copa", mo=3.0,
            argila=55, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
        )
        assert resultado["n"] == 60
        assert resultado["k2o"] == 30

    def test_plantio_e_crescimento_exige_momento(self):
        with pytest.raises(ErroAdubacao, match="momento"):
            calcular_adubacao_erva_mate(
                "desde_o_plantio", fase="plantio_e_crescimento", mo=3.0,
                argila=55, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
            )

    def test_recuperacao_formula_base_mais_coeficiente(self):
        # p_solo/k_solo baixos o bastante para cair nas classes atendidas pela recuperacao
        # (muito_baixo/baixo/medio) — a recuperacao nao cobre alto/muito_alto.
        resultado = calcular_adubacao_erva_mate(
            "recuperacao", mo=3.0, argila=55, p_solo=2.0, k_solo=10.0, ctc_ph7=9.5,
            manejo_galho_grosso="manejo_1_retido", massa_verde_t_ha=10,
        )
        assert resultado["classe_p"] == "muito_baixo"
        assert resultado["classe_k"] == "muito_baixo"
        assert resultado["n"] == 160
        assert resultado["p2o5"] == 190.0
        assert resultado["k2o"] == 245.0

    def test_recuperacao_fora_das_classes_atendidas_levanta_erro(self):
        with pytest.raises(ErroAdubacao, match="classes_atendidas|não está no programa"):
            calcular_adubacao_erva_mate(
                "recuperacao", mo=3.0, argila=55, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
                manejo_galho_grosso="manejo_1_retido", massa_verde_t_ha=10,
            )


class TestFrutiferasBespoke:
    """ADU-15 a ADU-19 (rascunho de oráculo compartilhado pelo autor em 2026-08-23):
    um caso por formato de manutenção próprio de frutífera. Cada um foi desenhado para
    denunciar um erro específico de leitura — ver comentário em cada teste."""

    def test_adu_15_amoreira_preta_colunas_nao_ordinais(self):
        # Ano 4 -> coluna 'ano_3_mais_...' (nao e indice ordinal); produtividade 12>10
        # -> subcoluna 'acima_10'. NOTA: a entrada original do autor tem argila=45%
        # (classe_argila 2), que dá classe_p=ALTO (p2o5=70) — mas o "esperado"
        # compartilhado (84) é o valor da classe MEDIO, que só bate com argila=32%
        # (classe_argila 3). Descasamento proposital no rascunho, sinalizado pelo
        # próprio autor ("ponto_de_atencao"); uso argila=32 aqui para bater com o
        # "esperado" já compartilhado, mas isso precisa de confirmação do autor antes
        # de virar referencia oficial em testes/casos/casos_recomendacao.json.
        resultado = calcular_adubacao_frutiferas(
            "amoreira_preta", fase="manutencao", ano=4, produtividade_estimada=12,
            mo=3.5, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
        )
        assert resultado["n"] == 117
        assert resultado["p2o5"] == 84
        assert resultado["k2o"] == 171

    def test_adu_15_amoreira_preta_primeiro_ano_nao_aplica(self):
        resultado = calcular_adubacao_frutiferas(
            "amoreira_preta", fase="manutencao", ano=1, produtividade_estimada=12,
            mo=3.5, argila=32, p_solo=15.0, k_solo=80, ctc_ph7=9.5,
        )
        assert resultado["n"] == 0.0

    def test_adu_16_mirtileiro_crescimento_e_manutencao_unificados(self):
        resultado = calcular_adubacao_frutiferas(
            "mirtileiro", fase="manutencao", produtividade_estimada=2.0,
            mo=3.0, argila=32, p_solo=25.0, k_solo=150, ctc_ph7=9.5,
        )
        assert resultado["n"] == 30
        assert resultado["p2o5"] == 10
        assert resultado["k2o"] == 15

    def test_mirtileiro_crescimento_direto_exige_manutencao(self):
        with pytest.raises(ErroAdubacao, match="manutencao"):
            calcular_adubacao_frutiferas("mirtileiro", fase="crescimento", mo=3.0)

    def test_adu_17_morangueiro_ignora_mo_de_proposito(self):
        # MO=6,0% (bem alto) na entrada e proposital: o Manual desconsidera a MO do
        # morangueiro (substrato organico contribui pouco em N, p.214). Se o motor
        # aplicasse a faixa de MO por habito, o N sairia diferente de 180.
        resultado = calcular_adubacao_frutiferas(
            "morangueiro", fase="manutencao", produtividade_estimada=25,
            mo=6.0, argila=32, p_solo=25.0, k_solo=150, ctc_ph7=9.5,
        )
        assert resultado["n"] == 180
        assert resultado["p2o5"] == 60
        assert resultado["k2o"] == 180

    def test_adu_18_nogueira_peca_taxa_por_tonelada_e_produtividade_fracionaria(self):
        resultado = calcular_adubacao_frutiferas(
            "nogueira_peca", fase="manutencao", produtividade_estimada=2.0,
            mo=3.0, argila=32, p_solo=25.0, k_solo=150, ctc_ph7=9.5,
        )
        assert resultado["n"] == 200
        assert resultado["p2o5"] == 9.2
        assert resultado["k2o"] == 9.6

    def test_adu_18_nogueira_peca_ano_de_alternancia_reduz_n_pela_metade(self):
        resultado = calcular_adubacao_frutiferas(
            "nogueira_peca", fase="manutencao", produtividade_estimada=2.0,
            mo=3.0, argila=32, p_solo=25.0, k_solo=150, ctc_ph7=9.5,
            ano_de_alternancia=True,
        )
        assert resultado["n"] == 100
        assert resultado["p2o5"] == 9.2  # PK nao muda com a alternancia
        assert resultado["k2o"] == 9.6

    def test_adu_19_videira_n_e_p_vem_de_classes_de_tecido_diferentes(self):
        # O caso discriminante: do MESMO laudo, N (via MO) e P (via classe de P no
        # solo) chegam a classes de tecido DIFERENTES. Se o motor reaproveitasse a
        # classe de N para o P (ou vice-versa), o p2o5 sairia 40 em vez de 60.
        resultado = calcular_adubacao_frutiferas(
            "videira", fase="manutencao", tipo_uva="vinho", produtividade_estimada=18,
            mo=3.5, argila=45, p_solo=4.0, k_solo=150, ctc_ph7=9.5,
        )
        assert resultado["classe_tecido_n"] == "normal"
        assert resultado["classe_tecido_p"] == "insuficiente"
        assert resultado["n"] == 20
        assert resultado["p2o5"] == 60
        assert resultado["k2o"] is None
        assert "análise de tecido" in resultado["k2o_pendente"]

    def test_videira_analise_de_tecido_sobrepoe_correspondencia_do_solo(self):
        resultado = calcular_adubacao_frutiferas(
            "videira", fase="manutencao", tipo_uva="vinho", produtividade_estimada=18,
            analise_de_tecido={"n": "excessivo", "p": "excessivo"},
        )
        assert resultado["n"] == 0
        assert resultado["p2o5"] == 0
        assert "classe_p" not in resultado  # nao precisou classificar o solo

    def test_videira_exige_tipo_uva(self):
        with pytest.raises(ErroAdubacao, match="tipo_uva"):
            calcular_adubacao_frutiferas("videira", fase="manutencao", produtividade_estimada=18, mo=3.0)
