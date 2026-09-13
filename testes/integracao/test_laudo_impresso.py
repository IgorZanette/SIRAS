"""
Folha de impressão do laudo.

Não há como renderizar um PDF aqui sem acrescentar um navegador às dependências do
projeto, então o que estes testes verificam é o que dá para verificar sem ele, e que é
justamente o que costuma quebrar em silêncio: controle de tela que vaza para o papel, e
regra de quebra de página que some numa refatoração do CSS.

A legibilidade em A4 continua sendo conferência visual do autor — imprimir e olhar.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

from siras.web import criar_app

_TELAS_CSS = Path(__file__).parent.parent.parent / "siras" / "web" / "static" / "css" / "siras-telas.css"

#: Elementos sem tag de fechamento, que não entram na pilha de ancestrais.
_VAZIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
           "link", "meta", "param", "source", "track", "wbr"}


class _Arvore(HTMLParser):
    """Percorre o HTML guardando, para cada elemento, se algum ancestral o oculta na
    impressão. É a única forma honesta de responder "este botão sai no papel?" — olhar
    só o próprio elemento não vê o .nao-imprime do contêiner."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pilha = []
        self.controles = []   # (tag, oculto_na_impressao)
        self.documento_oculto = None

    def _classes(self, attrs):
        return (dict(attrs).get("class") or "").split()

    def handle_starttag(self, tag, attrs):
        classes = self._classes(attrs)
        herdado = self.pilha[-1][1] if self.pilha else False
        oculto = herdado or "nao-imprime" in classes

        if tag == "button" or (tag == "a" and "btn" in classes):
            self.controles.append((tag, oculto))
        if "doc" in classes and tag == "article":
            self.documento_oculto = oculto

        if tag not in _VAZIOS:
            self.pilha.append((tag, oculto))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VAZIOS and self.pilha:
            self.pilha.pop()

    def handle_endtag(self, tag):
        for indice in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[indice][0] == tag:
                del self.pilha[indice:]
                return


@pytest.fixture
def html_do_laudo():
    formulario = {
        "cultura_id": "milho", "criterio_id": "graos_convencional", "cultivo": "1",
        "profundidade_incorporacao_cm": "20", "antecedente": "leguminosa",
        "prnt": "100", "expectativa_rendimento": "9",
        "ph_agua": "5.1", "indice_smp": "5.4", "al": "1.2", "ca": "2.4", "mg": "1.1",
        "v_percent": "42", "saturacao_al": "", "argila": "38", "mo": "2.8",
        "p": "11", "k": "96", "ctc_ph7": "9.4",
    }
    cliente = criar_app({"TESTING": True}).test_client()
    resposta = cliente.post("/analise/laudo", data=formulario)
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


def test_nenhum_controle_de_tela_vai_para_o_papel(html_do_laudo):
    """Botão impresso num laudo que vai anexado a projeto de crédito é ruído que o
    técnico não consegue explicar ao analista do banco."""
    arvore = _Arvore()
    arvore.feed(html_do_laudo)

    assert arvore.controles, "nenhum controle encontrado — o teste não está vendo a página"
    vazando = [tag for tag, oculto in arvore.controles if not oculto]
    assert not vazando, f"{len(vazando)} controle(s) sem .nao-imprime em nenhum ancestral"


def test_o_documento_em_si_nao_esta_oculto(html_do_laudo):
    """Guarda contra o teste acima passar pelo motivo errado: se alguém marcasse o
    laudo inteiro como .nao-imprime, nenhum controle vazaria e o papel sairia em branco."""
    arvore = _Arvore()
    arvore.feed(html_do_laudo)

    assert arvore.documento_oculto is False


def test_a_barra_de_etapas_nao_e_impressa(html_do_laudo):
    assert re.search(r'<ol class="etapas nao-imprime"', html_do_laudo)


def _bloco_de_impressao() -> str:
    css = _TELAS_CSS.read_text(encoding="utf-8")
    inicio = css.index("@media print")
    return css[inicio:]


def test_a_quebra_e_restringida_ao_item_e_nao_a_secao():
    """O tema aplica break-inside:avoid a section. Numa seção mais alta que a folha —
    a trilha tem mais de vinte passos — isso só empurra a seção para a página seguinte e
    deixa meia folha em branco, porque a restrição acaba ignorada de todo jeito."""
    bloco = _bloco_de_impressao()

    assert re.search(r"section,\s*\.painel\s*\{[^}]*break-inside:\s*auto", bloco)
    for item in (".dose", ".atributo", ".trilha__item", ".limitante"):
        assert re.search(rf"{re.escape(item)}[^{{]*\{{[^}}]*break-inside:\s*avoid", bloco), (
            f"{item} pode partir entre páginas"
        )


