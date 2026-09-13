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

    assert re.search(r"\.barra\.is-reduzida \{[^}]*--barra-escala:\s*\.8", _TELAS_CSS)
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
