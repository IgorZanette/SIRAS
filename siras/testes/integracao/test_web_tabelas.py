"""
Tabelas do Manual em tela (/tabelas).

O que estes testes guardam não é o layout: é que o que a tela mostra continue sendo o que
a base transcreveu. Uma tabela de conferência que discorde da base é pior que nenhuma —
o técnico confere o número contra ela e conclui que o laudo está errado.
"""

import pathlib
import pathlib
import re

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.relatorio.apresentacao import formatar_numero
from siras.relatorio.tabelas import CATALOGO, construir
from siras.web import criar_app

_DADOS = carregar_dados_comum()


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


def test_o_indice_lista_todas_as_tabelas(cliente):
    html = cliente.get("/tabelas").get_data(as_text=True)
    for item in CATALOGO:
        assert item["titulo"] in html


@pytest.mark.parametrize("identificador", [item["id"] for item in CATALOGO])
def test_cada_tabela_abre_e_cita_a_fonte(cliente, identificador):
    resposta = cliente.get(f"/tabelas/{identificador}")

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    tabela = construir(identificador, _DADOS)
    assert tabela.fonte in html
    assert tabela.linhas, "tabela sem linhas"


def test_identificador_inexistente_volta_ao_indice(cliente):
    resposta = cliente.get("/tabelas/nao-existe")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/tabelas")


def test_a_tabela_smp_tem_todas_as_linhas_transcritas():
    """28 linhas de índice SMP: se a tela mostrar menos, alguém filtrou o que não devia."""
    tabela = construir("calagem-smp", _DADOS)

    assert len(tabela.linhas) == len(_DADOS["calagem_smp"]["tabela"])


def test_a_dose_exibida_e_a_transcrita(cliente):
    """Amostra o arquivo e procura o valor na tela: a tela não pode reescrever a base."""
    html = cliente.get("/tabelas/calagem-smp").get_data(as_text=True)

    for linha in _DADOS["calagem_smp"]["tabela"][:5]:
        esperado = formatar_numero(linha["nc_ph_6_0"], 1)
        assert esperado in html, f"dose {esperado} não aparece na tela"


def test_criterios_nao_escondem_os_que_estao_fora_de_escopo(cliente):
    """Na tela de conferência, ao contrário do formulário, o arroz irrigado aparece: aqui
    o propósito é mostrar o que foi transcrito, e não oferecer o que se pode calcular."""
    html = cliente.get("/tabelas/criterios-calagem").get_data(as_text=True)

    assert "arroz irrigado" in html


def test_a_tabela_de_criterios_avisa_que_e_ela_quem_dispara(cliente):
    """É a confusão mais provável de quem lê o Manual pela primeira vez, e o CLAUDE.md
    registra que o pH de referência da Tabela 5.1 NÃO dispara a calagem."""
    html = cliente.get("/tabelas/criterios-calagem").get_data(as_text=True)

    assert "não o pH de referência da Tabela 5.1" in html


def test_a_tabela_rola_dentro_do_proprio_envelope(cliente):
    """Nove colunas em tela de 320px não podem fazer a página inteira rolar de lado
    (WCAG 1.4.10)."""
    html = cliente.get("/tabelas/interpretacao-p").get_data(as_text=True)

    assert re.search(r'class="painel tabela-envelope"', html)


def test_so_as_tabelas_de_prosa_quebram_linha(cliente):
    """Duas transcrições não são de valores, e por isso quebram linha.

    A folha de estilo impede quebra nas tabelas por um bom motivo: nas de classificação,
    partir um intervalo como "1,5 - 3,0" ao meio atrapalha mais que a rolagem. Mas os
    critérios de calagem trazem frases de condição em oito colunas, e o pH de referência
    lista 79 culturas numa célula — nessas duas a mesma regra produzia barra de rolagem
    horizontal e a tabela saindo da tela.

    O teste fixa os dois lados: quais quebram, e que as demais continuam sem quebrar."""
    de_prosa, de_valores = [], []
    for item in CATALOGO:
        html = cliente.get(f"/tabelas/{item['id']}").get_data(as_text=True)
        (de_prosa if "tabela-dados--texto" in html else de_valores).append(item["id"])

    assert sorted(de_prosa) == ["criterios-calagem", "ph-referencia"], de_prosa
    assert de_valores, "nenhuma tabela de valores restou"


def test_a_quebra_nao_parte_o_nome_da_linha():
    """`overflow-wrap: anywhere` corta no meio da palavra, e é isso que faz a célula de
    79 nomes caber. Na primeira coluna partiria "graos pd consolidado" em pedaços, e ela
    é o nome da linha — tem de continuar legível de relance."""
    css = (pathlib.Path(__file__).parents[2] / "siras" / "web" / "static" / "css"
           / "siras-telas.css").read_text(encoding="utf-8")

    assert re.search(r"\.tabela-dados--texto tbody th \{[^}]*overflow-wrap: normal", css)
    assert re.search(r"\.tabela-dados--texto th, \.tabela-dados--texto td \{"
                     r"[^}]*overflow-wrap: anywhere", css, re.S)


def test_o_menu_leva_as_tabelas_de_qualquer_tela(cliente):
    for rota in ("/", "/analise", "/analise/dados?cultura_id=soja", "/tabelas"):
        assert "Tabelas do Manual" in cliente.get(rota).get_data(as_text=True)
