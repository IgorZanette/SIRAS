"""
Testes de siras/motor/calagem.py.

Caso oficial G-SOJA-01 (testes/casos/casos_recomendacao.json, memória de cálculo em
docs/COMO_CALCULAR_ORACULO.md), confirmado pelo autor: soja, convencional, pH 5,1,
SMP 5,4, PRNT 100 -> nc_t_ha = 6,8.
"""

import pytest

from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.calagem import (
    ErroCalagem,
    calcular_calagem,
    calcular_calagem_por_cultura,
    resolver_criterio_id,
)
from siras.motor.trace import Trace


def _analise(**sobrescreve):
    campos = dict(
        ph_agua=5.1,
        indice_smp=5.4,
        argila=30.0,
        mo=2.5,
        p=8.0,
        k=120.0,
        ctc_ph7=12.0,
        al=0.5,
        ca=3.0,
        mg=1.5,
        v_percent=55.0,
    )
    campos.update(sobrescreve)
    return AnaliseSolo(**campos)


def _contexto(**sobrescreve):
    campos = dict(
        cultura_id="soja",
        sistema_manejo="convencional",
        condicao_area="todos os casos",
        prnt=100.0,
        profundidade_incorporacao_cm=20.0,
    )
    campos.update(sobrescreve)
    return Contexto(**campos)


class TestGraosConvencionalDispara:
    """Caso oficial G-SOJA-01: pH 5,1 (< 5,5) dispara a calagem."""

    def test_g_soja_01_calcula_6_8_t_ha(self):
        trace = Trace()
        resultado = calcular_calagem(_analise(), "graos_convencional", _contexto(), trace)

        assert resultado["nc_t_ha"] == 6.8
        assert resultado["motivo"] is None

    def test_g_soja_01_registra_um_passo_no_trace(self):
        trace = Trace()
        calcular_calagem(_analise(), "graos_convencional", _contexto(), trace)

        assert len(trace) == 1
        passo = list(trace)[0]
        assert passo.saida == {"nc_t_ha": 6.8, "motivo": None}
        assert "Tab. 5.2" in passo.fonte

    def test_prnt_diferente_de_100_altera_a_dose_real(self):
        trace = Trace()
        resultado = calcular_calagem(
            _analise(), "graos_convencional", _contexto(prnt=75.0), trace
        )
        # NC tabela (6.8) x fator 1.0 x 100/75 = 9.0666... -> 9.1 (meio para cima)
        assert resultado["nc_t_ha"] == 9.1


class TestGraosConvencionalSemDisparo:
    """pH acima do limite de disparo do critério (5,5): sem necessidade de calagem."""

    def test_ph_5_8_nao_dispara(self):
        trace = Trace()
        resultado = calcular_calagem(
            _analise(ph_agua=5.8), "graos_convencional", _contexto(), trace
        )

        assert resultado["nc_t_ha"] == 0.0
        assert resultado["motivo"] == "ph_acima_do_disparo"

    def test_ph_exatamente_no_limite_nao_dispara(self):
        trace = Trace()
        resultado = calcular_calagem(
            _analise(ph_agua=5.5), "graos_convencional", _contexto(), trace
        )
        assert resultado["nc_t_ha"] == 0.0
        assert resultado["motivo"] == "ph_acima_do_disparo"


class TestSmpForaDaFaixa:
    def test_smp_acima_de_7_1_retorna_zero(self):
        trace = Trace()
        resultado = calcular_calagem(
            _analise(indice_smp=7.5), "graos_convencional", _contexto(), trace
        )
        assert resultado["nc_t_ha"] == 0.0
        assert resultado["motivo"] == "smp_acima_da_tabela"

    def test_smp_abaixo_de_4_4_usa_limite_inferior(self):
        trace = Trace()
        resultado = calcular_calagem(
            _analise(indice_smp=4.0), "graos_convencional", _contexto(), trace
        )
        # linha 4.4 (limite_inferior): nc_ph_6_0 = 21.0, fator 1.0, PRNT 100
        assert resultado["nc_t_ha"] == 21.0
        assert resultado["motivo"] is None


