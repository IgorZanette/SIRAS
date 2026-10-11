"""
O estado do projeto que a tela inicial mostra (siras/dominio/estado.py).

A seção existe porque, para uma banca, o percurso vale tanto quanto o produto. E ela
só vale enquanto for verdade: uma página que afirma "concluído" sobre o que não está
custa mais credibilidade do que a seção inteira entrega.

Daí estes testes. O que eles protegem não é formatação — é a **sincronia** entre o
que a página afirma e o que `docs/processo/roadmap.md` registra. Escrito no template,
isso divergiria na primeira semana; aqui, divergir reprova a suíte.
"""

import re
from pathlib import Path

import pytest

from siras.dominio.estado import ETAPAS, ROTULO_DA_SITUACAO, SELO_DE_NATUREZA

_ROADMAP = (Path(__file__).parent.parent.parent / "docs" / "processo" / "roadmap.md")


@pytest.fixture(scope="module")
def roadmap() -> str:
    return _ROADMAP.read_text(encoding="utf-8").lower()


class TestSincroniaComORoadmap:
    @pytest.mark.parametrize("etapa", ETAPAS, ids=lambda e: e.nome)
    def test_cada_etapa_da_tela_existe_no_roadmap(self, etapa, roadmap):
        """O nome da etapa precisa aparecer no roadmap, com estas palavras.

        Não é rigor de redação: é o que garante que alguém que renomeie uma etapa no
        roadmap seja obrigado a olhar a tela, e vice-versa."""
        assert etapa.nome.lower() in roadmap, (
            f"'{etapa.nome}' aparece na tela inicial e não no roadmap — "
            f"uma das duas fontes está desatualizada"
        )

    def test_nada_em_andamento_depois_de_algo_proximo(self):
        """A ordem precisa ser a do percurso: concluído, depois em andamento, depois
        próximo. Uma etapa 'em andamento' listada abaixo de uma 'próxima' confundiria
        quem lê a página de cima para baixo."""
        ordem = {"concluido": 0, "andamento": 1, "proximo": 2}
        valores = [ordem[e.situacao] for e in ETAPAS]
        assert valores == sorted(valores), [e.nome for e in ETAPAS]


class TestHonestidade:
    @pytest.mark.parametrize("etapa", ETAPAS, ids=lambda e: e.nome)
    def test_nenhuma_descricao_promete_numero_que_a_pagina_nao_mostra(self, etapa):
        """A regra da tela inicial (ver o comentário no topo de inicio.html) proíbe
        benefício com número inventado. Percentual de produtividade e valor em reais
        não entram aqui — nem como ilustração."""
        proibidos = (r"\d+\s*%\s*(a mais|de aumento|de ganho)", r"R\$", r"reais")
        for padrao in proibidos:
            assert not re.search(padrao, etapa.descricao, re.I), (
                f"'{etapa.nome}' promete algo que a página não pode sustentar"
            )

    def test_o_selo_diz_que_o_trabalho_esta_em_desenvolvimento(self):
        """Um TCC que se apresenta como produto acabado perde mais do que ganha."""
        assert "desenvolvimento" in SELO_DE_NATUREZA.lower()

    def test_toda_situacao_tem_rotulo_e_icone(self):
        for etapa in ETAPAS:
            assert etapa.situacao in ROTULO_DA_SITUACAO, etapa.nome
            rotulo, icone = ROTULO_DA_SITUACAO[etapa.situacao]
            assert rotulo and icone


class TestNaTela:
    def test_a_secao_aparece_na_tela_inicial(self):
        from siras.web import criar_app

        html = criar_app({"TESTING": True}).test_client().get("/").get_data(as_text=True)

        assert "Em que pé está o trabalho" in html
        for etapa in ETAPAS:
            assert etapa.nome in html, etapa.nome
        assert SELO_DE_NATUREZA in html

    def test_a_tela_nao_escreve_as_etapas_a_mao(self):
        """Se alguém escrever uma etapa direto no template, ela passa a divergir do
        roadmap sem que nada reprove. O laço é a garantia de fonte única."""
        template = (
            Path(__file__).parent.parent.parent
            / "siras" / "web" / "templates" / "inicio.html"
        ).read_text(encoding="utf-8")
        bloco = re.search(
            r'id="titulo-estado".*?</section>', template, re.S
        ).group(0)

        assert "{% for etapa in etapas_do_projeto %}" in bloco
        for etapa in ETAPAS:
            assert etapa.nome not in bloco, (
                f"'{etapa.nome}' está escrito no template, e deveria vir de estado.py"
            )
