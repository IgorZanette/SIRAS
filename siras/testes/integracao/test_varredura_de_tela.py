"""
Achados da varredura de 03/11/2026, que percorreu todas as telas, as 61 culturas e os
exemplos procurando texto cru, palavra sem acento e conteúdo que estoura a tela do
telefone.

Cada teste guarda um defeito que já esteve na tela. Nenhum deles toca o motor ou a base:
o que mudou foi o que a tela diz sobre o que o motor decidiu.
"""

import re
import sys
from pathlib import Path

import pytest

from siras.web import criar_app

sys.path.insert(0, str(Path(__file__).parent))
from test_bancada_culturas import _campos_da_tela  # noqa: E402

_CSS = (
    Path(__file__).parent.parent.parent / "siras" / "web" / "static" / "css" / "siras-telas.css"
).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cliente():
    return criar_app({"TESTING": True}).test_client()


def _laudo_do_exemplo(cliente, cultura: str) -> str:
    tela = cliente.get(f"/analise/dados?cultura_id={cultura}&exemplo=1").get_data(as_text=True)
    campos = _campos_da_tela(tela)
    campos["cultura_id"] = cultura
    resposta = cliente.post("/analise/laudo", data=campos)
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


@pytest.mark.parametrize("rota", ["/", "/analise", "/tabelas", "/tabelas/interpretacao-p",
                                  "/analise/dados?cultura_id=soja&exemplo=1"])
def test_a_etiqueta_em_desenvolvimento_esta_no_cabecalho_de_toda_tela(cliente, rota):
    html = cliente.get(rota).get_data(as_text=True)
    cabecalho = html[html.index('class="barra'):html.index("</header>")]

    assert '<span class="selo-dev">Em desenvolvimento</span>' in cabecalho


def test_a_etiqueta_some_na_impressao():
    assert re.search(r"@media print \{ \.selo-dev \{ display: none !important; \} \}", _CSS)


def test_o_botao_de_ajuda_nao_anuncia_o_identificador_do_campo(cliente):
    """O leitor de tela dizia "Por que preencher expectativa_rendimento"."""
    html = cliente.get("/analise/dados?cultura_id=soja&exemplo=1").get_data(as_text=True)
    rotulos = re.findall(r'aria-label="Por que preencher[^"]*"', html)

    assert rotulos
    for rotulo in rotulos:
        assert "_" not in rotulo, rotulo


def test_aptidao_indeterminada_nao_mostra_mensagem_interna(cliente):
    """A aveia branca não resolve o pH de referência (ADR 0005, D5.7): a aptidão sai
    INDETERMINADA. A tela dizia "cultura 'aveia_branca' não encontrada em
    ph_referencia.json" e, logo acima, que "o que limita a área não se corrige"."""
    html = _laudo_do_exemplo(cliente, "aveia_branca")

    assert "ph_referencia.json" not in html
    assert "não encontrada em" not in html
    assert "o que limita a área não se corrige" not in html
    assert "A aptidão não pôde ser classificada" in html
    assert "Tabela 5.1" in html
    # Sem a classe de argila (vem dos derivados da aptidão), a nota não exibe "—".
    assert "classe de argila —" not in html


def test_a_trilha_nao_mostra_o_id_do_criterio(cliente):
    html = _laudo_do_exemplo(cliente, "soja")
    trilha = html[html.index("De onde vem cada número"):]

    assert not re.search(r'class="trilha__ref">graos_', trilha)
    assert "Critério grãos" in trilha


def test_tabelas_saem_com_cabecalho_e_atributo_acentuados(cliente):
    p = cliente.get("/tabelas/interpretacao-p").get_data(as_text=True)
    geral = cliente.get("/tabelas/interpretacao-geral").get_data(as_text=True)

    assert '<th scope="col">Médio</th>' in p
    assert "Adubacao" not in p
    assert "Ctc ph7" not in geral and "CTC a pH 7,0" in geral
    assert "Matéria orgânica" in geral
    assert "cmolc/dm³" in geral and "cmolc/dm3" not in geral


def test_a_nota_do_anexo_2_nao_traz_instrucao_de_manutencao(cliente):
    html = cliente.get("/tabelas/grupos-de-exigencia").get_data(as_text=True)

    assert "Não acrescente esses campos" not in html
    assert "O Anexo 2 dá somente os grupos de exigência" in html


@pytest.mark.parametrize("rota", ["/tabelas", "/tabelas/interpretacao-p"])
def test_tabelas_mantem_a_margem_lateral(cliente, rota):
    """`padding: X 0 Y` no <main class="env"> zerava a margem: no telefone o título
    encostava na borda da tela."""
    html = cliente.get(rota).get_data(as_text=True)
    main = re.search(r'<main class="env"[^>]*>', html).group(0)

    assert not re.search(r"padding:\s*[^;\"]+\s0\s", main)


def test_grades_da_calculadora_encolhem_no_telefone():
    """Trilha `1fr` não encolhe abaixo do conteúdo mínimo: a calculadora de custo e os
    totais estouravam 90px a tela de 360px."""
    assert re.search(r"\.custo, \.custo__saida, \.custo__entradas, \.formula \{ "
                     r"grid-template-columns: minmax\(0, 1fr\); \}", _CSS)
    assert "repeat(2, minmax(0, 1fr))" in _CSS