class TestCriterioInvalido:
    def test_criterio_inexistente_levanta_erro_calagem(self):
        trace = Trace()
        with pytest.raises(ErroCalagem, match="nao_existe"):
            calcular_calagem(_analise(), "nao_existe", _contexto(), trace)

    def test_criterio_com_smp_medio_de_duas_camadas_levanta_not_implemented(self):
        # graos_pd_com_restricoes usa decisao.tipo="ph_menor_que_e_al" (já implementado),
        # mas também dose.usar_smp_medio_das_camadas=true (D6, ainda pendente) — por isso
        # continua NotImplementedError, não pela decisão em si.
        trace = Trace()
        with pytest.raises(NotImplementedError):
            calcular_calagem(_analise(), "graos_pd_com_restricoes", _contexto(), trace)

    def test_criterio_fora_de_escopo_levanta_erro_calagem_nao_not_implemented(self):
        # arroz irrigado é excluído do escopo do SIRAS por decisão de projeto, não por
        # falta de implementação — por isso ErroCalagem, não NotImplementedError.
        trace = Trace()
        with pytest.raises(ErroCalagem, match="fora do escopo"):
            calcular_calagem(_analise(), "arroz_irrigado_solo_seco", _contexto(), trace)

        trace = Trace()
        with pytest.raises(ErroCalagem, match="fora do escopo"):
            calcular_calagem(_analise(), "arroz_irrigado_pregerminado", _contexto(), trace)


class TestDecisaoPhMenorQueEAl:
    """batata_e_batata_doce e frutiferas_ph55: disparo pH<5,5 E saturacao_al>10%."""

    def test_batata_dispara_com_ph_e_al_satisfeitos(self):
        analise = _analise(ph_agua=5.0, indice_smp=5.0, saturacao_al=15)
        trace = Trace()
        resultado = calcular_calagem(analise, "batata_e_batata_doce", _contexto(), trace)

        # Tab.5.2 SMP 5.0 x pH 5.5 = 6.6; fator 1.0; PRNT 100 -> 6.6
        assert resultado["nc_t_ha"] == 6.6
        assert resultado["motivo"] is None

    def test_batata_nao_dispara_quando_al_nao_satisfaz(self):
        analise = _analise(ph_agua=5.0, indice_smp=5.0, saturacao_al=5)
        trace = Trace()
        resultado = calcular_calagem(analise, "batata_e_batata_doce", _contexto(), trace)

        assert resultado["nc_t_ha"] == 0.0
        assert resultado["motivo"] == "condicao_ph_e_al_nao_satisfeita"

    def test_batata_nao_dispara_quando_ph_nao_satisfaz(self):
        analise = _analise(ph_agua=5.6, indice_smp=5.0, saturacao_al=15)
        trace = Trace()
        resultado = calcular_calagem(analise, "batata_e_batata_doce", _contexto(), trace)

        assert resultado["nc_t_ha"] == 0.0
        assert resultado["motivo"] == "condicao_ph_e_al_nao_satisfeita"

    def test_frutiferas_ph55_mesma_logica_criterio_diferente(self):
        analise = _analise(ph_agua=5.0, indice_smp=5.0, saturacao_al=15)
        trace = Trace()
        resultado = calcular_calagem(analise, "frutiferas_ph55", _contexto(), trace)
        assert resultado["nc_t_ha"] == 6.6


