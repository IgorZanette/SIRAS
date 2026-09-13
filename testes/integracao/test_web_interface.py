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


# --- exemplo por cultura ------------------------------------------------------

def test_o_exemplo_preenche_a_analise_inteira(cliente):
    """Transcrever dezessete campos antes de ver qualquer resultado é barreira alta para
    quem só quer conhecer o sistema, e no roteiro do SUS consome o tempo da tarefa sem
    medir nada."""
    html = cliente.get("/analise/dados?cultura_id=soja&exemplo=1").get_data(as_text=True)

    for campo in ("ph_agua", "indice_smp", "argila", "mo", "p", "k", "ctc_ph7",
                  "al", "ca", "mg", "v_percent", "prnt"):
        assert re.search(rf'id="{campo}"[^>]*value="[^"]+"', html), f"{campo} vazio no exemplo"


def test_a_produtividade_do_exemplo_vem_da_base(cliente):
    """Inventar uma produtividade típica por cultura seria afirmação agronômica. A soja
    usa o rendimento de referência que graos_adubacao_pk.json transcreve."""
    from siras.conhecimento.carregador import carregar_dados_graos

    esperado = (carregar_dados_graos()["adubacao_pk"]["manutencao_por_cultura"]
                ["culturas"]["soja"]["rendimento_referencia_t_ha"])
    html = cliente.get("/analise/dados?cultura_id=soja&exemplo=1").get_data(as_text=True)

    valor = re.search(r'id="expectativa_rendimento"[^>]*value="([^"]*)"', html).group(1)
    assert valor.replace(",", ".") == f"{float(esperado):g}"


def test_sem_exemplo_o_formulario_abre_vazio(cliente):
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert not re.search(r'id="ph_agua"[^>]*value="[^"]+"', html)


# --- modo claro ---------------------------------------------------------------

def test_existe_alternador_de_tema(cliente):
    """§14 do plano: tema escuro é ruim sob sol direto, e parte do público usa tablet em
    campo."""
    html = cliente.get("/").get_data(as_text=True)

    assert 'id="alternar-tema"' in html
    assert 'aria-pressed' in html


def test_o_tema_salvo_e_aplicado_antes_da_primeira_pintura(cliente):
    """Num script no fim da página, quem escolheu o modo claro veria a tela escura piscar
    antes de clarear."""
    html = cliente.get("/").get_data(as_text=True)
    cabeca = html[: html.index("</head>")]

    assert "siras-tema" in cabeca


def test_o_modo_claro_redefine_a_escala_de_neutros():
    assert re.search(r':root\[data-tema="claro"\]\s*\{[^}]*--n-900:\s*#F4F8F5', _TELAS_CSS)
    assert re.search(r':root\[data-tema="claro"\]\s*\{[^}]*--n-100:\s*#0D1410', _TELAS_CSS)


def test_o_verde_e_os_sinais_nao_mudam_com_o_tema():
    """São o vocabulário do sistema: a escala divergente da §2.2 significa o mesmo nos
    dois modos, e trocá-la por modo desfaria o que ela construiu."""
    bloco = re.search(r':root\[data-tema="claro"\]\s*\{(.*?)\}', _TELAS_CSS, re.S).group(1)

    for token in ("--v-400", "--sig-coral", "--sig-ambar", "--sig-aqua", "--d-a"):
        assert token not in bloco, f"{token} foi redefinido no modo claro"


# --- como aplicar -------------------------------------------------------------

def test_o_laudo_diz_como_aplicar(cliente):
    """Depois de "quanto", a pergunta seguinte do técnico é "como" — e o parcelamento já
    estava transcrito na base sem aparecer no laudo."""
    dados_do_formulario = dict(_ANALISE_COMPLETA,
                               cultura_id="tomate", criterio_id="olericolas_convencional")

    html = cliente.post("/analise/laudo", data=dados_do_formulario).get_data(as_text=True)

    assert "Como aplicar" in html
    assert "Parcelamento" in html
    assert "Integralmente no plantio" in html


def test_a_fonte_acompanha_a_regra_sem_competir_com_ela(cliente):
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    assert 'class="trilha__fonte"' in html
    assert re.search(r"\.trilha__fonte\s*\{[^}]*font-size:\s*var\(--fs-3xs\)", _TELAS_CSS)


# --- trilha enxuta ------------------------------------------------------------

def test_a_trilha_nao_repete_a_mesma_fonte(cliente):
    """A aptidão roda duas vezes, uma por cenário, e a calagem é recalculada dentro do
    POTENCIAL para testar a exequibilidade. Os passos repetidos citam a MESMA fonte:
    listá-los duas vezes não acrescenta rastreabilidade e consumia duas páginas do laudo
    impresso."""
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    trilha = html[html.index("De onde vem cada número"):]
    assert trilha.count("F1_acidez") == 0, "identificador cru na tela"
    assert trilha.count("composicao_aptidao") == 0, "identificador cru na tela"
    assert "Composição da classe" in trilha
    # Os sete fatores aparecem uma vez cada, e não duas.
    assert trilha.count('class="trilha__item"') == 12


def test_a_repeticao_continua_registrada(cliente):
    """Deduplicar não pode virar apagar: a regra foi mesmo aplicada duas vezes."""
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    assert 'class="trilha__vezes"' in html
    assert "2×" in html


def test_a_etiqueta_da_trilha_nao_invade_a_coluna_do_texto():
    """128px não cabiam 'graos_convencional', e inline-flex sem min-width não encolhe: a
    etiqueta se sobrepunha ao texto no PDF."""
    regra = re.search(r"\.trilha__ref \{(.*?)\}", _TELAS_CSS, re.S).group(1)

    assert "min-width: 0" in regra
    assert "overflow-wrap: anywhere" in regra


# --- contraste no modo claro --------------------------------------------------

def test_a_assinatura_nao_some_no_modo_claro():
    """O nome usa degradê do branco ao verde: sobre fundo claro ficava invisível."""
    assert re.search(
        r':root\[data-tema="claro"\] \.logo__nome \{[^}]*#0D1410', _TELAS_CSS
    )


def test_o_verde_vivo_nao_e_texto_sobre_claro():
    """§2.3 do plano: --v-400 sobre branco fica em torno de 2,2:1 e reprova no contraste
    mínimo. Onde era texto no modo escuro, o modo claro usa --v-700."""
    assert re.search(
        r':root\[data-tema="claro"\][^{]*\.hero h1 em[^{]*\{[^}]*var\(--v-700\)',
        _TELAS_CSS, re.S,
    )


def test_a_regua_ganha_opacidade_no_modo_claro():
    """A régua vive de opacidade: .3 sobre escuro é discreto, sobre branco é invisível."""
    assert re.search(
        r':root\[data-tema="claro"\] \.regua__faixa \{[^}]*opacity:\s*\.42', _TELAS_CSS
    )


# --- impressão ----------------------------------------------------------------

def test_os_dois_cenarios_ficam_lado_a_lado_no_papel():
    """A largura útil de uma A4 retrato cai dentro da consulta de 720px, então a regra de
    tela estreita entrava no papel e virava a seta de lado, com o texto na vertical."""
    bloco = _TELAS_CSS[_TELAS_CSS.rindex("@media print"):]

    assert re.search(r"\.cenarios \{[^}]*grid-template-columns: 1fr auto 1fr", bloco)
    assert re.search(r"\.cenarios__seta \{[^}]*transform: none", bloco)
