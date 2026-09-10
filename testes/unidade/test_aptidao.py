"""
Testes de siras/motor/aptidao.py contra as regras já congeladas em docs/CCAE-v1.0.md.

Estes são testes de unidade/fronteira escritos pelo desenvolvedor para verificar que o
código aplica corretamente a especificação — não são o conjunto de conformidade oficial.
Esse é testes/casos/casos_aptidao.json, cujo campo "referencia" só o autor preenche, à
mão, a partir do Manual, sem consultar este arquivo (CLAUDE.md, regra absoluta de dados
agronômicos; CCAE-v1.0.md Seção 9.1).
"""

import copy

import pytest

from siras.conhecimento.carregador import (
    carregar_dados_comum,
    carregar_dados_erva_mate,
    carregar_dados_frutiferas,
    carregar_dados_hortalicas,
    carregar_dados_outras,
    carregar_dados_tuberculos,
)
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.adubacao import grupo_exigencia
from siras.motor.aptidao import ErroAptidao, _resolver_grupo_p_ou_k, avaliar_aptidao
from siras.motor.trace import Trace

_DADOS = carregar_dados_comum()


def _analise(**sobrescreve):
    campos = dict(
        ph_agua=6.5,
        indice_smp=6.5,
        argila=30.0,
        mo=6.0,
        p=100.0,
        k=300.0,
        ctc_ph7=20.0,
        al=0.0,
        ca=5.0,
        mg=2.0,
        v_percent=80.0,
    )
    campos.update(sobrescreve)
    return AnaliseSolo(**campos)


def _contexto(**sobrescreve):
    campos = dict(
        cultura_id="milho",
        sistema_manejo="convencional",
        condicao_area="todos os casos",
        prnt=100.0,
        profundidade_incorporacao_cm=20.0,
    )
    campos.update(sobrescreve)
    return Contexto(**campos)


def _avaliar(analise, cultura_id="milho", cenario="ATUAL", contexto=None, dados=None):
    return avaliar_aptidao(
        analise, cultura_id, cenario, contexto or _contexto(cultura_id=cultura_id), Trace(),
        dados=dados if dados is not None else _DADOS,
    )


def _fator(resultado, id_fator):
    return next(f for f in resultado.fatores if f.id == id_fator)


class TestF1AcidezComPhReferencia:
    """Milho: pH de referência 6,0 (ph_referencia.json)."""

    def test_ph_acima_da_referencia_e_nulo(self):
        r = _avaliar(_analise(ph_agua=6.0))
        assert _fator(r, "F1_acidez").rotulo == "NULO"

    def test_ph_entre_5_5_e_referencia_e_ligeiro(self):
        r = _avaliar(_analise(ph_agua=5.7))
        assert _fator(r, "F1_acidez").rotulo == "LIGEIRO"

    def test_ph_exato_5_5_e_ligeiro(self):
        r = _avaliar(_analise(ph_agua=5.5))
        assert _fator(r, "F1_acidez").rotulo == "LIGEIRO"

    def test_ph_abaixo_5_5_m_percent_29_9_e_moderado(self):
        r = _avaliar(_analise(ph_agua=5.4, saturacao_al=29.9))
        assert _fator(r, "F1_acidez").rotulo == "MODERADO"

    def test_ph_abaixo_5_5_m_percent_30_e_forte(self):
        """CCAE §F1 escreve "m% < 30" / "30 <= m% <= 50" / "m% > 50": o limite 30,0 está
        na faixa do meio, logo é FORTE. Este teste afirmava MODERADO até 2026-09-09,
        aplicando a convenção de limite superior das tabelas de P/K, que não vale aqui
        (docs/HANDOFF-aptidao.md §4). O gabarito de conformidade CONF-FR-23, construído
        com m% = 30,0 exatos por aritmética reversa, é o oráculo desta linha."""
        r = _avaliar(_analise(ph_agua=5.4, saturacao_al=30.0))
        assert _fator(r, "F1_acidez").rotulo == "FORTE"

    def test_ph_abaixo_5_5_m_percent_30_1_e_forte(self):
        r = _avaliar(_analise(ph_agua=5.4, saturacao_al=30.1))
        assert _fator(r, "F1_acidez").rotulo == "FORTE"

    def test_ph_abaixo_5_5_m_percent_50_e_forte(self):
        r = _avaliar(_analise(ph_agua=5.4, saturacao_al=50.0))
        assert _fator(r, "F1_acidez").rotulo == "FORTE"

    def test_ph_abaixo_5_5_m_percent_50_1_e_muito_forte(self):
        r = _avaliar(_analise(ph_agua=5.4, saturacao_al=50.1))
        assert _fator(r, "F1_acidez").rotulo == "MUITO_FORTE"