def test_titulo_nao_fica_orfao_no_pe_da_pagina():
    assert re.search(r"break-after:\s*avoid", _bloco_de_impressao())


def test_a_cromia_do_diagnostico_sobrevive_a_impressao():
    """A régua e a ficha são o que carrega a interpretação. Impressas em cinza, o laudo
    perde justamente a leitura que o diferencia de uma planilha."""
    bloco = _bloco_de_impressao()
    assert "print-color-adjust: exact" in bloco
    for componente in (".regua__faixa", ".ficha"):
        assert componente in bloco


def test_a_malha_de_fundo_nao_vai_para_o_papel():
    assert re.search(r"body\.malha\s*\{[^}]*background-image:\s*none", _bloco_de_impressao())


# --- versão impressa: A4 em preto e branco -------------------------------------

_IMPRESSA_CSS = (
    Path(__file__).parent.parent.parent / "siras" / "web" / "static" / "css"
    / "siras-impressa.css"
).read_text(encoding="utf-8")

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


def test_o_laudo_em_cores_oferece_a_versao_impressa(cliente):
    html = cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)

    assert "Versão impressa" in html
    assert "Salvar em PDF" in html, "a versão trabalhada continua sendo oferecida"


def test_a_versao_impressa_troca_a_folha_de_estilo(cliente):
    resposta = cliente.post("/analise/laudo", data=dict(_ANALISE, formato="impressa"))
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert "siras-impressa.css" in html
    assert re.search(r'<body class="[^"]*\bimpressa\b', html)


def test_a_versao_em_cores_nao_carrega_a_folha_de_impressao(cliente):
    html = cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)

    assert "siras-impressa.css" not in html
    assert not re.search(r'<body class="[^"]*\bimpressa\b', html)


def test_o_formato_nao_gruda_na_analise(cliente):
    """'formato' diz como ESTA tela foi pedida. Se viajasse nos campos ocultos, voltar à
    edição a partir da versão impressa devolveria sempre a versão impressa."""
    html = cliente.post(
        "/analise/laudo", data=dict(_ANALISE, formato="impressa")
    ).get_data(as_text=True)

    assert 'name="formato" value="impressa"' not in html


def test_a_versao_impressa_mantem_o_conteudo_do_laudo(cliente):
    """Outra folha de estilo, e não outro documento: o que muda é a cor, não o que o
    laudo diz."""
    cores = cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)
    papel = cliente.post(
        "/analise/laudo", data=dict(_ANALISE, formato="impressa")
    ).get_data(as_text=True)

    for marca in ("Laudo de recomendação", "Responsável Técnico", "Assinatura e carimbo"):
        assert marca in cores and marca in papel


def test_a_rampa_de_classes_vira_cinza_monotono():
    """Num documento sem cor a única coisa que distingue cinco faixas é a luminosidade, e
    ela precisa crescer na mesma direção que a grandeza — senão a régua mente."""
    tons = []
    for classe in ("f-mb", "f-b", "f-m", "f-a", "f-ma"):
        achado = re.search(rf"\.{classe}\s*\{{\s*--cor:\s*#([0-9A-F]{{6}})", _IMPRESSA_CSS)
        assert achado, f"a folha impressa não redefine .{classe}"
        valor = achado.group(1)
        assert valor[0:2] == valor[2:4] == valor[4:6], f".{classe} não é cinza: #{valor}"
        tons.append(int(valor[0:2], 16))

    assert tons == sorted(tons, reverse=True), f"a rampa não é monótona: {tons}"


def test_a_faixa_vigente_e_marcada_por_forma_e_nao_por_tom():
    """Tom sobrevive mal a uma fotocópia; contorno sobrevive."""
    assert re.search(r"\.regua__faixa\.is-atual[^}]*outline:\s*[\d.]+px solid #000000",
                     _IMPRESSA_CSS, re.S)


def test_a_folha_impressa_declara_a4():
    assert re.search(r"@page \{ size: A4 portrait", _IMPRESSA_CSS)


def test_os_cinzas_sobrevivem_a_caixa_de_impressao():
    """Sem print-color-adjust o navegador descarta os fundos e as cinco faixas viram
    cinco retângulos brancos."""
    bloco = re.search(r"@media print \{(.*)\}", _IMPRESSA_CSS, re.S).group(1)

    assert "print-color-adjust: exact" in bloco
    assert ".regua__faixa" in bloco


def test_a_aplicacao_nao_acompanha_o_documento_impresso(cliente):
    """Na versão impressa o laudo não está dentro de uma ferramenta: ele é a entrega."""
    assert re.search(r"body\.impressa \.barra,", _IMPRESSA_CSS)
    assert re.search(r"body\.impressa \.etapas,", _IMPRESSA_CSS)
