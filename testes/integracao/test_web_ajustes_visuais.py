"""
Ajustes de escala, legibilidade e encaixe encontrados olhando a tela de verdade.

São defeitos de proporção, e não de lógica: um cabeçalho pequeno demais, um valor grande
demais que estoura a caixa, um ícone de ajuda que ninguém enxerga, uma seção de
referência ocupando metade do documento. Nenhum deles aparece num teste de motor, e todos
voltam na primeira refatoração de CSS se ninguém os guardar.
"""

import re
from pathlib import Path

import pytest

from siras.web import criar_app

_ESTATICOS = Path(__file__).parent.parent.parent / "siras" / "web" / "static"
_TELAS_CSS = (_ESTATICOS / "css" / "siras-telas.css").read_text(encoding="utf-8")
_IMPRESSA_CSS = (_ESTATICOS / "css" / "siras-impressa.css").read_text(encoding="utf-8")

_ANALISE = {
    "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
    "profundidade_incorporacao_cm": "20", "prnt": "100", "expectativa_rendimento": "3",
    "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
    "p": "11", "k": "96", "ctc_ph7": "9.4",
    "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
}


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


# --- barra que encolhe ao rolar -------------------------------------------------

def test_a_barra_e_a_marca_encolhem_juntas():
    """Altura, ícone e palavra saem da MESMA escala: encolher só um deles desequilibraria
    a assinatura, que é ícone e palavra montados lado a lado."""
    # Há mais de um bloco ".barra {": o de posicionamento e o de escala. Os tokens
    # precisam estar em algum deles, e não necessariamente no primeiro.
    blocos = "".join(re.findall(r"\n\.barra \{(.*?)\}", _TELAS_CSS, re.S))

    assert blocos, "nenhuma regra .barra encontrada"
    for token in ("--barra-escala", "--barra-altura", "--marca-icone", "--marca-palavra"):
        assert token in blocos, f"{token} não é declarado na barra"

    # .85: rolando, a barra fica 15% menor que o tamanho de repouso.
    assert re.search(r"\.barra\.is-reduzida \{[^}]*--barra-escala:\s*\.85\s*;", _TELAS_CSS)
    assert re.search(r"min-height: calc\(var\(--barra-altura\) \* var\(--barra-escala\)\)",
                     _TELAS_CSS)
    assert re.search(r"\.logo__icone \{[^}]*calc\(var\(--marca-icone\)", _TELAS_CSS, re.S)
    assert re.search(r"\.logo__nome \{ height: calc\(var\(--marca-palavra\)", _TELAS_CSS)


def test_o_encolhimento_tem_faixa_morta_para_nao_tremer():
    """Com um limiar só, uma página parada exatamente nele alterna de estado a cada pixel
    de rolagem e a barra treme."""
    codigo = (_ESTATICOS / "js" / "barra.js").read_text(encoding="utf-8")

    limiar = int(re.search(r"var LIMIAR = (\d+)", codigo).group(1))
    volta = int(re.search(r"var VOLTA = (\d+)", codigo).group(1))

    assert limiar > volta, "sem faixa morta entre reduzir e voltar"
    assert "requestAnimationFrame" in codigo, "medir a cada evento de rolagem trava o gesto"
    assert "passive: true" in codigo


def test_a_barra_nao_carrega_medida_em_pixel_no_javascript():
    """Os tamanhos são do CSS. O JavaScript só põe e tira uma classe — mexer no tamanho
    da marca não pode exigir editar dois arquivos."""
    codigo = (_ESTATICOS / "js" / "barra.js").read_text(encoding="utf-8")

    assert "is-reduzida" in codigo
    assert "style." not in codigo, "o script está escrevendo estilo direto"


def test_o_encolhimento_respeita_quem_pediu_menos_animacao():
    assert re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{[^}]*\.barra__int[^}]*transition: none",
        _TELAS_CSS, re.S,
    )


def test_a_barra_e_carregada_em_toda_pagina(cliente):
    assert "js/barra.js" in cliente.get("/").get_data(as_text=True)


# --- legibilidade e encaixe dos campos ------------------------------------------

