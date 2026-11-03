"""
Acentuação do texto que a base traz sem acento, só na exibição.

A base foi transcrita sem acentos, e parte dela é chave: o motor compara a condição da
área, e o formulário devolve o identificador da cultura e do antecedente. Por isso a base
não é reescrita — `texto_pt()` acentua na hora de mostrar. Estes testes travam os dois
lados: o texto que o usuário lê sai certo, e nenhum identificador é tocado.
"""

import re

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.relatorio.apresentacao import _ACENTOS, nome_de_exibicao, texto_pt
from siras.relatorio.tabelas import CATALOGO, construir
from siras.web import criar_app
from siras.web.formulario import GRUPOS, opcoes_de_manejo

SEM_ACENTO = re.compile(r"\b(" + "|".join(_ACENTOS) + r")\b", re.IGNORECASE)


@pytest.mark.parametrize("entrada, esperado", [
    ("calcario dolomitico", "calcário dolomítico"),
    ("Feijao", "Feijão"),
    ("NAO aplicar", "NÃO aplicar"),
    ("consolidado, sem restricoes na camada 10-20 cm", "consolidado, sem restrições na camada 10-20 cm"),
    ("O pH de referencia NAO e suficiente", "O pH de referência NÃO é suficiente"),
    ("arroz pre-germinado", "arroz pré-germinado"),
    ("Nogueira peca", "Nogueira-pecã"),
])
def test_acentua_o_texto_de_leitura(entrada, esperado):
    assert texto_pt(entrada) == esperado


@pytest.mark.parametrize("identificador", [
    "interpretacao_geral.json", "graos_pd_consolidado", "consorciacao_ou_pousio", "cana_de_acucar",
])
def test_nao_toca_identificador(identificador):
    """O limite de palavra não atravessa '_': nome de arquivo e id passam intactos."""
    assert texto_pt(identificador) == identificador


def test_ambiguos_ficam_como_estao_fora_das_frases_conferidas():
    """'e', 'ha' (hectare) e 'esta' não são adivinhados: só frases exatas são corrigidas."""
    assert texto_pt("2 t/ha e 3 t/ha") == "2 t/ha e 3 t/ha"
    assert texto_pt("esta cultura") == "esta cultura"


def test_nenhuma_tabela_mostra_palavra_sem_acento():
    dados = carregar_dados_comum()
    for item in CATALOGO:
        t = construir(item["id"], dados)
        textos = [t.titulo, t.descricao, t.aviso or "", *t.notas,
                  *(celula for linha in t.linhas for celula in linha)]
        for texto in textos:
            assert not SEM_ACENTO.search(texto), f"{item['id']}: {texto!r}"


def test_nomes_de_cultura_e_opcoes_de_manejo_saem_acentuados():
    dados = carregar_dados_comum()
    for cultura_id in dados["mapa_culturas"]["culturas"]:
        nome = nome_de_exibicao(cultura_id, dados)
        assert not SEM_ACENTO.search(nome), f"{cultura_id}: {nome!r}"
    for grupo, *_ in GRUPOS:
        for _, rotulo in opcoes_de_manejo(dados, grupo):
            assert not SEM_ACENTO.search(rotulo), rotulo


def test_o_formulario_continua_devolvendo_o_identificador_cru():
    """O rótulo é acentuado; o valor enviado ao servidor não. Se o value virasse
    'feijão', o motor não acharia a cultura."""
    cliente = criar_app({"TESTING": True}).test_client()
    html = cliente.get("/analise/dados?cultura_id=feijao").get_data(as_text=True)
    assert 'value="feijao"' in html
    assert "Feijão" in html