class TestF1AcidezSemPhReferencia:
    """Erva-mate: sem pH de referência (ph_referencia.json, grupo null); grupo_p/grupo_k=3
    (Anexo 2, p. 361-366, ver interpretacao_p.json/interpretacao_k.json e docs/decisoes/0005)."""

    def test_v_percent_suficiente_e_nulo(self):
        r = _avaliar(_analise(v_percent=40.0, ca=0.0, mg=0.0), cultura_id="erva-mate")
        assert _fator(r, "F1_acidez").rotulo == "NULO"

    def test_v_percent_insuficiente_sem_excecao_e_moderado(self):
        r = _avaliar(_analise(v_percent=39.9, ca=0.0, mg=0.0), cultura_id="erva-mate")
        assert _fator(r, "F1_acidez").rotulo == "MODERADO"

    def test_v_percent_insuficiente_com_excecao_ca_mg_e_nulo(self):
        r = _avaliar(_analise(v_percent=10.0, ca=4.0, mg=1.0), cultura_id="erva-mate")
        assert _fator(r, "F1_acidez").rotulo == "NULO"

    def test_ph_nao_e_avaliado_neste_ramo(self):
        # pH bem ácido não deveria importar: só V%/Ca/Mg decidem.
        r = _avaliar(_analise(ph_agua=4.0, v_percent=40.0, ca=0.0, mg=0.0), cultura_id="erva-mate")
        assert _fator(r, "F1_acidez").rotulo == "NULO"

    def test_f2_e_f3_tambem_resolvem_para_erva_mate(self):
        # Confirma que o gap de catálogo do grupo_exigencia (achado ao testar F1) foi
        # mesmo corrigido, não só contornado no teste.
        r = _avaliar(_analise(argila=30.0, p=100.0, k=300.0), cultura_id="erva-mate")
        assert r.classe != "INDETERMINADA"


class TestCatalogoGrupoPK:
    """grupo_p e grupo_k são eixos independentes (CCAE Sec. 6, F3, 'armadilha conhecida') —
    nunca derivar um do outro. Sentinela contra reintroduzir a suposição 'ramo (b) de F1
    (sem pH de referência) implica grupo_p == grupo_k == 3', que é falsa para a mandioca."""

    def test_florestais_sao_grupo_3_em_p_e_k(self):
        for cultura in ("araucária", "acácia-negra", "bracatinga", "cedro-australiano", "eucalipto", "pinus"):
            assert grupo_exigencia(
                cultura, _DADOS["mapa_culturas"], _DADOS["interpretacao_p"]["grupos_exigencia"],
                "interpretacao_p.json",
            ) == "grupo_3"
            assert grupo_exigencia(
                cultura, _DADOS["mapa_culturas"], _DADOS["interpretacao_k"]["grupos_exigencia"],
                "interpretacao_k.json",
            ) == "grupo_3"

    def test_mandioca_diverge_grupo_p_3_grupo_k_2(self):
        assert grupo_exigencia(
            "mandioca", _DADOS["mapa_culturas"], _DADOS["interpretacao_p"]["grupos_exigencia"],
            "interpretacao_p.json",
        ) == "grupo_3"
        assert grupo_exigencia(
            "mandioca", _DADOS["mapa_culturas"], _DADOS["interpretacao_k"]["grupos_exigencia"],
            "interpretacao_k.json",
        ) == "grupo_2"