def test_o_valor_do_campo_nao_usa_corpo_de_titulo():
    """18px em fonte display estourava a caixa: num <select> com 'Plantio direto
    consolidado com restrições' o texto era cortado pela seta."""
    assert re.search(
        r"\.campo__caixa input, \.campo__caixa select \{ font-size: var\(--fs-md\)", _TELAS_CSS
    )
    assert re.search(r"\.campo__caixa select \{ font-size: var\(--fs-sm\)", _TELAS_CSS)


def test_a_ajuda_do_campo_e_legivel():
    """A frase que mais explica o que preencher estava no menor corpo da escala."""
    assert re.search(r"\.campo__ajuda \{ font-size: var\(--fs-2xs\)", _TELAS_CSS)


def test_as_caixas_de_campos_vizinhos_se_alinham():
    """Textos de ajuda de tamanhos diferentes desalinhavam as caixas da mesma linha: uma
    começava onde a outra já terminara."""
    assert re.search(
        r"@supports \(grid-template-rows: subgrid\) \{.*?grid-template-rows: subgrid",
        _TELAS_CSS, re.S,
    )


def test_o_rotulo_quebra_em_vez_de_empurrar_a_dica_para_fora():
    assert re.search(r"\.campo__label \{ flex-wrap: wrap", _TELAS_CSS)


def test_o_i_da_dica_e_um_alvo_visivel_nos_dois_temas():
    """Sem fundo nem contorno ele sumia dentro do rótulo, e ninguém descobria que havia
    explicação ali."""
    escuro = re.search(r"\n\.dica__gatilho \{(.*?)\}", _TELAS_CSS, re.S).group(1)

    assert "background:" in escuro and "border:" in escuro
    assert re.search(
        r':root\[data-tema="claro"\] \.dica__gatilho \{[^}]*background:', _TELAS_CSS, re.S
    )


# --- a trilha como nota de rodapé -----------------------------------------------

def test_a_trilha_e_compacta(cliente):
    """É a seção mais longa do laudo e a menos protagonista: dá valor em análise de
    crédito rural, e não é o que o técnico veio buscar."""
    html = cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)

    assert 'class="sec sec--nota"' in html
    assert re.search(r"\.trilha \{[^}]*font-size: var\(--fs-2xs\)", _TELAS_CSS)
    assert re.search(r"\.trilha__passo \{[^}]*padding: 3px 0", _TELAS_CSS, re.S)


def test_a_trilha_nao_repete_um_icone_por_passo(cliente):
    """Vinte cópias do mesmo desenho não informavam nada e custavam uma coluna."""
    html = cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)
    trilha = html[html.index("De onde vem cada número"):]

    assert trilha.count("#i-rastro") <= 1


def test_a_fonte_fecha_a_mesma_frase_da_regra():
    """Em bloco próprio, cada passo ocupava duas linhas — quarenta linhas ao todo."""
    assert re.search(r"\.trilha__fonte \{ display: inline", _TELAS_CSS)


def test_a_trilha_continua_completa(cliente):
    """Compactar é diminuir o corpo, e não filtrar passo: a rastreabilidade inteira é o
    que dá ao laudo valor em análise de crédito rural."""
    html = cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)

    assert html.count('class="trilha__passo"') >= 10
    assert html.count('class="trilha__modulo"') == 3


# --- a versão impressa é mesmo preto e branco -----------------------------------

def test_a_folha_impressa_nao_tem_uma_gota_de_verde():
    """Uma tarja verde sobrevivente é pior que a peça inteira colorida: numa laser
    monocromática ela vira um cinza médio sem significado."""
    verde = re.findall(
        r"var\(--v-\d+\)|#8CE23F|#4E9A2A|rgba\(140,\s*226,\s*63|rgba\(78,\s*154,\s*42",
        _IMPRESSA_CSS,
    )

    assert not verde, f"verde remanescente na folha impressa: {verde}"