class TestExcecaoNaoAplicarSe:
    """CAL-02/CAL-04 (testes/casos/casos_recomendacao.json): exceção V>=65% E Al<10%
    do PD consolidado (graos_pd_consolidado, Tab. 5.3 nota 1)."""

    def test_cal_02_soja_pd_consolidado_excecao_nao_se_aplica(self):
        # V=50 (<65) e saturacao_al=15 (>=10): nenhuma condição basta, exceção não se aplica.
        analise = _analise(
            ph_agua=5.1, indice_smp=5.4, v_percent=50, saturacao_al=15,
            argila=45, mo=3.2, ctc_ph7=9.5,
        )
        contexto = _contexto(
            sistema_manejo="plantio_direto_consolidado", condicao_area="sem_restricoes", prnt=75.0,
        )
        trace = Trace()
        resultado = calcular_calagem(analise, "graos_pd_consolidado", contexto, trace)

        assert resultado["nc_t_ha"] == 2.3
        assert resultado["motivo"] is None

    def test_cal_04_milho_pd_consolidado_excecao_se_aplica(self):
        # V=70 (>=65) E saturacao_al=6 (<10): as duas condições valem, exceção dispensa a calagem.
        analise = _analise(
            ph_agua=5.2, indice_smp=5.6, v_percent=70, saturacao_al=6,
            argila=52, mo=4.1, ctc_ph7=12.0,
        )
        contexto = _contexto(
            sistema_manejo="plantio_direto_consolidado", condicao_area="sem_restricoes", prnt=100.0,
        )
        trace = Trace()
        resultado = calcular_calagem(analise, "graos_pd_consolidado", contexto, trace)

        assert resultado["nc_t_ha"] == 0.0
        assert resultado["motivo"] == "excecao_v_e_al"

    def test_saturacao_al_derivada_quando_nao_informada_diretamente(self):
        # Sem saturacao_al direta: deriva de ca/mg/k/al (D4). al alto e bases baixas -> m% alto.
        analise = _analise(
            ph_agua=5.2, indice_smp=5.6, v_percent=70, saturacao_al=None,
            al=5.0, ca=0.5, mg=0.2, k=39.1,  # k/391 = 0.1 cmolc/dm3
            argila=52, mo=4.1, ctc_ph7=12.0,
        )
        # CTC_efetiva = 0.5+0.2+0.1+5.0 = 5.8; m% = 5.0/5.8*100 = 86.2% (>=10, nao <10)
        assert analise.obter_saturacao_al() > 10


class TestBaixoPoderTampao:
    """CAL-06: SMP > 6,3 usa as equações polinomiais em vez da Tabela 5.2 (D2)."""

    def test_cal_06_milho_baixo_poder_tampao(self):
        analise = _analise(ph_agua=5.3, indice_smp=6.5, argila=18, mo=1.8, al=0.8, ctc_ph7=5.2)
        contexto = _contexto()
        trace = Trace()
        resultado = calcular_calagem(analise, "graos_convencional", contexto, trace)

        # NC = -0.516 + 0.805*1.8 + 2.435*0.8 = 2.881 -> 2.9
        assert resultado["nc_t_ha"] == 2.9

    def test_smp_exatamente_6_3_nao_usa_baixo_poder_tampao(self):
        # 6.3 nao e > 6.3, deve consultar a tabela normalmente.
        analise = _analise(ph_agua=5.3, indice_smp=6.3, argila=18, mo=1.8, al=0.8, ctc_ph7=5.2)
        trace = Trace()
        resultado = calcular_calagem(analise, "graos_convencional", _contexto(), trace)
        # Tabela 5.2, SMP 6.3, pH 6.0: nc_ph_6_0 = 1.8
        assert resultado["nc_t_ha"] == 1.8


class TestFator30cm:
    """CAL-07: macieira, incorporação a 30 cm (fator 1,5, Tab. 5.6 nota 5)."""

    def test_cal_07_macieira_incorporacao_30cm(self):
        analise = _analise(ph_agua=5.7, indice_smp=5.8, argila=48, mo=3.5, ctc_ph7=10.5)
        contexto = _contexto(
            cultura_id="macieira", sistema_manejo="qualquer", condicao_area="qualquer",
            prnt=85.0, profundidade_incorporacao_cm=30,
        )
        trace = Trace()
        resultado = calcular_calagem(analise, "macieira_oliveira", contexto, trace)

        # Tab.5.2 SMP 5.8 x pH 6.5 = 6.3; fator 1.0; x1.5 (30cm) = 9.45; PRNT 85 -> 11.1
        assert resultado["nc_t_ha"] == 11.1

    def test_fator_30cm_nao_aplica_com_incorporacao_a_20cm(self):
        analise = _analise(ph_agua=5.7, indice_smp=5.8, argila=48, mo=3.5, ctc_ph7=10.5)
        contexto = _contexto(
            cultura_id="macieira", sistema_manejo="qualquer", condicao_area="qualquer",
            prnt=100.0, profundidade_incorporacao_cm=20,
        )
        trace = Trace()
        resultado = calcular_calagem(analise, "macieira_oliveira", contexto, trace)
        # Sem o fator 1.5: 6.3 x fator 1.0, PRNT 100 -> 6.3
        assert resultado["nc_t_ha"] == 6.3