def _todas_entradas_com_grupo_exigencia_transcrito():
    """Toda cultura com grupo_exigencia.p/.k já transcrito do Anexo 2 em algum dos cinco
    arquivos de adubação por grupo (docs/decisoes/0005, D5.7) — não hardcoda nenhum valor
    numérico próprio, só compara a resolução do motor contra o que o autor já conferiu."""
    carregadores = (
        carregar_dados_hortalicas, carregar_dados_tuberculos, carregar_dados_outras,
        carregar_dados_frutiferas, carregar_dados_erva_mate,
    )
    casos = []
    for carregar in carregadores:
        for entrada in carregar()["adubacao"]["culturas"].values():
            grupo = entrada.get("grupo_exigencia")
            if not grupo:
                continue
            for cultura in entrada.get("culturas_incluidas", []):
                casos.append(pytest.param(cultura, grupo["p"], grupo["k"], id=cultura))
    return casos


@pytest.mark.parametrize("cultura_id, grupo_p, grupo_k", _todas_entradas_com_grupo_exigencia_transcrito())
def test_resolucao_bate_com_grupo_exigencia_ja_transcrito(cultura_id, grupo_p, grupo_k):
    assert _resolver_grupo_p_ou_k(cultura_id, "p", _DADOS) == f"grupo_{grupo_p}"
    assert _resolver_grupo_p_ou_k(cultura_id, "k", _DADOS) == f"grupo_{grupo_k}"


class TestForaDeEscopo:
    """CCAE-v1.0.md Sec. 1.3: arroz irrigado por alagamento e mandioca ficam fora do
    escopo da aptidão edáfica na v1.0, mesmo já tendo grupo_p/grupo_k catalogados."""

    def test_mandioca_levanta_erro_de_escopo(self):
        with pytest.raises(ErroAptidao):
            _avaliar(_analise(v_percent=10.0, ca=0.0, mg=0.0), cultura_id="mandioca")

    def test_arroz_irrigado_levanta_erro_de_escopo(self):
        with pytest.raises(ErroAptidao):
            _avaliar(_analise(), cultura_id="arroz-irrigado")


class TestF2Fosforo:
    """Milho: grupo_2 de P (Tabela 6.4). Argila 30% -> classe_argila 3."""

    def test_muito_baixo_no_limite_e_muito_forte(self):
        r = _avaliar(_analise(argila=30.0, p=6.0))
        assert _fator(r, "F2_fosforo").rotulo == "MUITO_FORTE"

    def test_logo_acima_do_limite_e_forte(self):
        r = _avaliar(_analise(argila=30.0, p=6.1))
        assert _fator(r, "F2_fosforo").rotulo == "FORTE"

    def test_alto_e_nulo(self):
        r = _avaliar(_analise(argila=30.0, p=25.0))
        assert _fator(r, "F2_fosforo").rotulo == "NULO"

    def test_muito_alto_gera_alerta_ambiental_sem_mudar_grau(self):
        r = _avaliar(_analise(argila=30.0, p=37.0))
        assert _fator(r, "F2_fosforo").rotulo == "NULO"
        assert any("F2_fosforo" in alerta and "Muito alto" in alerta for alerta in r.alertas)


class TestF3Potassio:
    """Milho: grupo_2 de K (Tabela 6.9). CTC 10,0 -> faixa_ctc 'b'."""

    def test_muito_baixo_no_limite_e_muito_forte(self):
        r = _avaliar(_analise(ctc_ph7=10.0, k=30.0))
        assert _fator(r, "F3_potassio").rotulo == "MUITO_FORTE"

    def test_logo_acima_do_limite_e_forte(self):
        r = _avaliar(_analise(ctc_ph7=10.0, k=30.1))
        assert _fator(r, "F3_potassio").rotulo == "FORTE"


