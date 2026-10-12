"""
Bancada: as 61 culturas do escopo, cada uma pelo caminho real da aplicação.

Para cada cultura, o teste abre o formulário preenchido com o exemplo, lê da TELA o que
o navegador enviaria — valores dos campos e opção selecionada de cada seletor — e faz o
POST. Nenhum valor é escrito aqui: se a tela não oferecer o campo que o motor exige, o
POST falha e o teste acusa.

Foi assim que apareceram, de uma vez, três buracos que nenhum teste anterior via:

- sete culturas de grãos dosam N por matéria orgânica CRUZADA com a cultura antecedente,
  e o exemplo não preenchia a antecedente;
- o aspargo dosa por fase, e a tela não oferecia o campo — o Manual nomeia as fases de N
  ('instalacao') e as de P/K ('pre_plantio') diferente, e as duas listas estavam na base
  sem ninguém lê-las;
- a erva-mate exige o momento da aplicação dentro da fase, e o campo também não existia.

É o tipo de defeito que só aparece exercitando a cultura inteira: o motor estava certo
nos três casos, e a tela é que não perguntava.
"""

import re

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.escopo import TOTAL_DE_CULTURAS_NO_ESCOPO, no_escopo_de_recomendacao
from siras.web import criar_app

#: Bancada ampla: roda antes de entregar, e não a cada alteração. Concentra a maior
#: parte do tempo da suíte e repete em volume o que os testes por grupo cobrem por
#: amostra — ver conftest.py na raiz. Para rodá-la: python -m pytest --completa
pytestmark = pytest.mark.lenta

_DADOS = carregar_dados_comum()
_CULTURAS = sorted(
    cultura for cultura in _DADOS["mapa_culturas"]["culturas"]
    if no_escopo_de_recomendacao(cultura)
)


@pytest.fixture(scope="module")
def cliente():
    return criar_app({"TESTING": True}).test_client()


def _campos_da_tela(html: str) -> dict:
    """O que o navegador enviaria: valor de cada input e opção marcada de cada select."""
    campos = dict(re.findall(r'<input[^>]*id="(\w+)"[^>]*value="([^"]*)"', html))
    for nome, corpo in re.findall(r'<select[^>]*id="(\w+)"[^>]*>(.*?)</select>', html, re.S):
        escolhida = (
            re.search(r'<option value="([^"]*)" selected', corpo)
            or re.search(r'<option value="([^"]*)"', corpo)
        )
        if escolhida:
            campos[nome] = escolhida.group(1)
    return campos


def test_a_bancada_cobre_o_escopo_inteiro():
    assert len(_CULTURAS) == TOTAL_DE_CULTURAS_NO_ESCOPO


@pytest.mark.parametrize("cultura", _CULTURAS)
def test_toda_cultura_gera_laudo_pelo_exemplo(cliente, cultura):
    """Da escolha da cultura ao laudo, sem nenhum campo preenchido à mão."""
    tela = cliente.get(f"/analise/dados?cultura_id={cultura}&exemplo=1")
    assert tela.status_code == 200

    campos = _campos_da_tela(tela.get_data(as_text=True))
    campos["cultura_id"] = cultura

    resposta = cliente.post("/analise/laudo", data=campos)

    if resposta.status_code != 200:
        texto = re.sub(r"<[^>]+>", " ", resposta.get_data(as_text=True))
        motivo = re.search(r"O laudo não foi gerado\s*(.{0,160})", texto)
        pytest.fail(
            f"{cultura}: {re.sub(r'  +', ' ', motivo.group(1)).strip() if motivo else resposta.status_code}"
        )


@pytest.mark.parametrize("cultura", _CULTURAS)
def test_todo_laudo_traz_as_quatro_saidas_e_a_trilha(cliente, cultura):
    """Um laudo que sai sem dose ou sem trilha passaria no teste acima e mesmo assim
    estaria quebrado."""
    campos = _campos_da_tela(
        cliente.get(f"/analise/dados?cultura_id={cultura}&exemplo=1").get_data(as_text=True)
    )
    campos["cultura_id"] = cultura
    html = cliente.post("/analise/laudo", data=campos).get_data(as_text=True)

    assert "Calcário" in html
    assert "Nitrogênio" in html
    assert "De onde vem cada número" in html
    assert "Aptidão edáfica" in html
    # Quatro cartões de veredito, sempre: calcário, N, P2O5 e K2O. O delimitador depois
    # de "dose" é necessário: sem ele a contagem pega dose__nome, dose__val e dose__obs.
    assert len(re.findall(r'class="dose[ "]', html)) == 4


@pytest.mark.parametrize("cultura", _CULTURAS)
def test_a_leitura_ao_vivo_responde_para_toda_cultura(cliente, cultura):
    campos = _campos_da_tela(
        cliente.get(f"/analise/dados?cultura_id={cultura}&exemplo=1").get_data(as_text=True)
    )
    campos["cultura_id"] = cultura

    corpo = cliente.post("/api/interpretar", json=campos).get_json()

    assert corpo["classes"]["p"], f"{cultura}: sem classe de fósforo na leitura ao vivo"
    assert corpo["classes"]["k"], f"{cultura}: sem classe de potássio na leitura ao vivo"
    assert "Calcário estimado" in corpo["html"]
