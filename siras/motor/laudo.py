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

Escopo: os seis grupos do escopo de recomendação. Grãos têm caminho próprio porque são a
exceção do Manual — publicam correção e manutenção em separado, com algoritmo de dose por
cultivo; os outros cinco publicam a dose pronta por classe de teor e compartilham um
despacho só, parametrizado pelas variáveis condicionais que cada um exige.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from siras.conhecimento.carregador import (
    carregar_dados_comum,
    carregar_dados_erva_mate,
    carregar_dados_frutiferas,
    carregar_dados_graos,
    carregar_dados_hortalicas,
    carregar_dados_outras,
    carregar_dados_tuberculos,
)
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.dominio.laudo import Laudo, RecomendacaoAdubacao, RecomendacaoCalagem
from siras.dominio.nomes import buscar_por_nome
from siras.motor.adubacao import (
    calcular_adubacao_erva_mate,
    calcular_adubacao_frutiferas,
    calcular_adubacao_hortalicas,
    calcular_adubacao_outras,
    calcular_adubacao_tuberculos,
    calcular_fosforo_potassio,
    calcular_nitrogenio,
    classificar_fosforo,
    classificar_potassio,
)
from siras.motor.aptidao import avaliar_aptidao
from siras.motor.calagem import calcular_calagem, resolver_criterio_id
from siras.motor.trace import Trace

#: Carregador da adubação de cada grupo.
_CARREGADOR_POR_GRUPO = {
    "graos": carregar_dados_graos,
    "hortalicas": carregar_dados_hortalicas,
    "tuberculos": carregar_dados_tuberculos,
    "outras": carregar_dados_outras,
    "frutiferas": carregar_dados_frutiferas,
    "erva_mate": carregar_dados_erva_mate,
}

#: Grupos de mapa_culturas.json que gerar_laudo() sabe adubar.
_GRUPOS_IMPLEMENTADOS = (
    "graos", "hortalicas", "tuberculos", "outras", "frutiferas", "erva_mate",
)


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


def _adubacao_de_grupo_publicado(
    calcular,
    carregar,
    chave_dados: str,
    extras_permitidos: Tuple[str, ...],
    obrigatorias: Tuple[str, ...] = (),
):
    """Monta o despacho de um grupo cuja adubação já vem publicada por classe de teor.

    Grãos são a exceção do Manual: publicam correção e manutenção em separado, com um
    algoritmo de dose por cultivo. Os outros cinco grupos publicam a dose pronta por
    classe, e por isso cabem num despacho só — o que varia entre eles é a lista de
    variáveis condicionais que a função da cultura exige (fase, ciclo, tipo, programa),
    e isso vem de Contexto.variaveis.
    """

    def despachar(
        analise: AnaliseSolo,
        cultura_id: str,
        contexto: Contexto,
        trace: Trace,
        dados: Dict[str, Any],
    ) -> RecomendacaoAdubacao:
        dados_grupo = carregar()
        extras = {
            nome: valor
            for nome, valor in contexto.variaveis.items()
            if nome in extras_permitidos and valor is not None
        }
        # Sem isto, a variável condicional ausente estoura como TypeError de argumento
        # posicional — mensagem de interpretador Python chegando ao técnico em campo.
        faltando = [nome for nome in obrigatorias if nome not in extras]
        if faltando:
            raise ErroLaudo(
                f"cultura '{cultura_id}': informe {', '.join(faltando)} — "
                f"o Manual publica recomendações distintas por {', '.join(faltando)} "
                f"para este grupo"
            )
        resultado = calcular(
            cultura_id,
            mo=analise.mo,
            argila=analise.argila,
            p_solo=analise.p,
            k_solo=analise.k,
            ctc_ph7=analise.ctc_ph7,
            dados_comuns=dados,
            **{chave_dados: dados_grupo},
            **extras,
        )
        return _montar_adubacao(analise, cultura_id, contexto, trace, dados, dados_grupo, resultado)

    return despachar


def _faixas_da_classe(
    analise: AnaliseSolo, cultura_id: str, dados_grupo: Dict[str, Any], dados: Dict[str, Any],
    resultado: Dict[str, Any],
) -> Tuple[list, list]:
    """Recupera as faixas que classificaram P e K, para a régua do laudo.

    As funções dos cinco grupos publicados devolvem a classe, não a faixa. Em vez de
    reclassificar por fora, esta função repete a MESMA seleção com o grupo de exigência
    declarado na cultura e confere que a classe encontrada bate com a que a adubação
    usou. Se divergirem, é erro de dado ou de resolução de grupo, e é melhor estourar
    aqui do que desenhar uma régua apontando para outra faixa.
    """
    entrada = buscar_por_nome(dados_grupo["adubacao"].get("culturas", {}), cultura_id) or {}
    declarado = entrada.get("grupo_exigencia")
    if not declarado:
        return [], []

    leitura_p = classificar_fosforo(f"grupo_{declarado['p']}", analise.argila, analise.p, dados)
    leitura_k = classificar_potassio(f"grupo_{declarado['k']}", analise.ctc_ph7, analise.k, dados)

    faixas = {"classe_p": [], "classe_k": []}
    for eixo, leitura in (("classe_p", leitura_p), ("classe_k", leitura_k)):
        classe_usada = resultado.get(eixo)
        # Classe ausente não é divergência: há fases que não dosam pela classe de teor
        # (frutífera em crescimento dosa N pela MO e pelo ano, por exemplo). Sem classe
        # não há régua a desenhar, e afirmar uma seria inventar leitura.
        if classe_usada is None:
            continue
        if classe_usada != leitura["classe"]:
            raise ErroLaudo(
                f"cultura '{cultura_id}': a adubação classificou {eixo}="
                f"'{classe_usada}' e a releitura das faixas deu '{leitura['classe']}' "
                f"— grupo de exigência divergente entre as duas leituras"
            )
        faixas[eixo] = leitura["faixas"]
    return faixas["classe_p"], faixas["classe_k"]