def test_a_folha_impressa_vence_o_tema_claro():
    """O tema claro pinta com ':root[data-tema=claro] .classe', que pesa mais que
    'body.impressa .classe'. Foi assim que o botão Imprimir saiu com texto escuro sobre
    fundo preto — ilegível."""
    # Os comentários precedem os seletores e entrariam na captura. E a regra vale para o
    # que pinta o DOCUMENTO — "body.impressa ..."; a barra de ações desta tela não
    # disputa com o tema, porque é a única coisa aqui que o tema nunca pintou.
    sem_comentario = re.sub(r"/\*.*?\*/", "", _IMPRESSA_CSS, flags=re.S)
    regras = re.findall(r"([^{}]+)\{[^{}]*\}", sem_comentario)
    do_documento = [" ".join(r.split()) for r in regras if "body.impressa" in r]

    assert do_documento, "nenhuma regra do documento encontrada"
    for regra in do_documento:
        assert regra.startswith(":root"), f"regra sem :root, perde para o tema: {regra[:60]}"


def test_o_botao_imprimir_tem_contraste_no_modo_claro():
    assert re.search(
        r":root body\.impressa \.btn--primario \{[^}]*background: #000000;[^}]*color: #FFFFFF",
        _IMPRESSA_CSS, re.S,
    )


def test_o_icone_do_botao_acompanha_o_texto():
    """O ícone da impressora herda currentColor: se o texto vai a branco, ele vai junto —
    e é por isso que basta acertar a cor do botão."""
    assert re.search(r"\.ico \{[^}]*color: inherit", (
        _ESTATICOS / "css" / "siras-theme.css"
    ).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "seletor",
    [r"\.sec__cab \.ico", r"\.cenarios__seta", r"\.orientacao--parcelamento",
     r"\.trilha__link"],
)
def test_cada_resto_de_verde_do_documento_foi_neutralizado(seletor):
    assert re.search(rf":root body\.impressa {seletor}", _IMPRESSA_CSS), (
        f"{seletor} ainda pode sair colorido no papel"
    )


# --- rodapé do campo: ajuda e aviso sem sobreposição ----------------------------

def test_todo_campo_tem_um_rodape_proprio(cliente):
    """O aviso de validação era injetado solto no fim do rótulo. Com a grade alinhando os
    campos por subgrid, esse quarto filho ficava sem faixa e era desenhado POR CIMA da
    ajuda — as duas frases sobrepostas."""
    tela = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert tela.count("campo__rodape") >= tela.count("campo__ajuda")
    assert re.search(r"\.campo__rodape \{ display: grid", _TELAS_CSS)


def test_o_aviso_nasce_dentro_do_rodape():
    codigo = (_ESTATICOS / "js" / "interacoes.js").read_text(encoding="utf-8")

    assert '.campo__rodape") || rotulo).appendChild(aviso)' in codigo


def test_a_ajuda_continua_ligada_ao_campo_por_aria(cliente):
    """Mover a ajuda para dentro do rodapé não pode soltá-la do campo que ela explica."""
    tela = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert 'aria-describedby="ph_agua-ajuda"' in tela
    assert 'id="ph_agua-ajuda"' in tela


# --- validação alcança os talhões acrescentados depois --------------------------

def test_a_validacao_e_delegada_e_nao_ligada_campo_a_campo():
    """Um talhão acrescentado pelo botão nasce depois da carga da página. Ligando ouvinte
    a ouvinte, esses cartões ficavam sem validação nenhuma — dava para digitar -500 de pH
    ali e nada acusava."""
    codigo = (_ESTATICOS / "js" / "interacoes.js").read_text(encoding="utf-8")

    assert 'document.addEventListener("focusout"' in codigo, (
        "blur não sobe na árvore e não pode ser delegado"
    )
    assert 'document.addEventListener("input"' in codigo
    assert "querySelectorAll('.campo input[type=\"number\"]')" not in codigo


def test_os_campos_do_talhao_adicional_declaram_a_mesma_faixa(cliente):
    """Sem min e max, a validação imediata não tem o que comparar."""
    dados = {
        "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
        "profundidade_incorporacao_cm": "20", "prnt": "100",
        "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
        "p": "11", "k": "96", "ctc_ph7": "9.4", "al": "1.2", "ca": "2.4", "mg": "1.1",
        "v_percent": "42", "talhao": "A1", "talhao__2": "B2", "ph_agua__2": "5.8",
    }
    tela = cliente.post("/analise/dados", data=dados).get_data(as_text=True)

    campo = re.search(r'<input[^>]*id="ph_agua__2"[^>]*>', tela).group(0)
    assert 'min="0"' in campo and 'max="14"' in campo
    assert "required" in campo


