"""
Ponto de entrada único do motor: gerar_laudo().

Orquestra, sem decidir nada por conta própria, as três saídas do SIRAS para uma análise
de solo:

    calagem   -> motor/calagem.py   (critério de grupo -> Tab. 5.2 -> PRNT)
    adubação  -> motor/adubacao.py  (classe de teor + expectativa -> N, P2O5, K2O)
    aptidão   -> motor/aptidao.py   (CCAE, cenários ATUAL e POTENCIAL)

Toda regra agronômica continua nos três módulos; aqui só existe despacho por grupo de
cultura, montagem do Laudo e registro no Trace dos passos que os módulos de adubação não
registram sozinhos (eles não recebem Trace — ver _registrar_adubacao_no_trace).

Escopo implementado: grupo 'graos' (docs/ROADMAP.md, S2/M1). Os demais grupos já têm
motor de adubação pronto, mas dados/comum/mapa_culturas.json ainda não os mapeia, e sem
esse mapeamento a calagem não resolve o critério — ver ErroLaudo em _resolver_grupo().
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from siras.conhecimento.carregador import carregar_dados_comum, carregar_dados_graos
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.dominio.laudo import Laudo, RecomendacaoAdubacao, RecomendacaoCalagem
from siras.motor.adubacao import calcular_fosforo_potassio, calcular_nitrogenio
from siras.motor.aptidao import avaliar_aptidao
from siras.motor.calagem import calcular_calagem, resolver_criterio_id
from siras.motor.trace import Trace

#: Grupos de mapa_culturas.json que gerar_laudo() sabe adubar hoje.
_GRUPOS_IMPLEMENTADOS = ("graos",)


class ErroLaudo(Exception):
    """Cultura sem grupo mapeado, ou grupo ainda não coberto pelo orquestrador."""


def _fonte_legivel(fonte: Any) -> str:
    """Formata o bloco 'fonte' de um arquivo da base como uma linha de citação.

    Os arquivos de dados guardam a fonte ora como string pronta ("Tabela 6.1.1, p. 105"),
    ora como dict com manual/tabelas/paginas. Aqui só se reformata o que foi transcrito —
    nenhuma tabela ou página é deduzida.
    """
    if isinstance(fonte, str):
        return fonte
    if not isinstance(fonte, dict):
        return str(fonte)

    tabelas = fonte.get("tabelas") or []
    paginas = fonte.get("paginas") or []

    partes = ["Manual 2016"]
    if tabelas:
        partes.append("Tab. " + "; ".join(str(t) for t in tabelas))
    if paginas:
        menor, maior = min(paginas), max(paginas)
        partes.append(f"p. {menor}" if menor == maior else f"p. {menor}-{maior}")
    return ", ".join(partes)


def _resolver_grupo(cultura_id: str, dados: Dict[str, Any]) -> str:
    """Descobre o grupo da cultura em mapa_culturas.json e recusa o que não é suportado."""
    entrada = dados["mapa_culturas"]["culturas"].get(cultura_id)
    if entrada is None:
        raise ErroLaudo(
            f"cultura '{cultura_id}' não está em dados/comum/mapa_culturas.json — sem o "
            f"mapeamento não há como resolver o critério de calagem nem o grupo de adubação"
        )

    grupo = entrada["grupo"]
    if grupo not in _GRUPOS_IMPLEMENTADOS:
        raise ErroLaudo(
            f"cultura '{cultura_id}': grupo '{grupo}' ainda não é coberto por gerar_laudo() "
            f"(implementados: {', '.join(_GRUPOS_IMPLEMENTADOS)})"
        )
    return grupo


def _calagem(
    analise: AnaliseSolo, cultura_id: str, contexto: Contexto, trace: Trace, dados: Dict[str, Any]
) -> RecomendacaoCalagem:
    criterio_id = resolver_criterio_id(cultura_id, contexto, dados)
    resultado = calcular_calagem(analise, criterio_id, contexto, trace)
    criterio = next(
        c for c in dados["criterios_calagem"]["criterios"] if c["id"] == criterio_id
    )
    return RecomendacaoCalagem(
        nc_t_ha=resultado["nc_t_ha"],
        motivo=resultado["motivo"],
        criterio_id=criterio_id,
        criterio=criterio,
    )


def _registrar_adubacao_no_trace(
    trace: Trace,
    cultura_id: str,
    analise: AnaliseSolo,
    contexto: Contexto,
    resultado_n: Dict[str, Any],
    resultado_pk: Dict[str, Any],
    dados: Dict[str, Any],
    dados_graos: Dict[str, Any],
) -> None:
    """Registra os passos da adubação.

    As funções de motor/adubacao.py não recebem Trace — são chamadas também pelos testes
    de reprodução de tabela, onde a trilha seria ruído. Como CLAUDE.md exige que toda
    decisão do motor deixe um passo, o registro acontece aqui, na fronteira, com as
    entradas e saídas que aquelas funções receberam e devolveram. Três passos, e não um,
    porque a trilha do laudo precisa separar a classificação do teor (que responde "em que
    classe estou") do cálculo da dose (que responde "de onde vem esse número").
    """
    trace.registrar(
        regra="R-ADU-01: classificação do teor de P (por classe de argila) e de K (por CTC a pH 7,0)",
        entradas={
            "argila": analise.argila,
            "p": analise.p,
            "ctc_ph7": analise.ctc_ph7,
            "k": analise.k,
        },
        saida={"classe_p": resultado_pk["classe_p"], "classe_k": resultado_pk["classe_k"]},
        fonte=(
            f"{_fonte_legivel(dados['interpretacao_p']['fonte'])} (P) e "
            f"{_fonte_legivel(dados['interpretacao_k']['fonte'])} (K)"
        ),
    )

    trace.registrar(
        regra="R-ADU-02: dose de N pela faixa de matéria orgânica",
        entradas={
            "cultura_id": cultura_id,
            "mo": analise.mo,
            "antecedente": contexto.antecedente,
        },
        saida={
            "n": resultado_n["n"],
            "faixa_mo": resultado_n["faixa_mo"],
            "motivo": resultado_n["motivo"],
        },
        fonte=_fonte_legivel(dados_graos["adubacao_n"]["fonte"]),
    )

    trace.registrar(
        regra="R-ADU-03: dose de P2O5 e K2O por classe de teor, cultivo e expectativa de rendimento",
        entradas={
            "cultura_id": cultura_id,
            "classe_p": resultado_pk["classe_p"],
            "classe_k": resultado_pk["classe_k"],
            "cultivo": contexto.cultivo,
            "expectativa_rendimento": contexto.expectativa_rendimento,
        },
        saida={"p2o5": resultado_pk["p2o5"], "k2o": resultado_pk["k2o"]},
        fonte=_fonte_legivel(dados_graos["adubacao_pk"]["fonte"]),
    )


def _adubacao_graos(
    analise: AnaliseSolo,
    cultura_id: str,
    contexto: Contexto,
    trace: Trace,
    dados: Dict[str, Any],
) -> RecomendacaoAdubacao:
    dados_graos = carregar_dados_graos()

    resultado_n = calcular_nitrogenio(
        cultura_id,
        mo=analise.mo,
        antecedente=contexto.antecedente,
        dados_graos=dados_graos,
    )
    resultado_pk = calcular_fosforo_potassio(
        cultura_id=cultura_id,
        argila=analise.argila,
        p_solo=analise.p,
        ctc_ph7=analise.ctc_ph7,
        k_solo=analise.k,
        cultivo=contexto.cultivo,
        expectativa_rendimento=contexto.expectativa_rendimento,
        dados_comuns=dados,
        dados_graos=dados_graos,
    )

    _registrar_adubacao_no_trace(
        trace, cultura_id, analise, contexto, resultado_n, resultado_pk, dados, dados_graos
    )

    return RecomendacaoAdubacao(
        n=resultado_n["n"],
        p2o5=resultado_pk["p2o5"],
        k2o=resultado_pk["k2o"],
        classe_p=resultado_pk["classe_p"],
        classe_k=resultado_pk["classe_k"],
        faixa_mo=resultado_n["faixa_mo"],
        motivo_n=resultado_n["motivo"],
        faixas_p=resultado_pk["faixas_p"],
        faixas_k=resultado_pk["faixas_k"],
    )


_ADUBACAO_POR_GRUPO = {
    "graos": _adubacao_graos,
}


def gerar_laudo(
    analise: AnaliseSolo,
    cultura_id: str,
    contexto: Contexto,
    dados: Optional[Dict[str, Any]] = None,
) -> Laudo:
    """Gera o laudo completo de uma análise de solo para uma cultura.

    Porta de entrada única do motor (CLAUDE.md, docs/ARQUITETURA.md): a camada web, os
    testes e os scripts de validação passam por aqui, e não pelas funções de cada módulo.
    Determinística — as mesmas entradas produzem o mesmo Laudo, com a mesma trilha.

    Args:
        analise: análise de solo já validada (AnaliseSolo valida na construção)
        cultura_id: identificador da cultura, como em dados/comum/mapa_culturas.json
        contexto: contexto operacional (manejo, PRNT, cultivo, expectativa de rendimento)
        dados: base comum pré-carregada; default carrega via carregar_dados_comum()

    Returns:
        Laudo, com a trilha de inferência completa em .trace.

    Raises:
        ErroLaudo: cultura não mapeada, grupo ainda não coberto, ou cultura_id divergente
            do declarado no Contexto
        ErroCalagem / ErroAdubacao / ErroAptidao: cultura fora do escopo do SIRAS, ou dado
            inconsistente — propagam sem tradução, para não apagar a causa real
    """
    if contexto.cultura_id != cultura_id:
        # Os dois vêm do mesmo formulário; divergirem significa bug de montagem do
        # Contexto, e silenciar isso geraria um laudo com a calagem de uma cultura e a
        # adubação de outra.
        raise ErroLaudo(
            f"cultura_id '{cultura_id}' diverge de contexto.cultura_id "
            f"'{contexto.cultura_id}' — o laudo sairia misturando duas culturas"
        )

    dados = dados if dados is not None else carregar_dados_comum()
    trace = Trace()

    grupo = _resolver_grupo(cultura_id, dados)

    calagem = _calagem(analise, cultura_id, contexto, trace, dados)
    adubacao = _ADUBACAO_POR_GRUPO[grupo](analise, cultura_id, contexto, trace, dados)

    # CCAE §7: os dois cenários saem sempre juntos — a diferença entre eles é o ganho
    # atribuível à recomendação emitida acima, e é o que integra os dois módulos.
    aptidao_atual = avaliar_aptidao(analise, cultura_id, "ATUAL", contexto, trace, dados)
    aptidao_potencial = avaliar_aptidao(analise, cultura_id, "POTENCIAL", contexto, trace, dados)

    return Laudo(
        cultura_id=cultura_id,
        grupo=grupo,
        analise=analise,
        contexto=contexto,
        calagem=calagem,
        adubacao=adubacao,
        aptidao_atual=aptidao_atual,
        aptidao_potencial=aptidao_potencial,
        trace=trace,
    )


__all__ = ["ErroLaudo", "gerar_laudo"]