class TestF4CalcioMagnesio:
    def test_calcio_baixo_domina_sobre_magnesio_alto(self):
        r = _avaliar(_analise(ca=1.0, mg=2.0))
        assert _fator(r, "F4_ca_mg").rotulo == "MODERADO"

    def test_ambos_altos_e_nulo(self):
        r = _avaliar(_analise(ca=5.0, mg=2.0))
        assert _fator(r, "F4_ca_mg").rotulo == "NULO"


class TestF5Ctc:
    def test_ctc_baixa_e_moderado(self):
        r = _avaliar(_analise(ctc_ph7=7.5))
        assert _fator(r, "F5_ctc").rotulo == "MODERADO"

    def test_ctc_alta_e_nulo(self):
        r = _avaliar(_analise(ctc_ph7=20.0))
        assert _fator(r, "F5_ctc").rotulo == "NULO"


class TestF6MateriaOrganica:
    def test_mo_baixo_e_moderado(self):
        r = _avaliar(_analise(mo=2.5))
        assert _fator(r, "F6_mo").rotulo == "MODERADO"

    def test_mo_alto_e_nulo(self):
        r = _avaliar(_analise(mo=6.0))
        assert _fator(r, "F6_mo").rotulo == "NULO"


class TestF7Textura:
    def test_argila_baixa_classe_4_e_moderado(self):
        r = _avaliar(_analise(argila=15.0, p=100.0))
        assert _fator(r, "F7_textura").rotulo == "MODERADO"

    def test_argila_alta_classe_1_e_nulo(self):
        r = _avaliar(_analise(argila=70.0, p=100.0))
        assert _fator(r, "F7_textura").rotulo == "NULO"

    def test_f7_desativado_por_config_e_sempre_nulo(self):
        dados = copy.deepcopy(_DADOS)
        dados["config_aptidao"]["F7_ATIVO"] = False
        r = _avaliar(_analise(argila=15.0, p=100.0), dados=dados)
        assert _fator(r, "F7_textura").rotulo == "NULO"


class TestComposicao:
    def test_fator_mais_limitante_determina_a_classe(self):
        # Tudo bom, só P muito baixo (FORTE) -> classe RESTRITA, F2 determinante.
        r = _avaliar(_analise(argila=30.0, p=6.1))
        assert r.grau_final == 3
        assert r.classe == "RESTRITA"
        assert r.fator_determinante == "F2_fosforo"

    def test_empate_resolve_pela_ordem_f1_a_f7(self):
        # F1 LIGEIRO (grau 1) e F5 baixa (grau 2, capped) -> quem manda é o maior grau
        # sozinho (F5); construir empate real exige dois fatores no mesmo grau máximo.
        # Aqui: F4 (Ca baixo) e F5 (CTC baixa) empatam em MODERADO; F4 vem primeiro.
        r = _avaliar(_analise(ca=1.0, mg=2.0, ctc_ph7=7.5))
        assert r.grau_final == 2
        assert r.fator_determinante == "F4_ca_mg"

    def test_tudo_bom_e_apta(self):
        # argila 70% -> classe 1 (F7 e classe de argila do F2 nulos); os demais campos
        # já vêm bons por padrão em _analise().
        r = _avaliar(_analise(argila=70.0))
        assert r.classe == "APTA"
        assert r.grau_final == 0

    def test_cultura_desconhecida_e_indeterminada(self):
        r = _avaliar(_analise(), cultura_id="cultura-que-nao-existe-no-catalogo")
        assert r.classe == "INDETERMINADA"
        assert r.grau_final is None
        assert r.alertas