def _montar_adubacao(
    analise: AnaliseSolo,
    cultura_id: str,
    contexto: Contexto,
    trace: Trace,
    dados: Dict[str, Any],
    dados_grupo: Dict[str, Any],
    resultado: Dict[str, Any],
) -> RecomendacaoAdubacao:
    faixas_p, faixas_k = _faixas_da_classe(analise, cultura_id, dados_grupo, dados, resultado)

    trace.registrar(
        regra="R-ADU-01: classificação do teor de P (por classe de argila) e de K (por CTC a pH 7,0)",
        entradas={
            "argila": analise.argila, "p": analise.p,
            "ctc_ph7": analise.ctc_ph7, "k": analise.k,
        },
        saida={"classe_p": resultado.get("classe_p"), "classe_k": resultado.get("classe_k")},
        fonte=(
            f"{_fonte_legivel(dados['interpretacao_p']['fonte'])} (P) e "
            f"{_fonte_legivel(dados['interpretacao_k']['fonte'])} (K)"
        ),
    )
    trace.registrar(
        regra="R-ADU-04: dose de N, P2O5 e K2O publicada por classe de teor e faixa de MO",
        entradas={
            "cultura_id": cultura_id, "mo": analise.mo,
            "variaveis_condicionais": dict(contexto.variaveis),
        },
        saida={
            "n": resultado.get("n"), "p2o5": resultado.get("p2o5"), "k2o": resultado.get("k2o"),
        },
        fonte=_fonte_legivel(dados_grupo["adubacao"]["fonte"]),
    )

    return RecomendacaoAdubacao(
        n=resultado.get("n"),
        p2o5=resultado.get("p2o5"),
        k2o=resultado.get("k2o"),
        classe_p=resultado.get("classe_p"),
        classe_k=resultado.get("classe_k"),
        motivo_n=resultado.get("motivo_n"),
        faixas_p=faixas_p,
        faixas_k=faixas_k,
    )


def _adubacao_erva_mate(
    analise: AnaliseSolo, cultura_id: str, contexto: Contexto, trace: Trace, dados: Dict[str, Any]
) -> RecomendacaoAdubacao:
    """Erva-mate não recebe cultura_id: a tabela é indexada por programa e fase, e a
    espécie é uma só (Seção 6.6.5)."""
    dados_grupo = carregar_dados_erva_mate()
    programa = contexto.variaveis.get("programa")
    if not programa:
        raise ErroLaudo(
            "erva-mate: informe o programa de adubação ('desde_o_plantio' ou 'recuperacao')"
        )
    extras = {
        nome: valor
        for nome, valor in contexto.variaveis.items()
        if nome in ("fase", "momento", "manejo_galho_grosso", "massa_verde_t_ha")
        and valor is not None
    }
    resultado = calcular_adubacao_erva_mate(
        programa,
        mo=analise.mo, argila=analise.argila, p_solo=analise.p,
        k_solo=analise.k, ctc_ph7=analise.ctc_ph7,
        dados_erva_mate=dados_grupo, dados_comuns=dados,
        **extras,
    )
    return _montar_adubacao(analise, cultura_id, contexto, trace, dados, dados_grupo, resultado)


_ADUBACAO_POR_GRUPO = {
    "graos": _adubacao_graos,
    "hortalicas": _adubacao_de_grupo_publicado(
        calcular_adubacao_hortalicas, carregar_dados_hortalicas, "dados_hortalicas",
        ("expectativa_rendimento", "fase", "fase_n", "fase_pk"),
    ),
    "tuberculos": _adubacao_de_grupo_publicado(
        calcular_adubacao_tuberculos, carregar_dados_tuberculos, "dados_tuberculos",
        ("expectativa_rendimento",),
    ),
    "outras": _adubacao_de_grupo_publicado(
        calcular_adubacao_outras, carregar_dados_outras, "dados_outras",
        ("ciclo", "tipo", "produtividade_t_ha"),
    ),
    "frutiferas": _adubacao_de_grupo_publicado(
        calcular_adubacao_frutiferas, carregar_dados_frutiferas, "dados_frutiferas",
        ("fase", "ano", "produtividade_estimada", "tipo_uva", "analise_de_tecido",
         "ano_de_alternancia"),
        obrigatorias=("fase",),
    ),
    "erva_mate": _adubacao_erva_mate,
}


def dados_do_grupo(grupo: str) -> Optional[Dict[str, Any]]:
    """Culturas transcritas na adubação de um grupo, ou None quando o grupo não as
    indexa por cultura (erva-mate indexa por programa e fase)."""
    carregar = _CARREGADOR_POR_GRUPO.get(grupo)
    if carregar is None:
        return None
    carregado = carregar()
    # Grãos são o único grupo com dois arquivos (N e PK) em vez de um: o de N é o que
    # lista as culturas.
    bloco = carregado.get("adubacao") or carregado.get("adubacao_n") or {}
    return bloco.get("culturas")


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
