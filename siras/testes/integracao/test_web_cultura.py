"""
Etapa 1 do fluxo: escolha da cultura e divulgação progressiva dos campos condicionais.

Critério de pronto (PLANO-FRONTEND §12): "soja nunca exibe 'fase do pomar'; macieira
sempre exibe". Mostrar todos os campos desde o início obrigaria todo usuário de soja a
processar perguntas que não lhe dizem respeito.

Os campos condicionais não são uma lista escrita no template: saem de `variavel_adicional`,
transcrito em cada cultura da base. Por isso os testes abaixo verificam a tela contra a
base, e não contra uma segunda lista escrita aqui.
"""

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.escopo import TOTAL_DE_CULTURAS_NO_ESCOPO, no_escopo_de_recomendacao
from siras.web import criar_app
from siras.web.formulario import GRUPOS

_DADOS = carregar_dados_comum()


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


def _tela(cliente, cultura_id):
    return cliente.get(f"/analise/dados?cultura_id={cultura_id}").get_data(as_text=True)


def test_a_escolha_de_cultura_abre(cliente):
    resposta = cliente.get("/analise")
    assert resposta.status_code == 200


def test_os_seis_grupos_aparecem(cliente):
    html = cliente.get("/analise").get_data(as_text=True)
    for _identificador, _icone, nome, _descricao in GRUPOS:
        assert nome in html, f"o grupo '{nome}' não aparece na tela de escolha"


def test_as_61_culturas_do_escopo_sao_oferecidas(cliente):
    """Seleção por reconhecimento, não por recordação (heurística 6 de Nielsen)."""
    html = cliente.get("/analise").get_data(as_text=True)

    no_escopo = [c for c in _DADOS["mapa_culturas"]["culturas"] if no_escopo_de_recomendacao(c)]
    assert len(no_escopo) == TOTAL_DE_CULTURAS_NO_ESCOPO

    for cultura_id in no_escopo:
        assert f"cultura_id={cultura_id}" in html, f"{cultura_id} não é oferecida"


def test_especie_florestal_nao_e_oferecida(cliente):
    html = cliente.get("/analise").get_data(as_text=True)
    for florestal in ("eucalipto", "pinus", "bracatinga"):
        assert f"cultura_id={florestal}" not in html


def test_especie_florestal_nao_abre_o_formulario(cliente):
    """Está mapeada para a aptidão e fora do escopo de recomendação (ADR 0006)."""
    resposta = cliente.get("/analise/dados?cultura_id=eucalipto")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/analise")


def test_soja_nunca_exibe_fase_do_pomar(cliente):
    assert "Fase do pomar" not in _tela(cliente, "soja")


def test_macieira_sempre_exibe_fase_do_pomar(cliente):
    assert "Fase do pomar" in _tela(cliente, "macieira")


@pytest.mark.parametrize(
    "cultura, rotulo",
    [
        ("videira", "Tipo de uva"),
        ("cana_de_acucar", "Ciclo da cana"),
        ("tabaco", "Tipo cultivado"),
        ("erva-mate", "Programa de adubação"),
    ],
)
def test_variavel_declarada_na_base_aparece_na_tela(cliente, cultura, rotulo):
    assert rotulo in _tela(cliente, cultura)


@pytest.mark.parametrize("cultura", ["soja", "tomate", "batata"])
def test_cultura_sem_variavel_declarada_nao_ganha_o_bloco(cliente, cultura):
    assert "Manejo da cultura" not in _tela(cliente, cultura)


def test_cultivo_e_antecedente_so_aparecem_em_graos(cliente):
    """Os dois são da lógica de grãos: cultivo muda a fração da correção de P e K, e o
    antecedente muda a dose de N. Em hortaliça não significam nada."""
    assert "1º cultivo" in _tela(cliente, "soja")
    assert "1º cultivo" not in _tela(cliente, "tomate")
    assert "Cultura antecedente" not in _tela(cliente, "macieira")


def test_laudo_de_frutifera_pelo_post_com_a_variavel_condicional(cliente):
    """O caminho inteiro de um grupo que não é grãos, incluindo a variável condicional."""
    dados_do_formulario = {
        "cultura_id": "citros", "criterio_id": "frutiferas_demais",
        "fase": "pre_plantio", "prnt": "100", "profundidade_incorporacao_cm": "20",
        "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
        "p": "11", "k": "96", "ctc_ph7": "9.4",
        "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
    }

    resposta = cliente.post("/analise/laudo", data=dados_do_formulario)

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert "Laudo de recomendação" in html
    assert "Citros" in html


def test_fase_ausente_em_frutifera_explica_o_que_falta(cliente):
    dados_do_formulario = {
        "cultura_id": "citros", "criterio_id": "frutiferas_demais",
        "prnt": "100", "profundidade_incorporacao_cm": "20",
        "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
        "p": "11", "k": "96", "ctc_ph7": "9.4",
        "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
    }

    resposta = cliente.post("/analise/laudo", data=dados_do_formulario)

    assert resposta.status_code == 422
    assert "informe fase" in resposta.get_data(as_text=True)
