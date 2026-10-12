"""
Testes de siras/motor/trace.py.

Testa:
- Trace acumula passos e expõe len/iter/bool corretamente
- registrar() retorna a própria saída, para uso em linha no motor
- os dicionários de entradas/saída são copiados, não referenciados
"""

from siras.motor.trace import PassoInferencia, Trace


class TestTraceVazio:
    def test_trace_novo_esta_vazio(self):
        trace = Trace()
        assert len(trace) == 0
        assert not trace
        assert list(trace) == []


class TestTraceRegistrar:
    def test_registrar_retorna_a_propria_saida(self):
        trace = Trace()
        saida = trace.registrar(
            regra="R-CAL-01: exemplo",
            entradas={"indice_smp": 5.4},
            saida={"nc_t_ha": 6.8},
            fonte="Manual 2016, Tab. 5.2, p. 70",
        )
        assert saida == {"nc_t_ha": 6.8}

    def test_registrar_acumula_passo(self):
        trace = Trace()
        trace.registrar("R1", {"a": 1}, {"b": 2}, "fonte 1")
        assert len(trace) == 1
        assert bool(trace) is True

        trace.registrar("R2", {"c": 3}, {"d": 4}, "fonte 2")
        assert len(trace) == 2

    def test_passos_mantem_ordem_de_registro(self):
        trace = Trace()
        trace.registrar("R1", {}, {}, "fonte 1")
        trace.registrar("R2", {}, {}, "fonte 2")

        passos = list(trace)
        assert [p.regra for p in passos] == ["R1", "R2"]

    def test_passo_registrado_tem_os_campos_corretos(self):
        trace = Trace()
        trace.registrar(
            regra="R-CAL-03",
            entradas={"indice_smp": 5.4, "ph_alvo": 6.0},
            saida={"nc_t_ha": 6.8},
            fonte="Manual 2016, Tab. 5.2 e 5.3",
        )
        passo = list(trace)[0]
        assert isinstance(passo, PassoInferencia)
        assert passo.regra == "R-CAL-03"
        assert passo.entradas == {"indice_smp": 5.4, "ph_alvo": 6.0}
        assert passo.saida == {"nc_t_ha": 6.8}
        assert passo.fonte == "Manual 2016, Tab. 5.2 e 5.3"

    def test_entradas_e_saida_sao_copiadas_nao_referenciadas(self):
        trace = Trace()
        entradas = {"indice_smp": 5.4}
        saida = {"nc_t_ha": 6.8}

        trace.registrar("R1", entradas, saida, "fonte")
        entradas["indice_smp"] = 999
        saida["nc_t_ha"] = 999

        passo = list(trace)[0]
        assert passo.entradas == {"indice_smp": 5.4}
        assert passo.saida == {"nc_t_ha": 6.8}


class TestTraceLimpar:
    def test_limpar_esvazia_o_trace(self):
        trace = Trace()
        trace.registrar("R1", {}, {}, "fonte 1")
        trace.registrar("R2", {}, {}, "fonte 2")

        trace.limpar()

        assert len(trace) == 0
        assert not trace