class TestRebaixamentoPorAcumulo:
    def test_desativado_por_padrao_nao_rebaixa(self):
        # F4, F5, F6 em MODERADO (3 fatores) mas REBAIXAMENTO_POR_ACUMULO=False (default).
        r = _avaliar(_analise(ca=1.0, ctc_ph7=7.5, mo=2.5))
        assert r.classe == "APTA_COM_RESTRICOES"
        assert r.rebaixamento_aplicado is False

    def test_ativado_com_3_fatores_moderados_rebaixa_uma_classe(self):
        dados = copy.deepcopy(_DADOS)
        dados["config_aptidao"]["REBAIXAMENTO_POR_ACUMULO"] = True
        r = _avaliar(_analise(ca=1.0, ctc_ph7=7.5, mo=2.5), dados=dados)
        assert r.classe == "RESTRITA"
        assert r.rebaixamento_aplicado is True


class TestCenarioPotencial:
    def test_fatores_corrigiveis_viram_nulo(self):
        analise = _analise(argila=30.0, p=6.1, k=30.1, ca=1.0, mo=2.5, ph_agua=6.0)
        r = _avaliar(analise, cenario="POTENCIAL")
        assert _fator(r, "F2_fosforo").rotulo == "NULO"
        assert _fator(r, "F3_potassio").rotulo == "NULO"
        assert _fator(r, "F4_ca_mg").rotulo == "NULO"
        assert _fator(r, "F6_mo").rotulo == "NULO"

    def test_f5_e_f7_permanecem_no_potencial(self):
        analise = _analise(ctc_ph7=7.5, argila=15.0)
        r_atual = _avaliar(analise, cenario="ATUAL")
        r_potencial = _avaliar(analise, cenario="POTENCIAL")
        assert _fator(r_atual, "F5_ctc").rotulo == _fator(r_potencial, "F5_ctc").rotulo == "MODERADO"
        assert _fator(r_atual, "F7_textura").rotulo == _fator(r_potencial, "F7_textura").rotulo == "MODERADO"

    def test_f1_sem_calagem_disparada_permanece_inalterado(self):
        # pH 5,7 -> LIGEIRO no ATUAL; o Manual não recomenda calcário nessa faixa
        # (graos_convencional só dispara com pH < 5,5), então nada muda no POTENCIAL.
        analise = _analise(ph_agua=5.7, indice_smp=6.5)
        r = _avaliar(analise, cenario="POTENCIAL")
        assert _fator(r, "F1_acidez").rotulo == "LIGEIRO"

    def test_f1_com_calagem_exequivel_vira_nulo(self):
        # pH 5,1, SMP 5,4 (caso oficial G-SOJA-01 de test_calagem.py: NC = 6,8 t/ha,
        # incorporado) -> abaixo do teto de 20 t/ha -> exequível.
        analise = _analise(ph_agua=5.1, indice_smp=5.4, saturacao_al=60.0)
        r = _avaliar(analise, cenario="POTENCIAL")
        assert _fator(r, "F1_acidez").rotulo == "NULO"
        assert "correcao_parcelada" not in r.alertas

    def test_f1_com_calagem_inexequivel_permanece_ligeiro_e_alerta(self):
        dados = copy.deepcopy(_DADOS)
        dados["config_aptidao"]["NC_MAX_INCORPORADO_T_HA"] = 0.1
        analise = _analise(ph_agua=5.1, indice_smp=5.4, saturacao_al=60.0)
        r = _avaliar(analise, cenario="POTENCIAL", dados=dados)
        assert _fator(r, "F1_acidez").rotulo == "LIGEIRO"
        assert "correcao_parcelada" in r.alertas


def test_cenario_invalido_levanta_value_error():
    with pytest.raises(ValueError):
        _avaliar(_analise(), cenario="FUTURO")


def test_determinismo():
    analise = _analise(argila=30.0, p=6.1, ph_agua=5.4, saturacao_al=40.0)
    resultados = [_avaliar(analise) for _ in range(20)]
    assert len({(r.classe, r.grau_final, r.fator_determinante) for r in resultados}) == 1