def test_o_talhao_adicional_e_obrigatorio_campo_a_campo(cliente):
    """Os campos do cartão saem do mesmo macro do formulário principal: se um for
    obrigatório lá, é obrigatório aqui."""
    tela = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)
    molde = tela[tela.index('id="molde-talhao"'):]

    # O id do molde é o nome do campo mais "__" mais a marca "__IDX__", que o JavaScript
    # troca pelo índice do talhão ao clonar.
    for campo in ("ph_agua", "indice_smp", "argila", "mo", "p", "k", "ctc_ph7"):
        marcacao = re.search(rf'<input[^>]*id="{campo}____IDX__"[^>]*>', molde).group(0)
        assert "required" in marcacao, f"{campo} não é obrigatório no cartão de talhão"


# --- o aviso de campo obrigatório é do programa ---------------------------------

def test_o_formulario_troca_a_bolha_do_navegador_pela_propria():
    """A bolha nativa é cinza, escrita pelo sistema operacional, mostra um campo por vez e
    some ao primeiro clique — a única peça da tela que não pertence ao produto."""
    codigo = (_ESTATICOS / "js" / "envio.js").read_text(encoding="utf-8")

    assert 'setAttribute("novalidate"' in codigo
    assert "Este campo precisa ser preenchido." in codigo
    assert "preventDefault" in codigo


def test_o_novalidate_e_posto_pelo_script_e_nao_escrito_no_html(cliente):
    """Desligar a validação no HTML deixaria quem está sem JavaScript sem nenhuma, e o
    servidor recebendo envio vazio."""
    tela = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)
    formulario = re.search(r"<form[^>]*data-formulario-analise[^>]*>", tela).group(0)

    assert "novalidate" not in formulario


def test_o_aviso_marca_todos_os_campos_de_uma_vez():
    """Um campo por clique faz o usuário descobrir o formulário aos poucos."""
    codigo = (_ESTATICOS / "js" / "envio.js").read_text(encoding="utf-8")

    assert "vazios.forEach(avisar)" in codigo
    assert "campos obrigatórios" in codigo
    assert "vazios[0].focus" in codigo


def test_a_tela_de_calculo_nao_sobe_sobre_envio_barrado():
    """O véu abriria sobre um formulário que nem foi enviado e ficaria girando."""
    codigo = (_ESTATICOS / "js" / "gerando.js").read_text(encoding="utf-8")

    assert "checkValidity()" in codigo


def test_o_envio_e_carregado_na_tela_de_dados(cliente):
    assert "js/envio.js" in cliente.get(
        "/analise/dados?cultura_id=soja"
    ).get_data(as_text=True)


# --- nada genérico: a barra de rolagem também é do sistema ----------------------

def test_a_barra_de_rolagem_segue_a_paleta():
    """A barra do sistema operacional é a última peça genérica de uma interface que
    desenhou o próprio conjunto de ícones — e num tema escuro ela aparece clara."""
    assert "::-webkit-scrollbar-thumb" in _TELAS_CSS
    assert re.search(r"scrollbar-color: var\(--n-700\)", _TELAS_CSS)
    assert re.search(r':root\[data-tema="claro"\] \* \{ scrollbar-color:', _TELAS_CSS)


# --- cada bloco com o seu próprio símbolo ---------------------------------------

def test_nenhum_bloco_do_formulario_toma_emprestado_o_icone_de_outro(cliente):
    """Três blocos vizinhos com o mesmo desenho deixam de identificar seja lá o que for:
    'A área analisada', 'Subsuperfície' e 'Outros talhões' dividiam o mesmo perfil."""
    tela = cliente.get("/analise/dados?cultura_id=abacateiro").get_data(as_text=True)

    icones = re.findall(r'<div class="bloco__cab">\s*<svg[^>]*><use href="[^"]*#i-([a-z-]+)"', tela)
    icones += re.findall(
        r'<summary class="bloco__cab"[^>]*>\s*<svg[^>]*><use href="[^"]*#i-([a-z-]+)"', tela
    )

    assert len(icones) >= 5, f"poucos blocos encontrados: {icones}"
    assert len(icones) == len(set(icones)), f"ícone repetido entre blocos: {icones}"


