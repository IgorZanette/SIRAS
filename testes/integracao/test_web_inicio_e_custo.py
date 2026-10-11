"""
A tela inicial que vende sem inventar, e a calculadora de custo do laudo.

Pedido do autor (13/09/2026): a tela inicial precisava fazer a pessoa pensar "isso vai me
ajudar", falando com o produtor e com o técnico com o mesmo peso, dizendo que o sistema é
gratuito e sem citar a conformidade. E o laudo passou a dizer quanto a recomendação custa.

O que estes testes guardam, acima de tudo, é a regra que torna a página defensável: nenhum
benefício com número inventado, e nenhum preço ou teor de fertilizante vindo do sistema.
"""

import json
import re
from types import SimpleNamespace

import pytest

from siras.dominio.escopo import TOTAL_DE_CULTURAS_NO_ESCOPO
from siras.relatorio.apresentacao import insumos_para_custo
from siras.web import criar_app

_UM_TALHAO = {
    "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
    "profundidade_incorporacao_cm": "20", "prnt": "100", "expectativa_rendimento": "3",
    "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
    "p": "11", "k": "96", "ctc_ph7": "9.4",
    "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
}


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


def _inicio(cliente) -> str:
    return cliente.get("/").get_data(as_text=True)


def _texto_da_pagina(html: str) -> str:
    corpo = html[html.index("<main"):html.index("</main>")]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", corpo))


# --- a tela inicial fala de benefício ------------------------------------------------

def test_a_promessa_e_um_beneficio_e_nao_uma_funcao(cliente):
    html = _inicio(cliente)

    assert "na dose que o seu solo pede" in html
    assert "Nem a mais, nem a menos." in html


def test_produtor_e_tecnico_tem_o_mesmo_peso(cliente):
    """Decisão do autor: os dois públicos, lado a lado, com a mesma quantidade de
    benefícios — nenhum deles como nota de rodapé do outro."""
    html = _inicio(cliente)
    publicos = re.findall(r'<article class="painel painel--marca publico">(.*?)</article>', html, re.S)

    assert len(publicos) == 2
    assert "Para o produtor" in publicos[0]
    assert "Para o agrônomo e o técnico" in publicos[1]
    assert publicos[0].count("<li>") == publicos[1].count("<li>")


def test_a_gratuidade_e_dita(cliente):
    texto = _texto_da_pagina(_inicio(cliente))

    assert "Gratuito" in texto
    assert "Grátis" in texto


def test_nenhuma_promessa_com_numero_inventado(cliente):
    """Sem "X% a mais" e sem "R$ Y economizados": seria dado fabricado, e é o primeiro
    número que a banca pede para ver de onde veio."""
    texto = _texto_da_pagina(_inicio(cliente))

    assert not re.search(r"\d+\s*%", texto), "percentual na tela inicial"
    assert not re.search(r"R\$\s*\d", texto), "valor em reais na tela inicial"


def test_a_conformidade_nao_e_usada_como_argumento(cliente):
    """Decisão do autor: a conformidade é resultado do trabalho, não peça de venda."""
    assert "conformidade" not in _texto_da_pagina(_inicio(cliente)).lower()


def test_o_escopo_citado_e_o_do_sistema(cliente):
    html = _inicio(cliente)

    assert f'data-contador="{TOTAL_DE_CULTURAS_NO_ESCOPO}"' in html
    assert f"{TOTAL_DE_CULTURAS_NO_ESCOPO} culturas" in html


@pytest.mark.parametrize("secao", [
    "titulo-problema", "titulo-comparativo", "titulo-como", "titulo-publico",
    "titulo-laudo", "titulo-confianca", "titulo-perguntas",
])
def test_a_historia_da_pagina_esta_inteira(cliente, secao):
    assert f'id="{secao}"' in _inicio(cliente)


def test_o_comparativo_rola_sozinho_em_tela_estreita(cliente):
    """Só a tabela pode ser mais larga que a tela, e dentro do próprio contêiner."""
    html = _inicio(cliente)

    assert re.search(r'<div class="comparativo-rolagem">\s*<table class="comparativo">', html)
    assert html.count('<th scope="row">') >= 5


def test_as_perguntas_frequentes_abrem_sem_javascript(cliente):
    assert _inicio(cliente).count('<details class="pergunta">') >= 5


def test_o_exemplo_abre_o_formulario_preenchido(cliente):
    html = _inicio(cliente)
    link = re.search(r'href="([^"]*exemplo=unico[^"]*)"', html).group(1).replace("&amp;", "&")

    resposta = cliente.get(link)

    assert resposta.status_code == 200
    assert 'name="ph_agua"' in resposta.get_data(as_text=True)


def test_a_previa_do_laudo_nao_mostra_valores(cliente):
    """A prévia é a estrutura do documento: dose de vitrine seria número agronômico
    fabricado."""
    previa = re.search(r'<figure class="previa".*?</figure>', _inicio(cliente), re.S).group(0)

    assert not re.search(r"\d", re.sub(r"<[^>]+>", "", previa).replace("P2O5", "").replace("K2O", ""))
    assert "ilustração sem valores" in previa


def test_a_apresentacao_continua_na_tela_inicial(cliente):
    assert 'id="guia"' in _inicio(cliente)


# --- a calculadora de custo ------------------------------------------------------------

