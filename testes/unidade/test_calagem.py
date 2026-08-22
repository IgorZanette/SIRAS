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

    def test_criterio_fora_de_escopo_levanta_not_implemented(self):
        trace = Trace()
        with pytest.raises(NotImplementedError):
            calcular_calagem(_analise(), "graos_pd_consolidado", _contexto(), trace)

    def test_criterio_por_saturacao_bases_levanta_not_implemented(self):
        trace = Trace()
        with pytest.raises(NotImplementedError):
            calcular_calagem(_analise(), "erva_mate_e_florestais", _contexto(), trace)

    def test_criterio_com_fator_30cm_levanta_not_implemented(self):
        # Regressão: macieira_oliveira e frutiferas_demais tem dose.fator_30cm (ajuste de
        # incorporação a 30 cm, x1.5). Sem essa guarda, o calculo roda e sai errado
        # (faltando o fator), sem erro nenhum — exatamente o que D3 (docs/decisoes/0002)
        # existe para evitar.
        trace = Trace()
        with pytest.raises(NotImplementedError):
            calcular_calagem(_analise(), "macieira_oliveira", _contexto(), trace)

        trace = Trace()
        with pytest.raises(NotImplementedError):
            calcular_calagem(_analise(), "frutiferas_demais", _contexto(), trace)


class TestTodosOsCriteriosDaBaseSaoCobertos:
    """Rede de segurança: todo critério de criterios_calagem.json precisa estar na
    allowlist de implementados OU levantar NotImplementedError. Nenhum pode passar
    despercebido e calcular um resultado incompleto silenciosamente.
    """

    IMPLEMENTADOS = {
        "graos_convencional",
        "graos_pd_implantacao",
        "aspargo",
        "olericolas_convencional",
        "cana_e_tabaco",
    }

    def test_cada_criterio_esta_na_allowlist_ou_levanta_not_implemented(self):
        from siras.conhecimento.carregador import carregar_dados_comum

        dados = carregar_dados_comum()
        criterios = dados["criterios_calagem"]["criterios"]

        for criterio in criterios:
            criterio_id = criterio["id"]
            trace = Trace()
            if criterio_id in self.IMPLEMENTADOS:
                resultado = calcular_calagem(_analise(), criterio_id, _contexto(), trace)
                assert "nc_t_ha" in resultado, f"criterio '{criterio_id}' não retornou nc_t_ha"
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
        with pytest.raises(ErroCalagem, match="milho"):
            resolver_criterio_id("milho", _contexto())

    def test_combinacao_sem_criterio_correspondente_levanta_erro_calagem(self):
        contexto = _contexto(sistema_manejo="convencional", condicao_area="condicao inexistente")
        with pytest.raises(ErroCalagem):
            resolver_criterio_id("soja", contexto)


class TestCalcularCalagemPorCultura:
    def test_g_soja_01_via_cultura(self):
        trace = Trace()
        resultado = calcular_calagem_por_cultura(_analise(), "soja", _contexto(), trace)
        assert resultado["nc_t_ha"] == 6.8
