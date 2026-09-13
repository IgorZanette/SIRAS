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

def test_a_assinatura_usa_a_marca_oficial_montada(cliente):
    """Ícone e palavra recortados do lockup oficial e montados em HTML, e não servidos
    como uma imagem só: montados, a palavra troca de cor com o tema e a assinatura some
    sozinha em tela estreita, sem um segundo arquivo."""
    html = cliente.get("/").get_data(as_text=True)

    assert "img/marca/siras-icone-64.png" in html
    assert "img/marca/siras-texto.png" in html
    assert "img/marca/siras-texto-escuro.png" in html


def test_a_palavra_da_marca_troca_com_o_tema():
    """O original é branco e sumiria no modo claro; a versão escura troca só os pixels
    brancos e preserva a folha verde do "A"."""
    assert re.search(r"\.logo__nome--claro \{[^}]*display: none", _TELAS_CSS)
    assert re.search(
        r':root\[data-tema="claro"\] \.logo__nome--escuro \{[^}]*display: none', _TELAS_CSS
    )


@pytest.mark.parametrize(
    "arquivo",
    ["img/marca/siras-icone-32.png", "img/marca/siras-icone-64.png",
     "img/marca/siras-icone-180.png", "img/marca/siras-icone-256.png",
     "img/marca/siras-texto.png", "img/marca/siras-texto-escuro.png"],
)
def test_os_arquivos_de_marca_sao_servidos(cliente, arquivo):
    assert cliente.get(f"/static/{arquivo}").status_code == 200


def test_a_pagina_declara_o_favicon_em_dois_tamanhos(cliente):
    """O navegador escolhe o mais próximo do que precisa: servir só o de 256 px faria o
    Chrome reamostrar para 16 px a cada pintura da aba."""
    html = cliente.get("/").get_data(as_text=True)

    assert 'sizes="32x32"' in html
    assert 'sizes="64x64"' in html
    assert 'rel="apple-touch-icon"' in html


def test_a_marca_carregada_em_toda_pagina_e_leve(cliente):
    """O lockup original tem 2172 px de largura e 355 KB. O que a barra carrega é o
    ícone de 64 px mais a palavra — servir o original reduzido por CSS custaria isso a
    cada carregamento e renderizaria pior."""
    total = sum(
        len(cliente.get(f"/static/img/marca/{nome}").data)
        for nome in ("siras-icone-64.png", "siras-texto.png")
    )

    assert total < 60 * 1024, f"{total // 1024} KB de marca na barra"


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


def test_o_modo_claro_nao_usa_branco_puro_de_fundo():
    """#FFFFFF puro lê como tela de formulário. O off-white carrega a mesma matiz
    levemente verde dos neutros escuros e lê como papel."""
    assert re.search(r':root\[data-tema="claro"\]\s*\{[^}]*--n-900:\s*#F6F8F5', _TELAS_CSS)
    assert re.search(r':root\[data-tema="claro"\]\s*\{[^}]*--n-100:\s*#0D1410', _TELAS_CSS)


def test_a_malha_de_fundo_sobrevive_no_modo_claro():
    """A malha é o que dá ao SIRAS a leitura de superfície de instrumento: sumir no modo
    claro trocaria a identidade por conveniência."""
    assert re.search(
        r':root\[data-tema="claro"\] \.malha \{[^}]*rgba\(13,20,16,\.045\)', _TELAS_CSS
    )


def test_os_paineis_ganham_profundidade_por_sombra_no_modo_claro():
    """Borda fina sobre branco desenha uma caixa; a sombra suave dá profundidade sem
    pesar."""
    assert re.search(
        r':root\[data-tema="claro"\] \.painel \{[^}]*box-shadow:', _TELAS_CSS, re.S
    )


