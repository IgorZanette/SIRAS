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

def test_a_assinatura_e_montada_e_nao_uma_imagem_unica(cliente):
    """Símbolo vetorial + nome em Sora. Como imagem única, o nome ficava achatado na
    altura da barra e obrigava a escolher um tamanho de arquivo."""
    html = cliente.get("/").get_data(as_text=True)

    assert "img/marca/siras-simbolo.svg" in html
    assert 'class="logo__nome"' in html
    assert "siras-logo.png" not in html, "voltou a usar a logo achatada em PNG"


@pytest.mark.parametrize(
    "arquivo",
    ["img/favicon.svg", "img/marca/siras-simbolo.svg", "img/marca/siras-icone-180.png"],
)
def test_os_arquivos_de_marca_sao_servidos(cliente, arquivo):
    assert cliente.get(f"/static/{arquivo}").status_code == 200


def test_a_pagina_declara_o_favicon(cliente):
    html = cliente.get("/").get_data(as_text=True)

    assert 'rel="icon"' in html
    assert 'rel="apple-touch-icon"' in html


def test_a_marca_de_tela_e_vetorial_e_leve(cliente):
    """O que a tela carrega em toda página é só o símbolo em SVG: uma forma que serve de
    16 px a 512 px, sem reamostragem e sem escolher tamanho."""
    simbolo = cliente.get("/static/img/marca/siras-simbolo.svg")
    favicon = cliente.get("/static/img/favicon.svg")

    assert b"<svg" in simbolo.data and b"<svg" in favicon.data
    assert len(simbolo.data) + len(favicon.data) < 12 * 1024


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


# --- variáveis condicionais ---------------------------------------------------

def test_massa_verde_da_erva_mate_e_campo_numerico_unico(cliente):
    """Defeito encontrado no uso: a massa verde saía como lista de escolha SEM nenhuma
    opção — obrigatória e impossível de preencher — e ainda duplicada ao lado.

    A causa estava em ignorar a base: erva_mate_adubacao.json declara a variável com
    `"tipo": "numero"`, e o código forçava escolha em tudo que fosse declarado."""
    html = cliente.get("/analise/dados?cultura_id=erva-mate").get_data(as_text=True)

    assert html.count('name="massa_verde_t_ha"') == 1, "campo duplicado"
    assert re.search(r'<input[^>]*id="massa_verde_t_ha"', html), "deveria ser campo numérico"
    assert not re.search(r'<select[^>]*id="massa_verde_t_ha"', html)


def test_a_ajuda_da_variavel_vem_da_propria_base(cliente):
    """A base descreve a variável em `descricao`. Essa frase é transcrição e é melhor
    ajuda do que qualquer texto que a interface inventasse."""
    html = cliente.get("/analise/dados?cultura_id=erva-mate").get_data(as_text=True)

    assert "massa verde de erva-mate comercial produzida" in html


@pytest.mark.parametrize(
    "cultura, campo",
    [
        ("erva-mate", "programa"), ("erva-mate", "manejo_galho_grosso"),
        ("videira", "fase"), ("videira", "tipo_uva"),
        ("cana_de_acucar", "ciclo"), ("tabaco", "tipo"),
    ],
)
def test_todo_campo_fora_do_laudo_de_laboratorio_tem_ajuda(cliente, cultura, campo):
    """Nada disso está no laudo do laboratório: sem uma frase dizendo de onde o valor
    vem, o técnico precisa adivinhar o que informar."""
    html = cliente.get(f"/analise/dados?cultura_id={cultura}").get_data(as_text=True)

    assert re.search(rf'id="{campo}-ajuda"', html), f"'{campo}' sem texto de ajuda"


def test_os_valores_de_escolha_sao_legiveis(cliente):
    """'manejo_1_retido' é identificador de base, não texto de tela."""
    html = cliente.get("/analise/dados?cultura_id=erva-mate").get_data(as_text=True)

    assert "galho grosso retido" in html
    assert "manejo_1_retido<" not in html


# --- tela de cálculo ----------------------------------------------------------

def test_a_tela_de_calculo_existe_e_comeca_oculta(cliente):
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert re.search(r'id="calculando"[^>]*hidden', html)
    assert 'aria-live="polite"' in html


def test_a_tela_de_calculo_lista_os_modulos_reais_do_motor(cliente):
    """A sequência não é enfeite: são os módulos que gerar_laudo() percorre, na ordem em
    que os chama. Quem espera aprende o que o sistema faz."""
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert html.count("data-passo") == 5
    for passo in ("Lendo a análise de solo", "Calculando a calagem",
                  "Classificando fósforo e potássio", "Avaliando a aptidão edáfica",
                  "Montando a trilha"):
        assert passo in html


def test_a_tela_de_calculo_nao_e_impressa(cliente):
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert re.search(r'class="calculando nao-imprime"', html)


def test_a_animacao_para_com_prefers_reduced_motion():
    """Animação em laço é a que causa desconforto vestibular. A informação continua
    inteira; só para de se mexer."""
    assert re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{[^}]*\.calculando[^}]*animation: none",
        _TELAS_CSS, re.S,
    )