class TestSaturacaoBasesErvaMate:
    """CAL-08/CAL-09: erva-mate, critério por saturação por bases (Tab. 5.6)."""

    def test_cal_08_dispara_sem_excecao(self):
        analise = _analise(
            ph_agua=4.9, v_percent=32, ctc_ph7=8.0, ca=2.0, mg=0.8, argila=55, mo=4.8,
        )
        contexto = _contexto(cultura_id="erva-mate", sistema_manejo="qualquer", condicao_area="qualquer")
        trace = Trace()
        resultado = calcular_calagem(analise, "erva_mate_e_florestais", contexto, trace)

        # NC = ((40-32)/100) x 8.0 = 0.64 -> 0.6
        assert resultado["nc_t_ha"] == 0.6
        assert resultado["motivo"] is None

    def test_cal_09_excecao_ca_mg_suficientes(self):
        analise = _analise(
            ph_agua=5.4, v_percent=35, ctc_ph7=10.0, ca=4.5, mg=1.2, argila=50, mo=5.2,
        )
        contexto = _contexto(cultura_id="erva-mate", sistema_manejo="qualquer", condicao_area="qualquer")
        trace = Trace()
        resultado = calcular_calagem(analise, "erva_mate_e_florestais", contexto, trace)

        assert resultado["nc_t_ha"] == 0.0
        assert resultado["motivo"] == "ca_mg_suficientes"

    def test_v_acima_do_alvo_nao_dispara(self):
        analise = _analise(ph_agua=5.4, v_percent=45, ctc_ph7=10.0, ca=1.0, mg=0.2, argila=50, mo=5.2)
        contexto = _contexto(cultura_id="erva-mate", sistema_manejo="qualquer", condicao_area="qualquer")
        trace = Trace()
        resultado = calcular_calagem(analise, "erva_mate_e_florestais", contexto, trace)

        assert resultado["nc_t_ha"] == 0.0
        assert resultado["motivo"] == "v_acima_do_alvo"


class TestTetoAplicacaoSuperficial:
    """D9: teto de 5 t/ha em aplicação superficial, aplicado antes da conversão por PRNT."""

    def test_teto_trunca_quando_dose_ultrapassa_5_t_ha(self):
        # SMP baixo o bastante para que fator 1/4 ainda ultrapasse 5 t/ha antes do PRNT.
        analise = _analise(ph_agua=4.0, indice_smp=4.4, argila=50, mo=3.0, ctc_ph7=10.0)
        contexto = _contexto(
            sistema_manejo="plantio_direto_consolidado", condicao_area="sem_restricoes", prnt=100.0,
        )
        trace = Trace()
        resultado = calcular_calagem(analise, "graos_pd_consolidado", contexto, trace)

        # Tab.5.2 limite_inferior (4.4), pH 6.0 = 21.0; x1/4 = 5.25 > 5.0 -> truncado a 5.0
        assert resultado["nc_t_ha"] == 5.0
        passo = list(trace)[0]
        assert passo.entradas["truncado_pelo_teto_superficial"] is True


