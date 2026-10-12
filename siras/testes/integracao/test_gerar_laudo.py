"""
Testes do ponto de entrada único do motor, gerar_laudo().

Diferente de testes/unidade/test_casos_validados.py, que chama calcular_calagem() com o
criterio_id já resolvido, aqui o caminho é o completo — inclusive resolver_criterio_id()
a partir de cultura + sistema de manejo + condição da área. É esse caminho que a camada
web vai exercitar.

Os valores esperados de calagem e adubação vêm de testes/casos/casos_recomendacao.json,
campo `referencia`, calculado à mão pelo autor. Nenhum número agronômico é escrito aqui.

A aptidão não é conferida contra referência neste arquivo: os casos de recomendação não
trazem Ca, Mg nem V%, e os testes completam esses campos com zero (mesma convenção de
test_casos_validados.py). Um laudo com Ca=0 e Mg=0 tem calagem e adubação válidas e
aptidão sem sentido agronômico — quem valida a aptidão é o conjunto de casos de
testes/unidade/test_conformidade_aptidao.py.
"""

import json
from pathlib import Path

import pytest

from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.laudo import ErroLaudo, gerar_laudo

_CAMINHO_CASOS = Path(__file__).parent.parent / "casos" / "casos_recomendacao.json"

#: Condição da área transcrita em dados/comum/criterios_calagem.json para o critério
#: graos_convencional. resolver_criterio_id() casa a string exata.
_CONDICAO_AREA_GRAOS_CONVENCIONAL = "todos os casos"

_CAMPOS_ANALISE_PADRAO = dict(
    ph_agua=7.0, indice_smp=6.0, argila=0.0, mo=0.0, p=0.0, k=0.0, ctc_ph7=0.0,
    al=0.0, ca=0.0, mg=0.0, v_percent=0.0, saturacao_al=None,
)


def _casos():
    dados = json.loads(_CAMINHO_CASOS.read_text(encoding="utf-8"))
    return {caso["id"]: caso for caso in dados["casos"]}


def _analise(entrada: dict) -> AnaliseSolo:
    campos = dict(_CAMPOS_ANALISE_PADRAO)
    for chave, valor in entrada.items():
        if chave in campos:
            campos[chave] = valor
    return AnaliseSolo(**campos)


def _contexto(entrada: dict) -> Contexto:
    return Contexto(
        cultura_id=entrada["cultura"],
        sistema_manejo=entrada["sistema_manejo"],
        condicao_area=_CONDICAO_AREA_GRAOS_CONVENCIONAL,
        prnt=entrada["prnt"],
        profundidade_incorporacao_cm=entrada["profundidade_incorporacao_cm"],
        expectativa_rendimento=entrada.get("expectativa_rendimento"),
        cultivo=entrada.get("cultivo", 1),
    )


def _laudo_do_caso(caso_id: str):
    caso = _casos()[caso_id]
    entrada = caso["entrada"]
    return caso, gerar_laudo(_analise(entrada), entrada["cultura"], _contexto(entrada))


def test_adu_01_laudo_completo_bate_com_a_referencia():
    """Caso ponta a ponta: calagem não disparada + classes de P e K + N, P2O5 e K2O."""
    caso, laudo = _laudo_do_caso("ADU-01")
    referencia = caso["referencia"]

    assert laudo.calagem.criterio_id == "graos_convencional"
    assert laudo.calagem.nc_t_ha == referencia["nc_t_ha"]
    assert laudo.calagem.motivo == referencia["motivo_sem_calagem"]

    assert laudo.adubacao.classe_p == referencia["classe_p"]
    assert laudo.adubacao.classe_k == referencia["classe_k"]
    assert laudo.adubacao.n == referencia["n"]
    assert laudo.adubacao.p2o5 == referencia["p2o5"]
    assert laudo.adubacao.k2o == referencia["k2o"]