@pytest.mark.parametrize(
    "nome",
    ["manejo", "aplicar", "area", "subsolo", "talhao", "talhoes", "assina", "soma",
     "adiciona", "exemplo"],
)
def test_todo_icone_novo_segue_as_regras_da_familia(nome):
    """Grade de 24, traço de 1.75, sem preenchimento, e a onda de horizonte que assina o
    conjunto — é ela que separa este desenho de qualquer biblioteca genérica."""
    sprite = (_ESTATICOS / "img" / "siras-icons.svg").read_text(encoding="utf-8")
    simbolo = re.search(rf'<symbol id="i-{nome}".*?</symbol>', sprite, re.S).group(0)

    assert 'viewBox="0 0 24 24"' in simbolo
    assert 'stroke-width="1.75"' in simbolo
    assert 'fill="none"' in simbolo
    assert 'stroke="currentColor"' in simbolo
    # A onda: uma curva em S dupla, com dois pares de controle espelhados.
    assert re.search(r"c[\d\s.,-]+s[\d\s.,-]+", simbolo), f"i-{nome} não tem onda de horizonte"


# --- o selo de aptidão ----------------------------------------------------------

_APTA_COM_RESTRICOES = {
    "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
    "profundidade_incorporacao_cm": "20", "prnt": "100",
    "ph_agua": "6.0", "indice_smp": "6.1", "argila": "16", "mo": "1.6",
    "p": "22.0", "k": "120", "ctc_ph7": "5.1",
    "al": "0.0", "ca": "3.1", "mg": "1.2", "v_percent": "68",
}

_APTA = dict(
    _APTA_COM_RESTRICOES,
    ph_agua="6.3", indice_smp="6.2", argila="44", mo="3.6",
    p="28.0", k="210", ctc_ph7="14.2", al="0.0", ca="7.4", mg="2.8", v_percent="78",
)


def test_apta_com_restricoes_sai_verde_e_nao_amarela(cliente):
    """Âmbar ali dizia que a área não está apta. Ela está: a restrição qualifica a
    aptidão, não a retira — e um selo amarelo logo abaixo da recomendação fazia o leitor
    entender que a recomendação não seria suficiente."""
    html = cliente.post("/analise/laudo", data=_APTA_COM_RESTRICOES).get_data(as_text=True)

    assert "Apta com restrições" in html
    assert "--cor:#57A331" in html
    assert "--cor:var(--sig-ambar)" not in html


def test_a_apta_recebe_o_verde_mais_vivo(cliente):
    html = cliente.post("/analise/laudo", data=_APTA).get_data(as_text=True)

    assert "--cor:#3E8F14" in html


def test_a_ressalva_ganha_uma_marca_discreta_de_atencao(cliente):
    html = cliente.post("/analise/laudo", data=_APTA_COM_RESTRICOES).get_data(as_text=True)

    assert "aptidao__selo--atencao" in html
    assert "aptidao__atencao" in html
    assert re.search(r"\.aptidao__atencao \{[^}]*width: 22px", _TELAS_CSS, re.S), (
        "a marca precisa ser pequena: ela avisa, não compete com o veredito"
    )


def test_a_apta_sem_ressalva_nao_ganha_marca(cliente):
    html = cliente.post("/analise/laudo", data=_APTA).get_data(as_text=True)

    assert "aptidao__atencao" not in html


def test_a_marca_de_atencao_e_decorativa_para_o_leitor_de_tela(cliente):
    """O rótulo 'Apta com restrições' já diz o que ela marca: anunciá-la de novo seria
    repetição (WCAG 1.4.1 exige o texto, não o dobro dele)."""
    html = cliente.post("/analise/laudo", data=_APTA_COM_RESTRICOES).get_data(as_text=True)
    marca = re.search(r'<span class="aptidao__atencao"[^>]*>', html).group(0)

    assert 'aria-hidden="true"' in marca


def test_no_papel_preto_e_branco_a_marca_vira_contorno():
    """O âmbar não sobrevive a uma laser monocromática; a forma sobrevive."""
    assert re.search(r":root body\.impressa \.aptidao__atencao \{[^}]*border-color: #000000",
                     _IMPRESSA_CSS, re.S)
