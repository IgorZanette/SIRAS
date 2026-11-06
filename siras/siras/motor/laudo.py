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

import dataclasses
from typing import Any, Dict, Optional, Tuple

from siras.conhecimento.carregador import (
    carregar_dados_comum,
    carregar_dados_erva_mate,
    carregar_dados_frutiferas,
    carregar_dados_graos,
    carregar_dados_hortalicas,
    carregar_dados_outras,
    carregar_dados_tuberculos,
    carregar_formulas_npk,
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
from siras.motor.aplicacao_calcario import dados_do_grupo, regra_de_aplicacao
from siras.motor.aptidao import avaliar_aptidao
from siras.motor.calagem import calcular_calagem, resolver_criterio_id
from siras.motor.formulacao import recomendar_formulacao
from siras.motor.trace import Trace

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
    analise: AnaliseSolo, cultura_id: str, contexto: Contexto, trace: Trace,
    dados: Dict[str, Any],
) -> RecomendacaoCalagem:
    criterio_id = resolver_criterio_id(cultura_id, contexto, dados)
    resultado = calcular_calagem(analise, criterio_id, contexto, trace)
    criterio = next(
        c for c in dados["criterios_calagem"]["criterios"] if c["id"] == criterio_id
    )

    # R-CAL-04: o modo de aplicação pela situação da cultura. A DOSE não muda -- ela já
    # saiu acima, do critério da tabela, e o Manual manda usar "a mesma dose" (p. 243).
    # Por isso a troca é numa cópia do critério, que o laudo lê; o teto de aplicação
    # superficial do plantio direto (D9) também não entra: é de outra tabela. A aptidão
    # resolve pela MESMA função (motor/aplicacao_calcario.py), para o teto da §7.2.
    regra = regra_de_aplicacao(cultura_id, contexto, dados)
    if regra is not None:
        trace.registrar(
            regra="R-CAL-04: modo de aplicação do calcário pela situação da cultura",
            entradas={
                campo: contexto.variaveis.get(campo)
                for campo in ("programa", "fase", "momento")
            } | {"modo_na_tabela": criterio.get("modo_aplicacao")},
            saida={"situacao": regra["situacao"], "modo": regra["modo"], "area": regra["area"]},
            fonte=regra["fonte"],
        )
        criterio = {
            **criterio,
            "modo_aplicacao": regra["modo"],
            "area_aplicacao": regra["area"],
            "fonte_modo_aplicacao": regra["fonte"],
        }

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

    # A expectativa de rendimento entra aqui desde a ADR 0010: a parcela adicional sai
    # separada na saída do passo, porque a dose publicada é a tabelada e o excedente é
    # decisão de outra linha do Manual. Um total sem essa separação deixaria o leitor da
    # trilha sem saber de onde veio a diferença.
    trace.registrar(
        regra="R-ADU-02: dose de N pela faixa de matéria orgânica e pela expectativa de rendimento",
        entradas={
            "cultura_id": cultura_id,
            "mo": analise.mo,
            "antecedente": contexto.antecedente,
            "expectativa_rendimento": contexto.expectativa_rendimento,
        },
        saida={
            "n": resultado_n["n"],
            "faixa_mo": resultado_n["faixa_mo"],
            "adicional_kg_n_ha": resultado_n["adicional_kg_n_ha"],
            "teto_na_faixa_de_mo": resultado_n["teto"],
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
        expectativa_rendimento=contexto.expectativa_rendimento,
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
        orientacoes=_orientacoes(
            dados_graos["adubacao_n"]["culturas"].get(cultura_id, {})
        ),
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
                f"cultura '{cultura_id}': informe {', '.join(repr(n) for n in faltando)} — "
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


def _orientacoes(entrada: Dict[str, Any]) -> Dict[str, Any]:
    """Parcelamento, observações e restrições que a cultura publica, sem reescrever nada."""
    if not entrada:
        return {}
    colhidas = {
        chave: entrada[chave]
        for chave in ("parcelamento", "observacoes", "restricoes", "nota", "motivo")
        if entrada.get(chave)
    }
    return colhidas


def _montar_adubacao(
    analise: AnaliseSolo,
    cultura_id: str,
    contexto: Contexto,
    trace: Trace,
    dados: Dict[str, Any],
    dados_grupo: Dict[str, Any],
    resultado: Dict[str, Any],
) -> RecomendacaoAdubacao:
    entrada = buscar_por_nome(dados_grupo["adubacao"].get("culturas", {}), cultura_id) or {}
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
        orientacoes=_orientacoes(entrada),
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
    recomendacao = _montar_adubacao(
        analise, cultura_id, contexto, trace, dados, dados_grupo, resultado
    )
    if resultado.get("monitoramento"):
        recomendacao = dataclasses.replace(
            recomendacao, monitoramento=dict(resultado["monitoramento"])
        )
    regimes = resultado.get("regimes")
    if not regimes:
        return recomendacao

    # Passo próprio, e não uma chave a mais no R-ADU-04: "qual tabela dosou cada
    # nutriente" é a decisão que a banca vai perguntar quando a dose de P de um erval em
    # recuperação sair sem a parcela de elevação do teor.
    trace.registrar(
        regra=(
            "R-ADU-05/06: na recuperação de erval, só o nutriente abaixo do teor crítico "
            "segue o programa de recuperação; o outro, e o N quando nenhum está "
            "deficitário, seguem o regime de produção"
        ),
        entradas={
            "classe_p": resultado.get("classe_p"),
            "classe_k": resultado.get("classe_k"),
            "classes_da_recuperacao": dados_grupo["adubacao"]["culturas"]["erva_mate"]
            ["programa_recuperacao"]["pk"]["classes_atendidas"],
        },
        saida=dict(regimes),
        fonte="Manual 2016, Seção 6.6.5, programa de recuperação de ervais, p. 243-244",
    )
    return dataclasses.replace(recomendacao, regimes=dict(regimes))


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


def gerar_laudo(
    analise: AnaliseSolo,
    cultura_id: str,
    contexto: Contexto,
    dados: Optional[Dict[str, Any]] = None,
) -> Laudo:
    """Gera o laudo completo de uma análise de solo para uma cultura.

    Porta de entrada única do motor (CLAUDE.md, docs/especificacao/arquitetura.md): a camada web, os
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

    # Depois da adubação, e a partir dela: a formulação não é recomendação nova, é a
    # tradução da que acabou de sair para o produto que se compra. Três caminhos, porque
    # não existe catálogo oficial de fórmulas comercializadas (ADR 0009) — com o catálogo
    # vazio, a fórmula ideal e a mistura de simples seguem, e o laudo continua completo.
    formulacao = recomendar_formulacao(
        adubacao, carregar_formulas_npk(), trace,
        n_plantio=contexto.n_plantio,
        formulas_usuario=contexto.formulas_usuario,
    )

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
        formulacao=formulacao,
        avisos=_avisos_de_monitoramento(adubacao, calagem, trace),
    )


def _avisos_de_monitoramento(
    adubacao: RecomendacaoAdubacao, calagem: RecomendacaoCalagem, trace: Trace
) -> list:
    """R-ADU-07: o erval em produção com teor inadequado deve passar à recuperação.

    "Quando forem detectados teores inadequados de Ca e/ou Mg (ver Capítulo 5) ou P e/ou
    K (ver Capítulo 6), deve-se iniciar o programa de adubação para recuperação de
    ervais" (Manual 2016, p. 243). As remissões do próprio Manual dão a régua:

      - P e K, pelo Cap. 6: classe abaixo do teor crítico -- as classes que a tabela de
        recuperação atende. A produção pressupõe o contrário (p. 242).
      - Ca e Mg, pelo Cap. 5: o critério de calagem da cultura dispara. Para a erva-mate a
        calagem "visa apenas o suprimento de Ca e Mg", e a p. 84 manda calar quando "os
        teores de Ca e/ou Mg estão baixos", pelos critérios da Tab. 5.6. Calagem disparada
        = `motivo` vazio, como em toda a apresentação do laudo.

    É AVISO, e não troca de programa: escolher o programa continua sendo do usuário, e o
    laudo de produção sai inteiro. A leitura das duas remissões está transcrita em
    `producao.monitoramento` da base.
    """
    monitoramento = adubacao.monitoramento
    if not monitoramento:
        return []

    motivos = []
    if monitoramento["p_abaixo_do_critico"]:
        motivos.append("fósforo abaixo do teor crítico")
    if monitoramento["k_abaixo_do_critico"]:
        motivos.append("potássio abaixo do teor crítico")
    ca_mg_baixos = calagem.motivo is None
    if ca_mg_baixos:
        motivos.append("cálcio e/ou magnésio insuficientes pelo critério de calagem (Tab. 5.6)")

    trace.registrar(
        regra=(
            "R-ADU-07: monitoramento do erval em produção — teor inadequado de Ca/Mg ou "
            "de P/K indica a passagem ao programa de recuperação"
        ),
        entradas={
            "classe_p": monitoramento["classe_p"],
            "classe_k": monitoramento["classe_k"],
            "calagem_disparada": ca_mg_baixos,
        },
        saida={"indicar_recuperacao": bool(motivos), "motivos": motivos},
        fonte=f"Manual 2016, {monitoramento['fonte']}",
    )
    if not motivos:
        return []
    return [{
        "tipo": "atencao",
        "titulo": "Este erval deve passar ao programa de recuperação",
        "texto": (
            f"A análise mostra {', '.join(motivos)}. O Manual manda, nesse caso, iniciar o "
            "programa de adubação para recuperação de ervais; as doses acima são as do "
            "regime de produção, que pressupõe P e K acima do teor crítico. Para a "
            "recomendação de recuperação, gere o laudo de novo com o programa "
            "“Recuperação de erval”."
        ),
        "fonte": f"Manual 2016, {monitoramento['fonte']}",
    }]


__all__ = ["ErroLaudo", "gerar_laudo"]
