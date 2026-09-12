"""
Defeitos de interface encontrados no uso real e corrigidos.

Cada teste aqui nasceu de algo que só apareceu abrindo a tela: contraste que some, pílula
sublinhada, leitura ao vivo incompleta, aptidão pela metade. São guardas de regressão —
existem para que o mesmo defeito não volte numa refatoração de CSS ou de template.
"""

import re
from pathlib import Path

import pytest

from siras.web import criar_app

_ESTATICOS = Path(__file__).parent.parent.parent / "siras" / "web" / "static"
_TELAS_CSS = (_ESTATICOS / "css" / "siras-telas.css").read_text(encoding="utf-8")

_ANALISE_COMPLETA = {
    "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
    "profundidade_incorporacao_cm": "20", "prnt": "100", "expectativa_rendimento": "3",
    "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
    "p": "11", "k": "96", "ctc_ph7": "9.4",
    "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
}


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


# --- contraste ----------------------------------------------------------------

def test_o_menu_suspenso_declara_esquema_de_cor_escuro():
    """O menu de um <select> é desenhado pelo sistema, não pelo CSS da página: sem
    color-scheme o Windows abre a lista com fundo claro e o texto herda a cor clara do
    tema — texto branco sobre branco, e a opção só aparece quando está selecionada."""
    assert re.search(r"\.campo__caixa select\s*\{[^}]*color-scheme:\s*dark", _TELAS_CSS)
    assert re.search(r"select option[^{]*\{[^}]*background:\s*var\(--n-800\)", _TELAS_CSS)


# --- pílula de cultura --------------------------------------------------------

def test_a_pilula_de_cultura_nao_sai_sublinhada():
    """Virou <a> na etapa 1 e herdou o sublinhado do link."""
    regra = re.search(r"\n\.cultura \{(.*?)\}", _TELAS_CSS, re.S).group(1)

    assert "text-decoration: none" in regra
    assert "inline-flex" in regra, "altura não se aplica a elemento inline"


def test_a_cultura_e_um_link_de_verdade(cliente):
    """Elemento nativo: navega com teclado e funciona sem JavaScript (WCAG 2.1.1)."""
    html = cliente.get("/analise").get_data(as_text=True)

    assert re.search(r'<a class="cultura" href="[^"]*cultura_id=soja"', html)


# --- marca --------------------------------------------------------------------

def test_a_barra_usa_a_logo_oficial_sem_repetir_o_nome(cliente):
    """A logo já traz 'SIRAS' desenhado; escrevê-lo de novo ao lado duplicava o nome."""
    html = cliente.get("/").get_data(as_text=True)

    assert "img/marca/siras-logo.png" in html
    assert 'class="logo__txt"' not in html


@pytest.mark.parametrize(
    "arquivo",
    ["img/favicon.svg", "img/marca/siras-logo.png",
     "img/marca/siras-icone-32.png", "img/marca/siras-icone-180.png"],
)
def test_os_arquivos_de_marca_sao_servidos(cliente, arquivo):
    assert cliente.get(f"/static/{arquivo}").status_code == 200


def test_a_pagina_declara_o_favicon(cliente):
    html = cliente.get("/").get_data(as_text=True)

    assert 'rel="icon"' in html
    assert 'rel="apple-touch-icon"' in html


def test_os_arquivos_de_marca_cabem_numa_tela(cliente):
    """Os originais somam 1,5 MB. Servi-los reduzidos por CSS custaria isso a cada
    carregamento e ainda renderizaria pior, porque o navegador reamostra a cada pintura."""
    total = sum(
        len(cliente.get(f"/static/img/marca/{nome}").data)
        for nome in ("siras-logo.png", "siras-icone-32.png", "siras-icone-180.png")
    )

    assert total < 120 * 1024, f"{total // 1024} KB de marca numa tela"


# --- leitura ao vivo ----------------------------------------------------------

def test_a_leitura_ao_vivo_mostra_todos_os_atributos_interpretaveis(cliente):
    """Mostrava quatro linhas e deixava de fora acidez, MO, Ca, Mg, CTC e V% — que o
    motor já sabia interpretar."""
    html = cliente.post("/api/interpretar", json=_ANALISE_COMPLETA).get_json()["html"]

    for atributo in ("Acidez", "Matéria orgânica", "Fósforo", "Potássio",
                     "Cálcio", "Magnésio", "CTC a pH 7,0",
                     "Saturação por alumínio", "Saturação por bases", "Calcário estimado"):
        assert atributo in html, f"'{atributo}' não aparece na leitura ao vivo"


def test_a_regua_so_aparece_onde_a_escala_tem_cinco_classes(cliente):
    """MO, Ca, Mg e CTC têm escalas próprias de três ou quatro classes: esticar a régua
    de cinco estratos sobre elas afirmaria uma leitura que o Manual não faz."""
    html = cliente.post("/api/interpretar", json=_ANALISE_COMPLETA).get_json()["html"]

    assert html.count('class="regua"') == 2, "régua deveria existir só para P e K"


def test_a_leitura_ao_vivo_cresce_conforme_o_preenchimento(cliente):
    parcial = cliente.post("/api/interpretar",
                           json={"cultura_id": "soja", "argila": "38", "p": "11"})
    completa = cliente.post("/api/interpretar", json=_ANALISE_COMPLETA)

    assert parcial.get_json()["html"].count('class="linha') < \
        completa.get_json()["html"].count('class="linha')


# --- laudo: os dois cenários --------------------------------------------------

def test_o_laudo_mostra_as_duas_aptidoes_lado_a_lado(cliente):
    """O CCAE §7 põe a comparação como a informação: mostrar só a atual, com a potencial
    em prosa, perdia o ganho atribuível à recomendação."""
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    assert "Hoje" in html
    assert "Após a correção" in html
    assert html.count('class="aptidao__selo"') == 2
    assert "Fatores de limitação, na situação atual" in html


def test_o_laudo_separa_os_fatores_que_permanecem(cliente):
    """O que a calagem e a adubação não corrigem é a informação de manejo mais útil do
    laudo — e é o que o cenário POTENCIAL isola."""
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    assert "O que permanece depois da correção" in html
