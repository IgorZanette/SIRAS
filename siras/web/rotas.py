"""Rotas do SIRAS.

Mapa previsto (PLANO-FRONTEND §9.1), implementado por etapas:

    /                  landing                        — pronto
    /analise           etapa 1, escolha da cultura    — pronto
    /analise/dados     etapa 2, análise de solo       — pronto
    /analise/laudo     etapa 3, laudo                 — pronto
    /api/interpretar   POST, leitura ao vivo          — pronto
    /tabelas           as tabelas transcritas         — pronto

As rotas montam AnaliseSolo e Contexto a partir do formulário e chamam gerar_laudo().
Nenhuma interpretação acontece aqui nem em JavaScript: fonte única de verdade é o motor
Python (PLANO-FRONTEND §9.4, opção B).
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from siras.conhecimento.carregador import carregar_dados_comum, carregar_dados_graos
from siras.dominio.escopo import (
    TOTAL_DE_CULTURAS_NO_ESCOPO,
    no_escopo_de_recomendacao,
)
from siras.motor.laudo import dados_do_grupo
from siras.motor.adubacao import ErroAdubacao
from siras.motor.aptidao import ErroAptidao
from siras.motor.calagem import ErroCalagem
from siras.motor.laudo import ErroLaudo, gerar_laudo
from siras.motor.leitura import interpretar_parcial
from siras.relatorio import tabelas as tabelas_do_manual
from siras.relatorio.apresentacao import (
    apresentar_laudo,
    apresentar_leitura,
    nome_de_exibicao,
)
from siras.web import exemplo as exemplo_de_formulario
from siras.web import formulario

bp = Blueprint("siras", __name__)

def _opcoes_do_formulario(cultura_id: str) -> Dict[str, Any]:
    """Tudo que a tela de dados oferece sai da base de conhecimento.

    Nenhuma lista de cultura, de manejo, de antecedente ou de variável condicional é
    escrita no template: se a base ganhar uma cultura, a tela ganha junto, e se perder, a
    tela não oferece uma opção que o motor recusaria.
    """
    dados = carregar_dados_comum()
    dados_graos = carregar_dados_graos()
    grupo = formulario.grupo_da_cultura(cultura_id, dados)
    return {
        "dados": dados,
        "cultura_id": cultura_id,
        "cultura_nome": nome_de_exibicao(cultura_id, dados) if cultura_id else "",
        "grupo": grupo,
        "manejos": formulario.opcoes_de_manejo(dados, grupo),
        "antecedentes": formulario.antecedentes_disponiveis(dados_graos) if grupo == "graos" else [],
        "culturas_com_antecedente": (
            formulario.culturas_que_exigem_antecedente(dados_graos, dados)
            if grupo == "graos" else []
        ),
        "variaveis": formulario.variaveis_condicionais(
            cultura_id, grupo, dados_do_grupo(grupo)
        ),
        "faixas": formulario.FAIXA_DO_CAMPO,
        "campos_acidez": formulario.CAMPOS_ACIDEZ,
        "campos_fertilidade": formulario.CAMPOS_FERTILIDADE,
        "campos_subsuperficie": formulario.CAMPOS_SUBSUPERFICIE,
        "campos_contexto": formulario.CAMPOS_CONTEXTO,
    }


def _tela_de_dados(cultura_id: str, leitura=None, erro_do_motor: str = None,
                   com_exemplo: bool = False):
    opcoes = _opcoes_do_formulario(cultura_id)
    leitura = leitura or formulario.LeituraFormulario()
    if com_exemplo and not leitura.valores:
        leitura.valores = exemplo_de_formulario.montar(
            cultura_id, opcoes["grupo"], opcoes["dados"],
            opcoes["manejos"], opcoes["variaveis"],
            dados_do_grupo(opcoes["grupo"]),
        )
    return render_template(
        "dados.html",
        leitura=leitura,
        erro_do_motor=erro_do_motor,
        **opcoes,
    )


@bp.get("/")
def inicio():
    """Landing. O total de culturas vem de siras/dominio/escopo.py, e não escrito no
    template: número de vitrine que diverge do escopo real é o tipo de erro que só
    aparece quando alguém da banca conta."""
    return render_template("inicio.html", total_de_culturas=TOTAL_DE_CULTURAS_NO_ESCOPO)


@bp.get("/tabelas")
def tabelas():
    """As tabelas do Manual como o SIRAS as transcreveu.

    Serve à conferência — quem desconfiar de uma dose abre a tabela que a produziu sem
    sair do sistema — e ao valor didático que o plano atribui à leitura ao vivo (§9.3):
    ver a estrutura da tabela converte a ferramenta de caixa-preta em material de estudo.
    """
    return render_template("tabelas.html", catalogo=tabelas_do_manual.CATALOGO)


@bp.get("/tabelas/<identificador>")
def tabela(identificador: str):
    construida = tabelas_do_manual.construir(identificador, carregar_dados_comum())
    if construida is None:
        return redirect(url_for("siras.tabelas"))
    return render_template("tabela.html", tabela=construida)


@bp.get("/analise")
def cultura():
    """Etapa 1. A cultura precede a análise porque define o critério de calagem, o grupo
    de exigência em P e K e quais campos condicionais existem (PLANO-FRONTEND §9.1)."""
    return render_template(
        "cultura.html", grupos=formulario.grupos_com_culturas(carregar_dados_comum())
    )


@bp.get("/analise/dados")
def dados():
    """Sem cultura escolhida não há formulário a montar: quais campos existem depende
    dela. Volta para a etapa 1 em vez de exibir uma tela pela metade."""
    cultura_id = (request.args.get("cultura_id") or "").strip()
    dados_comuns = carregar_dados_comum()
    if (
        not cultura_id
        or not formulario.grupo_da_cultura(cultura_id, dados_comuns)
        or not no_escopo_de_recomendacao(cultura_id)
    ):
        # Espécie florestal está mapeada para a aptidão e fora do escopo de recomendação
        # (docs/decisoes/0006): o formulário de recomendação não abre para ela.
        return redirect(url_for("siras.cultura"))
    return _tela_de_dados(cultura_id, com_exemplo=bool(request.args.get("exemplo")))


@bp.get("/analise/laudo")
def laudo_sem_dados():
    """O laudo nasce de um POST. Chegar aqui por link ou recarga volta ao formulário em
    vez de mostrar uma página de erro sobre um método HTTP."""
    return redirect(url_for("siras.dados"))


@bp.post("/api/interpretar")
def interpretar():
    """Leitura ao vivo: interpreta o que já foi digitado (PLANO-FRONTEND §9.3 e §9.4).

    Opção B da §9.4: a interpretação roda no mesmo motor Python que os casos de teste
    validam. A opção A — reimplementar a classificação em JavaScript — pareceria mais
    simples e criaria uma segunda implementação não testada da regra que a hipótese H1.1
    mede.

    Devolve a marcação já renderizada pelo Jinja, e não dados para o JS montar: assim a
    régua e a ficha do painel são literalmente os mesmos componentes do laudo.
    """
    payload = request.get_json(silent=True) or {}
    dados_comuns = carregar_dados_comum()

    campos = {
        nome: formulario.para_numero(valor)
        for nome, valor in payload.items()
        if nome not in ("cultura_id", "criterio_id")
    }
    cultura_id = (payload.get("cultura_id") or "").strip()
    criterio_id = (payload.get("criterio_id") or "").strip() or None
    grupo = dados_comuns["mapa_culturas"]["culturas"].get(cultura_id, {}).get("grupo", "")

    leitura = interpretar_parcial(
        campos,
        cultura_id=cultura_id,
        grupo=grupo,
        criterio_id=criterio_id,
        prnt=campos.get("prnt"),
        profundidade_incorporacao_cm=campos.get("profundidade_incorporacao_cm") or 20.0,
        dados=dados_comuns,
    )
    linhas = apresentar_leitura(leitura)

    return jsonify({
        "html": render_template("_parciais/leitura.html", linhas=linhas),
        # Estruturado ao lado do HTML para que os testes afirmem sobre a classe, e não
        # sobre marcação — asserção em HTML quebra a cada ajuste de layout.
        "classes": {
            "p": (leitura.get("fosforo") or {}).get("classe"),
            "k": (leitura.get("potassio") or {}).get("classe"),
        },
    })


@bp.post("/analise/laudo")
def laudo():
    dados_comuns = carregar_dados_comum()
    cultura_id = (request.form.get("cultura_id") or "").strip()
    grupo = formulario.grupo_da_cultura(cultura_id, dados_comuns)
    leitura = formulario.ler(request.form, dados_comuns, dados_do_grupo(grupo))

    if not leitura.ok:
        return _tela_de_dados(cultura_id, leitura), 422

    try:
        resultado = gerar_laudo(leitura.analise, leitura.contexto.cultura_id, leitura.contexto)
    except (ErroLaudo, ErroCalagem, ErroAdubacao, ErroAptidao) as erro:
        # Erro de escopo ou de base incompleta, não de digitação: o formulário volta
        # preenchido e a mensagem do motor aparece inteira, sem tradução que a apague.
        return _tela_de_dados(cultura_id, leitura, erro_do_motor=str(erro)), 422

    return render_template("laudo.html", laudo=apresentar_laudo(resultado, dados_comuns))