def _laudo(nc=2.0, n=30.0, p2o5=40.0, k2o=50.0):
    return SimpleNamespace(
        calagem=SimpleNamespace(nc_t_ha=nc),
        adubacao=SimpleNamespace(n=n, p2o5=p2o5, k2o=k2o),
    )


def test_insumos_levam_so_as_doses_do_motor():
    custo = insumos_para_custo([SimpleNamespace(rotulo="A1", area_ha=12.5, laudo=_laudo())])

    assert custo["talhoes"] == [{
        "rotulo": "A1", "area_ha": 12.5,
        "doses": {"calagem": 2.0, "n": 30.0, "p2o5": 40.0, "k2o": 50.0},
    }]
    for grandeza in custo["grandezas"]:
        assert set(grandeza) == {"nome", "rotulo", "chave", "tem_dose"}


def test_dose_em_intervalo_fica_fora_da_conta():
    intervalo = {"min": 20.0, "max": 40.0}
    custo = insumos_para_custo([SimpleNamespace(rotulo="", area_ha=None, laudo=_laudo(p2o5=intervalo))])

    assert custo["talhoes"][0]["doses"]["p2o5"] is None
    assert custo["talhoes"][0]["area_ha"] is None
    assert next(g for g in custo["grandezas"] if g["chave"] == "p2o5")["tem_dose"] is True


def test_grandeza_sem_dose_em_nenhum_talhao_nao_pede_preco():
    custo = insumos_para_custo([
        SimpleNamespace(rotulo="A", area_ha=1, laudo=_laudo(nc=0.0, n=0.0)),
        SimpleNamespace(rotulo="B", area_ha=2, laudo=_laudo(nc=0.0, n=0.0)),
    ])
    tem = {g["chave"]: g["tem_dose"] for g in custo["grandezas"]}

    assert tem == {"calagem": False, "n": False, "p2o5": True, "k2o": True}


def test_o_laudo_traz_a_calculadora_com_as_doses(cliente):
    html = cliente.post("/analise/laudo", data=_UM_TALHAO).get_data(as_text=True)

    assert "data-custo" in html
    assert "js/custo.js" in html
    dados = json.loads(re.search(
        r'<script type="application/json" id="custo-dados">(.*?)</script>', html, re.S
    ).group(1))
    assert len(dados["talhoes"]) == 1
    assert set(dados["talhoes"][0]["doses"]) == {"calagem", "n", "p2o5", "k2o"}


_CAMPOS_DE_CUSTO = (
    r"<input[^>]*data-(?:calcario-preco|formula|saca-peso|saca-preco|comp-teor|comp-peso|comp-preco)"
    r"[^>]*>"
)


def test_nenhuma_formula_peso_ou_preco_vem_preenchido(cliente):
    """Fórmula, peso da saca e teor estão no rótulo do que a pessoa compra: sugerir um
    valor típico seria afirmação agronômica da interface."""
    html = cliente.post("/analise/laudo", data=_UM_TALHAO).get_data(as_text=True)
    campos = re.findall(_CAMPOS_DE_CUSTO, html, re.S)

    assert len(campos) == 1 + 3 * 3 + 3
    assert not any("value=" in campo for campo in campos)


def test_ate_tres_formulas_e_complemento_opcional(cliente):
    html = cliente.post("/analise/laudo", data=_UM_TALHAO).get_data(as_text=True)

    assert html.count("data-formula-opcao") == 3
    assert "data-complemento" in html
    assert "Complemento de nitrogênio" in html


def test_o_criterio_de_dose_e_declarado_na_tela(cliente):
    """Decisão do autor (13/09/2026): a dose é a maior entre a que cobre P2O5 e a que
    cobre K2O. Critério que muda o resultado precisa estar escrito onde o resultado está."""
    html = cliente.post("/analise/laudo", data=_UM_TALHAO).get_data(as_text=True)
    nota = re.search(r'<p class="t-aux custo__nota">(.*?)</p>', html, re.S).group(1)

    assert "Critério de dose" in nota
    assert "não indica quando aplicar o complemento" in nota


def test_a_calculadora_fica_fora_do_documento_e_da_impressao(cliente):
    html = cliente.post("/analise/laudo", data=_UM_TALHAO).get_data(as_text=True)
    documento = html[html.index('<article class="doc">'):html.index("</article>")]

    assert "data-custo" not in documento
    assert re.search(r'<section class="painel custo nao-imprime"', html)


def test_a_versao_impressa_nao_tem_calculadora(cliente):
    html = cliente.post(
        "/analise/laudo", data=dict(_UM_TALHAO, formato="impressa")
    ).get_data(as_text=True)

    assert "data-custo" not in html
    assert "js/custo.js" not in html


def test_o_script_nao_guarda_precos_nem_traz_teor():
    from pathlib import Path

    codigo = (Path(__file__).parent.parent.parent / "siras" / "web" / "static" / "js"
              / "custo.js").read_text(encoding="utf-8")

    assert "localStorage" not in codigo and "sessionStorage" not in codigo
    assert 'currency: "BRL"' in codigo
    # O critério do autor: a maior das duas quantidades, nunca a média nem uma só.
    assert "Math.max(paraP, paraK)" in codigo
    # A mais barata só entre as que atendem e têm custo completo.
    assert "atendeTudo && custoCompleto" in codigo
