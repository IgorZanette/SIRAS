"""
Análise de vários talhões num laudo só.

Uma propriedade raramente é uma amostra só. O que se repete a cada talhão é apenas a
análise de solo: cultura, sistema de manejo, PRNT, cultivo e antecedente são preenchidos
uma vez e valem para todas as áreas.

O que estes testes guardam, acima de tudo, é que a análise de UMA área continuou sendo
exatamente o que era. O primeiro talhão mantém os nomes de campo originais e só do
segundo em diante vem o sufixo "__N" — se isso se perder, quebram juntos a leitura ao
vivo, o preenchimento por exemplo e a volta do laudo para a edição.
"""

import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from siras.relatorio.apresentacao import consolidar_por_area
from siras.web import criar_app

_ESTATICOS = Path(__file__).parent.parent.parent / "siras" / "web" / "static"

_UM_TALHAO = {
    "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
    "profundidade_incorporacao_cm": "20", "prnt": "100", "expectativa_rendimento": "3",
    "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
    "p": "11", "k": "96", "ctc_ph7": "9.4",
    "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
}

#: Uma segunda amostra deliberadamente diferente da primeira: mais arenosa, menos ácida e
#: mais pobre em fósforo. Serve para que duas recomendações iguais denunciem que o
#: segundo talhão não foi lido de verdade.
_SEGUNDA_AMOSTRA = {
    "ph_agua": "5.8", "indice_smp": "6.0", "argila": "24", "mo": "1.9",
    "p": "4.2", "k": "54", "ctc_ph7": "6.1",
    "al": "0.3", "ca": "3.1", "mg": "1.4", "v_percent": "61",
}


def _dois_talhoes(**extra):
    dados = dict(_UM_TALHAO, talhao="A1")
    dados["talhao__2"] = "B2"
    dados.update({campo + "__2": valor for campo, valor in _SEGUNDA_AMOSTRA.items()})
    dados.update(extra)
    return dados


def _laudo_falso(nc=2.0, n=30.0, p2o5=40.0, k2o=50.0):
    return SimpleNamespace(
        calagem=SimpleNamespace(nc_t_ha=nc),
        adubacao=SimpleNamespace(n=n, p2o5=p2o5, k2o=k2o),
    )


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


# --- a análise de uma área não mudou -------------------------------------------

def test_um_talhao_continua_sem_cabecalho_de_talhao(cliente):
    """Com uma área só, o documento é exatamente o que sempre foi."""
    html = cliente.post("/analise/laudo", data=_UM_TALHAO).get_data(as_text=True)

    assert 'class="talhao"' not in html
    assert "Quantidade total a comprar" not in html
    assert "Laudo de recomendação" in html


def test_o_primeiro_talhao_nao_usa_sufixo(cliente):
    """É o que faz a leitura ao vivo, o exemplo e a volta à edição seguirem funcionando
    sem saber que talhões múltiplos existem."""
    tela = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert 'id="ph_agua"' in tela
    assert 'id="ph_agua__1"' not in tela


# --- várias áreas ---------------------------------------------------------------

def test_cada_talhao_recebe_a_sua_recomendacao(cliente):
    resposta = cliente.post("/analise/laudo", data=_dois_talhoes())
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert "Talhão 1 de 2" in html and "Talhão 2 de 2" in html
    assert ">A1<" in html and ">B2<" in html


def test_as_duas_amostras_sao_mesmo_interpretadas(cliente):
    """Duas recomendações idênticas para amostras diferentes denunciariam que o segundo
    talhão foi ignorado e o primeiro repetido."""
    html = cliente.post("/analise/laudo", data=_dois_talhoes()).get_data(as_text=True)

    fosforos = re.findall(
        r'linha__nome">Fósforo</span>\s*<span class="linha__val">([^<]+)<', html
    )
    assert len(fosforos) == 2, "esperava dois blocos de atributos, achei %d" % len(fosforos)
    assert fosforos[0].startswith("11,0") and fosforos[1].startswith("4,2"), fosforos


def test_o_nome_do_talhao_passa_a_ser_obrigatorio(cliente):
    """Um laudo que traz várias recomendações e não diz a qual área cada uma pertence é
    pior que não trazê-las."""
    resposta = cliente.post("/analise/laudo", data=_dois_talhoes(talhao=""))
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 422
    assert "Nome do talhão 1" in html