def test_cal_01_dose_de_calcario_bate_com_a_referencia():
    """Mesma cultura, caso em que a calagem dispara: a dose tem de vir da Tab. 5.2."""
    caso, laudo = _laudo_do_caso("CAL-01")

    assert laudo.calagem.nc_t_ha == caso["referencia"]["nc_t_ha"]
    assert laudo.calagem.motivo is None
    assert laudo.grupo == "graos"


def test_laudo_registra_a_trilha_de_calagem_adubacao_e_aptidao():
    """A trilha é o diferencial declarado do SIRAS: nenhum módulo pode sair dela."""
    _, laudo = _laudo_do_caso("ADU-01")
    regras = [passo.regra for passo in laudo.trace]

    assert any(regra.startswith("graos_convencional") for regra in regras)
    assert any(regra.startswith("R-ADU-01") for regra in regras)
    assert any(regra.startswith("R-ADU-02") for regra in regras)
    assert any(regra.startswith("R-ADU-03") for regra in regras)
    assert regras.count("composicao_aptidao") == 2  # ATUAL e POTENCIAL

    assert all(passo.fonte for passo in laudo.trace), "todo passo precisa citar a fonte"


def test_laudo_traz_os_dois_cenarios_de_aptidao():
    """CCAE §7: a diferença entre ATUAL e POTENCIAL é o ganho atribuível à recomendação."""
    _, laudo = _laudo_do_caso("ADU-01")

    assert laudo.aptidao_atual.cenario == "ATUAL"
    assert laudo.aptidao_potencial.cenario == "POTENCIAL"


def test_gerar_laudo_e_deterministico():
    """Mesma entrada, mesmo laudo — requisito do contrato do motor (CLAUDE.md)."""
    _, primeiro = _laudo_do_caso("ADU-01")
    _, segundo = _laudo_do_caso("ADU-01")

    assert primeiro.calagem == segundo.calagem
    assert primeiro.adubacao == segundo.adubacao
    assert [passo.regra for passo in primeiro.trace] == [passo.regra for passo in segundo.trace]


def test_cultura_divergente_do_contexto_e_recusada():
    """Contexto montado com outra cultura produziria calagem de uma e adubação de outra."""
    caso = _casos()["ADU-01"]
    entrada = caso["entrada"]

    with pytest.raises(ErroLaudo, match="diverge de contexto.cultura_id"):
        gerar_laudo(_analise(entrada), "milho", _contexto(entrada))


def test_variavel_condicional_ausente_falha_com_mensagem_de_dominio():
    """Frutífera exige a fase do pomar. Sem a guarda, a ausência estoura como TypeError
    de argumento posicional — mensagem de interpretador Python chegando ao técnico."""
    entrada = _casos()["ADU-01"]["entrada"]
    contexto = Contexto(
        cultura_id="macieira",
        sistema_manejo="qualquer",
        condicao_area="area total ou faixa de plantio",
        prnt=entrada["prnt"],
        profundidade_incorporacao_cm=entrada["profundidade_incorporacao_cm"],
    )

    with pytest.raises(ErroLaudo, match="informe fase"):
        gerar_laudo(_analise(entrada), "macieira", contexto)


def test_cultura_fora_do_mapa_falha_apontando_o_arquivo():
    """A mensagem precisa dizer onde falta o dado — é transcrição pendente, não bug.

    O identificador é um sentinela, e não uma cultura real de propósito: quando a
    transcrição do mapa avança, uma cultura real deixa de servir de exemplo e o teste
    passa a falhar por motivo errado. Foi o que aconteceu com 'tomate'.
    """
    entrada = _casos()["ADU-01"]["entrada"]
    inexistente = "cultura_nao_mapeada_para_teste"
    contexto = Contexto(
        cultura_id=inexistente,
        sistema_manejo="convencional",
        condicao_area=_CONDICAO_AREA_GRAOS_CONVENCIONAL,
        prnt=entrada["prnt"],
        profundidade_incorporacao_cm=entrada["profundidade_incorporacao_cm"],
    )

    with pytest.raises(ErroLaudo, match="mapa_culturas.json"):
        gerar_laudo(_analise(entrada), inexistente, contexto)
