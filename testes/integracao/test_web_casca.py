"""
Casca web: tema, fontes auto-hospedadas, sprite de ícones e macros.

O critério de pronto desta etapa é "a página abre com a rede desligada e nenhuma
requisição externa falha" (PLANO-FRONTEND §12). Esses testes são a versão automatizada
desse critério: em vez de confiar em desligar o wi-fi e olhar, varrem o HTML servido e
o CSS em busca de qualquer referência a host externo, e conferem que todo arquivo
citado existe e é servido.

Motivo de existir: no dia do teste de usabilidade, uma fonte que caia para o fallback
porque a máquina está sem internet faz o participante avaliar um problema que não é do
produto.
"""

import re
from pathlib import Path

import pytest

from siras.web import criar_app

_ESTATICOS = Path(__file__).parent.parent.parent / "siras" / "web" / "static"
_TEMPLATES = Path(__file__).parent.parent.parent / "siras" / "web" / "templates"

#: Os 24 símbolos do conjunto (PLANO-FRONTEND §6.3), mais a marca e os três que a
#: interface pediu depois: sol e lua para o alternador de tema, e a lupa. Todos seguem
#: as regras da família, inclusive a onda de horizonte que assina o conjunto.
_ICONES_ESPERADOS = {
    "perfil", "broto", "calagem", "analise", "regua", "alvo", "aptidao", "laudo", "rastro",
    "graos", "hortalicas", "tuberculos", "frutiferas", "erva", "comerciais",
    "alerta", "confere", "avanca", "volta", "imprime", "edita", "baixa", "info",
    "sol", "lua", "lupa",
    "marca",
}


@pytest.fixture
def cliente():
    app = criar_app({"TESTING": True})
    return app.test_client()


def _ids_do_sprite() -> set:
    sprite = (_ESTATICOS / "img" / "siras-icons.svg").read_text(encoding="utf-8")
    return set(re.findall(r'<symbol id="i-([a-z-]+)"', sprite))


def test_pagina_inicial_responde(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["Content-Type"]


def test_html_servido_nao_referencia_host_externo(cliente):
    """Nenhuma dependência de CDN: o sistema roda em localhost, offline."""
    html = cliente.get("/").get_data(as_text=True)
    externos = re.findall(r'(?:href|src)="(https?:)?//[^"]+"', html)
    assert not externos, f"referências externas no HTML: {externos}"


def test_css_nao_referencia_host_externo():
    for arquivo in sorted((_ESTATICOS / "css").glob("*.css")):
        texto = arquivo.read_text(encoding="utf-8")
        assert "http://" not in texto and "https://" not in texto, (
            f"{arquivo.name} referencia host externo"
        )
        assert "@import" not in texto, f"{arquivo.name} usa @import — outra requisição"


@pytest.mark.parametrize(
    "caminho",
    [
        "/static/css/siras-fontes.css",
        "/static/css/siras-theme.css",
        "/static/css/siras-telas.css",
        "/static/img/siras-icons.svg",
        "/static/fonts/sora-latin.woff2",
        "/static/fonts/sora-latin-ext.woff2",
        "/static/fonts/manrope-latin.woff2",
        "/static/fonts/manrope-latin-ext.woff2",
    ],
)
def test_estatico_e_servido(cliente, caminho):
    assert cliente.get(caminho).status_code == 200


def test_todo_font_face_aponta_para_arquivo_existente():
    css = (_ESTATICOS / "css" / "siras-fontes.css").read_text(encoding="utf-8")
    referenciados = re.findall(r"url\('\.\./fonts/([^']+)'\)", css)

    assert referenciados, "siras-fontes.css não declara nenhuma fonte local"
    for nome in referenciados:
        assert (_ESTATICOS / "fonts" / nome).is_file(), f"{nome} declarado e ausente"


def test_licenca_das_fontes_acompanha_os_arquivos():
    """SIL OFL 1.1 exige que a licença seja distribuída junto com a fonte."""
    for familia in ("sora", "manrope"):
        licenca = _ESTATICOS / "fonts" / f"OFL-{familia}.txt"
        assert licenca.is_file(), f"falta a licença de {familia}"
        assert "SIL OPEN FONT LICENSE" in licenca.read_text(encoding="utf-8").upper()


def test_sprite_tem_o_conjunto_completo():
    assert _ids_do_sprite() == _ICONES_ESPERADOS


def test_todo_icone_usado_nos_templates_existe_no_sprite():
    """Um href para um id inexistente não quebra a página: rende um espaço em branco.
    Este teste é o que transforma esse silêncio em falha."""
    disponiveis = _ids_do_sprite()
    usados = set()
    for template in _TEMPLATES.rglob("*.html"):
        texto = template.read_text(encoding="utf-8")
        usados |= set(re.findall(r"#i-([a-z-]+)", texto))
        usados |= set(re.findall(r'i\.ico\("([a-z-]+)"', texto))

    faltando = usados - disponiveis
    assert not faltando, f"ícones usados nos templates e ausentes do sprite: {faltando}"


def test_sprite_nao_carrega_metadados_da_ferramenta_de_origem():
    """O arquivo entregue com o plano trazia ~6 KB de manifesto C2PA em base64, resíduo
    da ferramenta que o gerou. Não é do projeto e não é versionado."""
    sprite = (_ESTATICOS / "img" / "siras-icons.svg").read_text(encoding="utf-8")
    assert "<metadata>" not in sprite
    assert "c2pa" not in sprite.lower()