def test_o_erro_de_um_talhao_diz_de_qual_talhao_e(cliente):
    """Num formulário com quatro áreas, 'falta o fósforo' sem dizer de qual delas não
    ajuda ninguém."""
    dados = _dois_talhoes()
    dados["p__2"] = ""
    html = cliente.post("/analise/laudo", data=dados).get_data(as_text=True)

    assert "Fósforo (talhão B2)" in html


# --- quantidade total a comprar -------------------------------------------------

def test_sem_todas_as_areas_nao_ha_total(cliente):
    """Somar sobre um conjunto incompleto daria um número que parece o total da
    propriedade e não é."""
    html = cliente.post(
        "/analise/laudo", data=_dois_talhoes(area_ha="12,5")
    ).get_data(as_text=True)

    assert "Quantidade total a comprar" not in html


def test_com_todas_as_areas_o_laudo_soma_a_compra(cliente):
    dados = _dois_talhoes(area_ha="12,5")
    dados["area_ha__2"] = "8"
    html = cliente.post("/analise/laudo", data=dados).get_data(as_text=True)

    assert "Quantidade total a comprar" in html
    assert "20,5 ha" in html


def test_o_total_e_dose_vezes_area_e_nada_mais():
    """Não há critério agronômico na consolidação: é aritmética sobre a saída do motor."""
    laudo = _laudo_falso()
    total = consolidar_por_area([
        SimpleNamespace(rotulo="A", area_ha=10.0, laudo=laudo),
        SimpleNamespace(rotulo="B", area_ha=5.0, laudo=laudo),
    ])

    assert total["area_total"] == "15,0"
    assert total["itens"][0] == {"nome": "Calcário", "quantidade": "30,0", "unidade": "t"}
    assert total["sem_total"] == []


def test_dose_sem_numero_fica_de_fora_do_total_e_o_laudo_diz():
    """O Manual nem sempre publica um número: há teto e intervalo. Multiplicá-los por
    área daria uma quantidade com precisão que a fonte não dá."""
    laudo = _laudo_falso(p2o5={"valor": 45.0, "qualificador": "ate"})

    total = consolidar_por_area([SimpleNamespace(rotulo="A", area_ha=10.0, laudo=laudo)])

    assert any("Fósforo" in nome for nome in total["sem_total"])
    assert all("Fósforo" not in item["nome"] for item in total["itens"])


def test_area_faltando_em_um_bloco_zera_o_total():
    laudo = _laudo_falso()

    assert consolidar_por_area([
        SimpleNamespace(rotulo="A", area_ha=10.0, laudo=laudo),
        SimpleNamespace(rotulo="B", area_ha=None, laudo=laudo),
    ]) is None


# --- a volta do laudo para a edição ---------------------------------------------

def test_editar_traz_de_volta_todos_os_talhoes(cliente):
    """Perder o segundo talhão ao corrigir um número do primeiro apagaria metade do
    trabalho."""
    dados = _dois_talhoes(area_ha="12,5")
    dados["area_ha__2"] = "8"
    laudo = cliente.post("/analise/laudo", data=dados).get_data(as_text=True)
    ocultos = dict(
        re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">', laudo)
    )

    assert "talhao__2" in ocultos and "ph_agua__2" in ocultos

    tela = cliente.post("/analise/dados", data=ocultos).get_data(as_text=True)

    assert 'data-talhao="2"' in tela
    assert 'value="B2"' in tela
    assert re.search(r'id="ph_agua__2"[^>]*value="5.8"', tela)


def test_o_formulario_traz_o_molde_e_o_botao(cliente):
    tela = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert "data-adicionar-talhao" in tela
    assert 'id="molde-talhao"' in tela
    assert "__IDX__" in tela, "o molde precisa da marca que o JavaScript troca"


def test_sem_javascript_a_analise_de_um_talhao_funciona_inteira(cliente):
    """O bloco de talhões é acréscimo, não requisito: sem JavaScript ele apenas não ganha
    cartões."""
    codigo = (_ESTATICOS / "js" / "talhoes.js").read_text(encoding="utf-8")

    assert "molde-talhao" in codigo
    assert "__IDX__" in codigo
    assert cliente.post("/analise/laudo", data=_UM_TALHAO).status_code == 200


def test_o_indice_do_campo_nunca_e_reaproveitado():
    """Reaproveitar o índice de um talhão removido misturaria os valores de um campo com
    os do que acabou de sair, se o navegador tivesse restaurado algum."""
    codigo = (_ESTATICOS / "js" / "talhoes.js").read_text(encoding="utf-8")

    assert "maiorIndice() + 1" in codigo