class TestTodosOsCriteriosDaBaseSaoCobertos:
    """Rede de segurança: todo critério de criterios_calagem.json precisa estar na
    allowlist de implementados OU levantar NotImplementedError. Nenhum pode passar
    despercebido e calcular um resultado incompleto silenciosamente.
    """

    IMPLEMENTADOS = {
        "graos_convencional",
        "graos_pd_implantacao",
        "graos_pd_consolidado",
        "aspargo",
        "olericolas_convencional",
        "olericolas_pd_consolidado",
        "macieira_oliveira",
        "frutiferas_demais",
        "frutiferas_ph55",
        "batata_e_batata_doce",
        "cana_e_tabaco",
        "erva_mate_e_florestais",
    }

    # Fora de escopo por decisão de projeto (criterio.notas), não por falta de código.
    FORA_DE_ESCOPO = {
        "arroz_irrigado_solo_seco",
        "arroz_irrigado_pregerminado",
    }

    def test_cada_criterio_esta_na_allowlist_ou_levanta_erro_esperado(self):
        from siras.conhecimento.carregador import carregar_dados_comum

        dados = carregar_dados_comum()
        criterios = dados["criterios_calagem"]["criterios"]

        for criterio in criterios:
            criterio_id = criterio["id"]
            trace = Trace()
            if criterio_id in self.IMPLEMENTADOS:
                resultado = calcular_calagem(_analise(), criterio_id, _contexto(), trace)
                assert "nc_t_ha" in resultado, f"criterio '{criterio_id}' não retornou nc_t_ha"
            elif criterio_id in self.FORA_DE_ESCOPO:
                with pytest.raises(ErroCalagem, match="fora do escopo"):
                    calcular_calagem(_analise(), criterio_id, _contexto(), trace)
            else:
                with pytest.raises(NotImplementedError):
                    calcular_calagem(_analise(), criterio_id, _contexto(), trace)


class TestResolverCriterioId:
    """Resolução cultura -> critério via mapa_culturas.json (dados/comum/)."""

    def test_soja_convencional_resolve_graos_convencional(self):
        resultado = resolver_criterio_id("soja", _contexto())
        assert resultado == "graos_convencional"

    def test_soja_pd_implantacao_resolve_criterio_correto(self):
        contexto = _contexto(
            sistema_manejo="plantio_direto",
            condicao_area="implantacao do sistema",
        )
        resultado = resolver_criterio_id("soja", contexto)
        assert resultado == "graos_pd_implantacao"

    def test_macieira_resolve_direto_pelo_criterio_calagem(self):
        # Override direto: ignora sistema_manejo/condicao_area do contexto.
        contexto = _contexto(
            sistema_manejo="irrelevante", condicao_area="irrelevante"
        )
        resultado = resolver_criterio_id("macieira", contexto)
        assert resultado == "macieira_oliveira"

    def test_erva_mate_resolve_direto_pelo_criterio_calagem(self):
        resultado = resolver_criterio_id("erva-mate", _contexto())
        assert resultado == "erva_mate_e_florestais"

    def test_cultura_nao_mapeada_levanta_erro_calagem(self):
        with pytest.raises(ErroCalagem, match="algodao"):
            resolver_criterio_id("algodao", _contexto())

    def test_milho_convencional_resolve_graos_convencional(self):
        resultado = resolver_criterio_id("milho", _contexto())
        assert resultado == "graos_convencional"

    def test_trigo_convencional_resolve_graos_convencional(self):
        resultado = resolver_criterio_id("trigo", _contexto())
        assert resultado == "graos_convencional"

    def test_feijao_convencional_resolve_graos_convencional(self):
        resultado = resolver_criterio_id("feijao", _contexto())
        assert resultado == "graos_convencional"

    def test_mapa_culturas_tem_as_21_culturas_de_graos(self):
        from siras.conhecimento.carregador import carregar_dados_comum, carregar_dados_graos

        dados_comuns = carregar_dados_comum()
        dados_graos = carregar_dados_graos()

        culturas_graos_adubacao = set(dados_graos["adubacao_n"]["culturas"].keys())
        culturas_mapa = {
            cultura
            for cultura, entrada in dados_comuns["mapa_culturas"]["culturas"].items()
            if entrada["grupo"] == "graos"
        }

        assert culturas_mapa == culturas_graos_adubacao

    def test_combinacao_sem_criterio_correspondente_levanta_erro_calagem(self):
        contexto = _contexto(sistema_manejo="convencional", condicao_area="condicao inexistente")
        with pytest.raises(ErroCalagem):
            resolver_criterio_id("soja", contexto)


class TestCalcularCalagemPorCultura:
    def test_g_soja_01_via_cultura(self):
        trace = Trace()
        resultado = calcular_calagem_por_cultura(_analise(), "soja", _contexto(), trace)
        assert resultado["nc_t_ha"] == 6.8