def test_os_sinais_sao_recalibrados_e_nao_trocados_no_modo_claro():
    """Coral, laranja, âmbar e aqua foram desenhados para brilhar sobre preto; sobre
    claro ficam entre 1,4:1 e 2,6:1 e viram pastel. As variantes do modo claro mantêm
    MATIZ e SATURAÇÃO e baixam só a luminosidade — o significado de cada sinal na escala
    divergente da §2.2 continua o mesmo."""
    import colorsys

    bloco = re.search(r':root\[data-tema="claro"\]\s*\{(.*?)\n\}', _TELAS_CSS, re.S).group(1)

    def matiz(cor):
        cor = cor.lstrip("#")
        r, g, b = (int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return colorsys.rgb_to_hls(r, g, b)[0]

    originais = {"--sig-coral": "#FF6B4A", "--sig-laranja": "#FF9F3D",
                 "--sig-ambar": "#FFC93D", "--sig-aqua": "#2BE0C8"}
    for token, original in originais.items():
        claro = re.search(rf"{token}:\s*(#[0-9A-Fa-f]{{6}})", bloco).group(1)
        assert abs(matiz(claro) - matiz(original)) < 0.04, f"{token} mudou de matiz"

    # O mapeamento classe -> sinal e o verde de ação continuam intactos.
    for token in ("--d-a", "--d-mb", "--v-400"):
        assert token not in bloco, f"{token} foi redefinido no modo claro"


def test_os_sinais_do_modo_claro_passam_no_piso_de_componente():
    """3:1 sobre o fundo, que é o piso do WCAG para componentes gráficos."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from conferir_contraste import contraste

    bloco = re.search(r':root\[data-tema="claro"\]\s*\{(.*?)\n\}', _TELAS_CSS, re.S).group(1)
    fundo = re.search(r"--n-900:\s*(#[0-9A-Fa-f]{6})", bloco).group(1)

    for token in ("--sig-coral", "--sig-laranja", "--sig-ambar", "--sig-aqua"):
        cor = re.search(rf"{token}:\s*(#[0-9A-Fa-f]{{6}})", bloco).group(1)
        assert contraste(cor, fundo) >= 3.0, f"{token} em {contraste(cor, fundo):.2f}:1"


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
        r':root\[data-tema="claro"\] \.regua__faixa \{[^}]*opacity:\s*\.55', _TELAS_CSS
    )


# --- impressão ----------------------------------------------------------------

def test_os_dois_cenarios_ficam_lado_a_lado_no_papel():
    """A largura útil de uma A4 retrato cai dentro da consulta de 720px, então a regra de
    tela estreita entrava no papel e virava a seta de lado, com o texto na vertical."""
    # O arquivo tem mais de um bloco @media print; a busca é no arquivo inteiro.
    assert re.search(r"\.cenarios \{[^}]*grid-template-columns: 1fr auto 1fr", _TELAS_CSS)
    assert re.search(r"\.cenarios__seta \{[^}]*transform: none", _TELAS_CSS)


# --- usabilidade --------------------------------------------------------------

def test_os_campos_declaram_a_faixa_que_o_dominio_valida(cliente):
    """As faixas não são escolha da interface: são as que AnaliseSolo e Contexto já
    recusam na construção. Declará-las no HTML adianta o erro para o momento da
    digitação, e a validação do servidor continua sendo a que vale."""
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    esperado = {"ph_agua": ("0", "14"), "indice_smp": ("3", "8"),
                "v_percent": ("0", "100"), "prnt": ("0", "100")}
    for campo, (minimo, maximo) in esperado.items():
        tag = re.search(rf'<input[^>]*id="{campo}"[^>]*>', html).group(0)
        assert f'min="{minimo}"' in tag, f"{campo} sem min"
        assert f'max="{maximo}"' in tag, f"{campo} sem max"


def test_as_faixas_do_html_sao_as_do_dominio():
    """Guarda contra a interface e o domínio divergirem: se AnaliseSolo mudar uma faixa,
    o HTML passa a mentir sobre o que é aceito."""
    from siras.dominio.analise import AnaliseSolo
    from siras.web.formulario import FAIXA_DO_CAMPO

    base = dict(ph_agua=6.0, indice_smp=6.0, argila=30, mo=3, p=10, k=80,
                ctc_ph7=9, al=1, ca=2, mg=1, v_percent=50)
    for campo, (minimo, maximo) in FAIXA_DO_CAMPO.items():
        if campo not in base or maximo is None:
            continue
        for fora in (minimo - 1, maximo + 1):
            with pytest.raises(ValueError):
                AnaliseSolo(**{**base, campo: fora})


def test_o_valor_digitado_nao_se_confunde_com_o_marcador(cliente):
    """Valor e placeholder tinham a mesma cara: não dava para saber se o campo estava
    preenchido sem clicar nele."""
    html = cliente.get("/analise/dados?cultura_id=soja&exemplo=1").get_data(as_text=True)

    assert "campo--preenchido" in html
    assert re.search(r"\.campo__caixa input \{[^}]*font-weight: 600", _TELAS_CSS)
    assert re.search(r"::placeholder \{[^}]*font-weight: 400", _TELAS_CSS)


def test_a_leitura_ao_vivo_mostra_um_exemplo_antes_de_digitar(cliente):
    """Vazio é convite, não lamento — e mostrar COMO a leitura vai aparecer convida mais
    do que descrevê-la. O exemplo é esmaecido, sem interação e aria-hidden: ninguém o
    confunde com uma interpretação da análise."""
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert 'class="vazio__exemplo"' in html
    assert "Exemplo de como aparece" in html
    assert re.search(r'class="vazio__exemplo" aria-hidden="true"', html)


@pytest.mark.parametrize("rota, passo", [("/analise", 1), ("/analise/dados?cultura_id=soja", 2)])
def test_o_fluxo_mostra_quanto_falta(cliente, rota, passo):
    """Os três passos nomeados dizem ONDE se está; a barra diz QUANTO falta."""
    html = cliente.get(rota).get_data(as_text=True)

    assert f'aria-valuenow="{passo}"' in html
    assert 'role="progressbar"' in html


def test_a_regua_diz_a_faixa_numerica_de_cada_classe(cliente):
    """A régua desenha a posição mas não escreve o número da borda: quem precisa do
    valor exato descobre passando o mouse, sem poluir o componente."""
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    titulos = re.findall(r'class="regua__faixa[^"]*"\s*title="([^"]*)"', html)
    assert len(titulos) >= 5
    assert any("Muito baixo: até" in titulo for titulo in titulos)
    # Vírgula decimal, e não ponto: é número para brasileiro ler.
    assert not any(re.search(r"\d\.\d", titulo) for titulo in titulos)


def test_o_formulario_vira_uma_coluna_em_tela_estreita():
    """O público usa tablet e telefone em campo: duas colunas de 170px com rótulo,
    unidade e ajuda não cabem em 375px sem o texto quebrar em cada palavra."""
    assert re.search(
        r"@media \(max-width: 560px\) \{[^@]*\.grade \{ grid-template-columns: 1fr",
        _TELAS_CSS, re.S,
    )


def test_o_clique_tem_resposta_propria():
    """O hover diz 'dá para clicar'; o active diz 'clicou'."""
    assert re.search(r"\.btn:active \{[^}]*transform:", _TELAS_CSS)


# --- exemplos por cenario -----------------------------------------------------

def test_ha_tres_cenarios_de_exemplo(cliente):
    """Um exemplo só nunca exercita o laudo SEM calagem, que é metade do que o sistema
    faz. Os três percorrem caminhos diferentes do motor."""
    from siras.web.exemplo import CENARIOS

    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert len(CENARIOS) == 3
    for cenario in CENARIOS:
        assert cenario["nome"] in html
        assert f"exemplo={cenario['id']}" in html


@pytest.mark.parametrize("cenario", ["argiloso", "arenoso", "corrigido"])
def test_cada_cenario_preenche_valores_proprios(cliente, cenario):
    html = cliente.get(f"/analise/dados?cultura_id=soja&exemplo={cenario}").get_data(as_text=True)

    argila = re.search(r'id="argila"[^>]*value="([^"]*)"', html).group(1)
    assert argila, f"{cenario} não preencheu a argila"


def test_os_cenarios_percorrem_caminhos_diferentes(cliente):
    """O solo corrigido tem pH acima do gatilho: o laudo dele sai SEM calagem indicada,
    e o argiloso ácido sai com dose."""
    def nc(cenario):
        campos = dict(re.findall(
            r'<input[^>]*id="(\w+)"[^>]*value="([^"]*)"',
            cliente.get(f"/analise/dados?cultura_id=soja&exemplo={cenario}").get_data(as_text=True),
        ))
        campos.update({"cultura_id": "soja", "criterio_id": "graos_convencional"})
        html = cliente.post("/analise/laudo", data=campos).get_data(as_text=True)
        return "Calagem não indicada" in html

    assert nc("corrigido") is True, "o cenário corrigido deveria dispensar a calagem"
    assert nc("argiloso") is False, "o cenário argiloso ácido deveria pedir calcário"


# --- identificação do documento -----------------------------------------------

def test_o_laudo_traz_data_e_espaco_de_assinatura(cliente):
    """O SIRAS é apoio à decisão: a recomendação oficial é do profissional habilitado, e
    o documento precisa carregar de quem ela é."""
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    assert "Emitido em" in html
    assert 'class="assinatura__linha"' in html
    assert "Assinatura e carimbo" in html


def test_o_responsavel_informado_sai_impresso(cliente):
    """Quem se identifica recebe o laudo pronto para assinar e carimbar."""
    dados = dict(_ANALISE_COMPLETA,
                 responsavel_nome="Igor Zanette",
                 responsavel_registro="CREA-RS 123456",
                 responsavel_documento="000.000.000-00",
                 propriedade="Fazenda Santa Rita")

    html = cliente.post("/analise/laudo", data=dados).get_data(as_text=True)

    assert "Igor Zanette" in html
    assert "CREA-RS 123456" in html
    assert "Fazenda Santa Rita" in html


def test_sem_responsavel_a_linha_de_assinatura_continua(cliente):
    """Quem só quer ver a recomendação na tela não precisa se identificar — e o laudo
    continua assinável à mão."""
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    assert "Responsável técnico" in html
    assert 'class="assinatura__linha"' in html


def test_a_identificacao_nao_entra_no_motor():
    """Nome e CPF são metadado do documento, não entrada de cálculo: gerar_laudo()
    continua sendo função pura de análise, cultura e contexto."""
    import inspect

    from siras.motor.laudo import gerar_laudo

    parametros = set(inspect.signature(gerar_laudo).parameters)
    assert not parametros & {"responsavel", "responsavel_nome", "emitido_em"}


# --- apresentação de primeira visita -------------------------------------------

def test_a_apresentacao_nasce_oculta(cliente):
    """Sem JavaScript a página simplesmente não a mostra — em vez de mostrá-la sem meio
    de fechar, que seria pior que não ter guia nenhum."""
    html = cliente.get("/").get_data(as_text=True)

    assert re.search(r'id="guia"[^>]*hidden', html)
    assert html.count("data-guia-passo") == 3
    assert "data-guia-fechar" in html


def test_a_apresentacao_reaparece_a_cada_ciclo_de_visitas():
    """O público do SIRAS não é de uso diário: quem abre o sistema em duas safras
    diferentes volta sem lembrar que a cultura precede a análise, e uma guia que nunca
    mais aparece deixa de ajudar exatamente quem mais precisa."""
    codigo = (_ESTATICOS / "js" / "guia.js").read_text(encoding="utf-8")

    assert re.search(r"var CICLO = \d+", codigo)
    assert "(entrada - 1) % CICLO === 0" in codigo
    assert "Escape" in codigo, "deveria fechar com Esc"


def test_uma_entrada_e_uma_sessao_e_nao_um_carregamento():
    """Recarregar a página cinco vezes seguidas não pode fazer a guia voltar: isso seria
    contar impaciência como visita."""
    codigo = (_ESTATICOS / "js" / "guia.js").read_text(encoding="utf-8")

    assert "sessionStorage" in codigo
    assert "siras-guia-visitas" in codigo


def test_pular_significa_agora_nao_e_nao_nunca_mais():
    """Numa guia periódica, fechar não pode marcar 'visto para sempre' — quem decide a
    próxima aparição é o contador, que já avançou ao abrir a página."""
    codigo = (_ESTATICOS / "js" / "guia.js").read_text(encoding="utf-8")

    corpo_do_fechar = re.search(r"function fechar\(\) \{(.*?)\n  \}", codigo, re.S).group(1)
    assert "setItem" not in corpo_do_fechar


# --- microinterações -----------------------------------------------------------

def test_o_alternador_de_tema_usa_sol_e_lua(cliente):
    html = cliente.get("/").get_data(as_text=True)

    assert "#i-sol" in html and "#i-lua" in html
    assert re.search(r"\.tema__claro \{[^}]*transform: rotate", _TELAS_CSS)


def test_a_tela_de_calculo_confirma_antes_de_navegar(cliente):
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert 'class="calculando__pronto"' in html
    assert "Laudo pronto" in html


def test_cada_tela_entra_com_transicao():
    assert re.search(r"main \{ animation: entrar-tela", _TELAS_CSS)
    assert re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{[^}]*main[^}]*animation: none",
        _TELAS_CSS, re.S,
    )


# --- volta do laudo para o formulário ------------------------------------------

def test_editar_a_analise_devolve_o_formulario_preenchido(cliente):
    """Gerar o laudo e perceber que o fósforo foi digitado errado não pode custar a
    redigitação dos outros vinte campos. O botão reenvia o que produziu aquele laudo, e
    a tela volta como estava."""
    laudo = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)
    ocultos = dict(re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">', laudo))

    assert set(_ANALISE_COMPLETA) <= set(ocultos), "o laudo não leva de volta tudo o que recebeu"

    volta = cliente.post("/analise/dados", data=ocultos)
    assert volta.status_code == 200

    html = volta.get_data(as_text=True)
    for campo, valor in _ANALISE_COMPLETA.items():
        if campo in ("cultura_id", "criterio_id", "cultivo", "profundidade_incorporacao_cm"):
            continue  # escolhas: voltam como <option selected>, não como value=
        assert re.search(rf'id="{campo}"[^>]*value="{valor}"', html), (
            f"{campo} não voltou preenchido"
        )


def test_a_volta_traz_o_responsavel_junto(cliente):
    """Quem assina o laudo costuma ser o mesmo em todas as análises do dia: perder o
    nome e o registro a cada correção anula a razão de o campo existir."""
    dados = dict(_ANALISE_COMPLETA, responsavel_nome="Igor Zanette", responsavel_registro="CREA-RS 12345")
    laudo = cliente.post("/analise/laudo", data=dados).get_data(as_text=True)
    ocultos = dict(re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">', laudo))

    html = cliente.post("/analise/dados", data=ocultos).get_data(as_text=True)

    assert 'value="Igor Zanette"' in html
    assert 'value="CREA-RS 12345"' in html


def test_a_volta_e_um_envio_e_nao_um_link(cliente):
    """Um <a href> não carrega valores. O controle precisa ser um formulário, ou o
    caminho de volta esvazia a tela — que era o defeito."""
    html = cliente.post("/analise/laudo", data=_ANALISE_COMPLETA).get_data(as_text=True)

    assert re.search(r'<form method="post" action="/analise/dados"', html)
    assert "Editar a análise" in html


def test_a_volta_preserva_ate_o_valor_que_o_motor_recusou(cliente):
    """Quem volta vem justamente corrigir: apagar o valor recusado esconderia o que
    precisa ser corrigido."""
    html = cliente.post(
        "/analise/dados", data=dict(_ANALISE_COMPLETA, p="valor invalido")
    ).get_data(as_text=True)

    assert 'value="valor invalido"' in html
