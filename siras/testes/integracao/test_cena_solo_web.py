"""Testes web da cena 3D, ligados às rotas reais do SIRAS (ADR 0012).

Nenhum teste depende do canvas: a cena é decoração, e a página precisa estar
inteira e navegável sem ela — sem JavaScript, sem WebGL, ou com a cena falhando.

O teste que mais importa aqui é o último: o laudo não recebe nada de 3D. É ele
que protege o escopo declarado, e por isso exercita a rota REAL do laudo, com um
POST de análise completa, em vez de uma rota de exemplo.
"""
import re
from pathlib import Path

import pytest

from siras.web import criar_app

ROTA_INICIO = "/"
RAIZ = Path(__file__).resolve().parents[2]
PARCIAL_GERANDO = RAIZ / "siras/web/templates/_parciais/gerando.html"

#: Uma análise completa de soja, no formato que o formulário envia. Mesma usada em
#: testes/integracao/test_web_interface.py — o laudo é POST, e não uma rota de GET.
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


@pytest.fixture
def html_inicio(cliente):
    resp = cliente.get(ROTA_INICIO)
    assert resp.status_code == 200
    return resp.get_data(as_text=True), cliente


def _sem_cena(html: str) -> str:
    """Remove contêiner, controles e legenda da cena: o que sobra é a página."""
    for marcador in ("data-cena-solo", "data-cena-controles", "data-cena-legenda"):
        html = re.sub(rf"<(div|figure)[^>]*{marcador}.*?</\1>", "", html, flags=re.S)
    return html


def test_hero_completa_sem_a_cena(html_inicio):
    html, _ = html_inicio
    pagina = _sem_cena(html)
    assert re.search(r"<h1[^>]*>.+?</h1>", pagina, re.S), "título da hero precisa existir sem a cena"
    assert re.search(r"<a [^>]*href=", pagina), "links/botões da hero precisam existir sem a cena"


def test_conteudo_vem_antes_da_cena_na_ordem_de_leitura(html_inicio):
    html, _ = html_inicio
    assert html.index("<h1") < html.index("data-cena-solo")


def test_contener_aria_hidden_e_nao_imprime(html_inicio):
    html, _ = html_inicio
    tag = re.search(r"<div[^>]*data-cena-solo=[^>]*>", html, re.S).group(0)
    assert 'aria-hidden="true"' in tag and "nao-imprime" in tag


def test_fallback_servido(html_inicio):
    html, cliente = html_inicio
    src = re.search(r'<img[^>]*cena-solo__fallback[^>]*src="([^"]+)"', html, re.S).group(1)
    assert cliente.get(src).status_code == 200


def test_script_com_defer_e_import_map_antes_do_primeiro_modulo(html_inicio):
    """O import map precisa existir antes do primeiro carregamento de MÓDULO — não
    antes de qualquer `script`.

    A distinção importa aqui. O primeiro `script` da página é o inline do `head` que
    aplica o tema salvo antes da primeira pintura, e ele tem de continuar sendo o
    primeiro: num `defer` no fim da página, quem usa o modo claro veria a tela escura
    piscar antes de clarear. Ele é script clássico e não dispara carregamento de
    módulo nenhum, então não compete com o import map.

    Quem usa o map é o `import()` dinâmico dentro de `cena-solo.js`, que roda bem
    depois — e o map está no `head`, antes de tudo o que importa."""
    html, _ = html_inicio
    tag = re.search(r'<script[^>]*src="[^"]*js/cena-solo\.js"[^>]*>', html).group(0)
    assert " defer" in tag

    pos_map = html.index('type="importmap"')
    modulos = [m.start() for m in re.finditer(r'<script[^>]*type="module"', html)]
    assert all(pos_map < pos for pos in modulos), (
        "o import map precisa vir antes de qualquer script de módulo"
    )
    # E antes de cena-solo.js, que é quem dispara o import() dinâmico.
    assert pos_map < html.index("js/cena-solo.js")


def test_motor_e_three_servidos(html_inicio):
    html, cliente = html_inicio
    motor = re.search(r'data-cena-motor="([^"]+)"', html).group(1)
    three = re.search(r'"three":\s*"([^"]+)"', html).group(1)
    assert cliente.get(motor).status_code == 200
    assert cliente.get(three).status_code == 200


def test_tela_de_espera_mantem_o_contrato_de_gerando_js():
    if not PARCIAL_GERANDO.exists():
        pytest.skip("ajuste PARCIAL_GERANDO para o caminho real")
    html = PARCIAL_GERANDO.read_text(encoding="utf-8")
    assert "data-etapa" in html, "gerando.js depende de data-etapa"


@pytest.mark.parametrize("formato", ["", "impressa"])
def test_laudo_sem_nada_de_3d(cliente, formato):
    """Escopo declarado: o laudo continua exatamente como está, em tela e impresso.

    É o teste que protege a fronteira. O cabeçalho da cena entra por BLOCO Jinja, e
    não em base.html, justamente para que esta página não baixe um byte de three.js
    nem um seletor de CSS que não vai usar."""
    dados = dict(_ANALISE)
    if formato:
        dados["formato"] = formato
    resposta = cliente.post("/analise/laudo", data=dados)

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    for marca in ("data-cena-solo", "cena-solo.css", "cena-solo.js",
                  "importmap", "three.module"):
        assert marca not in html, f"o laudo carregou '{marca}'"


def test_so_as_telas_ate_o_laudo_carregam_a_cena(cliente):
    """A cena existe na interface ATÉ a geração do laudo, e em nenhum outro lugar.

    A tela de dados entra na lista porque hospeda o véu da tela de espera, que tem
    cena; a de escolha da cultura e a de tabelas não têm nada que a cena ilustre."""
    com_cena = ("/", "/analise/dados?cultura_id=soja")
    sem_cena = ("/analise", "/tabelas")

    for rota in com_cena:
        assert "data-cena-solo" in cliente.get(rota).get_data(as_text=True), rota
    for rota in sem_cena:
        html = cliente.get(rota).get_data(as_text=True)
        assert "data-cena-solo" not in html and "importmap" not in html, rota
