"""
Cálculo de adubação de N, P2O5 e K2O para os seis grupos de cultura do SIRAS: grãos,
hortaliças, tubérculos, outras culturas comerciais (cana e tabaco), frutíferas e
erva-mate (Cap. 6 do Manual).

Grãos (calcular_nitrogenio/calcular_fosforo_potassio) usam o algoritmo de correção +
manutenção por cultivo (Tabelas 6.1.1-6.1.4). Os demais grupos (calcular_adubacao_*)
já trazem a dose pronta por classe de teor/MO na própria tabela da cultura — não há
correção/manutenção separadas — e usam os utilitários genéricos `_navegar`/
`_resolver_dose`/`_classificar_p_e_k` para ler essas tabelas, todas no mesmo formato
(dados/culturas/<grupo>/*.json).

Escopo NÃO implementado, deliberadamente (levanta NotImplementedError, nunca um valor
adivinhado):
- Frutíferas cuja manutenção depende de teor foliar sem correspondência solo-tecido
  declarada pelo Manual (ameixeira, macieira, pessegueiro/nectarineira — `dados/`
  já marca `requer_analise_foliar: true`, `implementado_no_siras: false`).
- Frutíferas com indexação de manutenção própria e ainda sem caso de teste calculado à
  mão (amoreira-preta, mirtileiro, morangueiro, nogueira-pecã).
- Videira: N e P (correspondência solo→tecido declarada, Tab. 6.5.18, nota 1) estão
  implementados; K não tem correspondência declarada pelo Manual — o próprio `dados/`
  registra o alerta ("alerta" em `correspondencia_solo_tecido.k`).
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from siras.conhecimento.carregador import (
    carregar_dados_comum,
    carregar_dados_erva_mate,
    carregar_dados_frutiferas,
    carregar_dados_graos,
    carregar_dados_hortalicas,
    carregar_dados_outras,
    carregar_dados_tuberculos,
)


class ErroAdubacao(Exception):
    """Erro de dado ausente ou inconsistente ao calcular a adubação."""


def _arredondar_dezena(valor: float) -> float:
    """Arredonda para a dezena mais próxima, meio para cima (mesma política de D1).

    graos_adubacao_pk.json, algoritmo_dose.arredondamento: "A parcela de correção é
    arredondada para a dezena mais próxima ANTES de somar a manutenção."
    """
    return float((Decimal(str(valor)) / 10).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 10)


def _classificar_faixa(valor: float, faixas: List[Dict[str, Any]], chave_rotulo: str = "classe") -> str:
    """Classifica um valor numérico segundo uma lista de faixas contíguas (de/ate).

    Convenção (confirmada em testes/casos/casos_recomendacao.json, caso ADU-01: "P=6,0
    cai em muito_baixo, limite superior inclusivo"): faixa aplica-se quando
    de < valor <= ate (limite inferior aberto, superior fechado); None em "de"/"ate"
    representa -infinito/+infinito.
    """
    for faixa in faixas:
        de = faixa["de"]
        ate = faixa["ate"]
        if (de is None or valor > de) and (ate is None or valor <= ate):
            return faixa[chave_rotulo]
    raise ErroAdubacao(f"valor {valor} não se encaixa em nenhuma faixa: {faixas}")


def _grupo_exigencia(cultura_id: str, mapa_culturas: Dict[str, Any], grupos_exigencia: List[Dict[str, Any]],
                      nome_arquivo: str) -> str:
    """Resolve o grupo de exigência (P ou K) de uma cultura.

    Primeiro tenta a lista explícita de culturas de cada grupo (dado transcrito). Se a
    cultura não aparecer em nenhuma lista explícita mas pertencer ao grupo "graos" em
    mapa_culturas.json, cai no grupo_2 — que os dois arquivos descrevem em texto como
    "culturas de grãos exceto arroz irrigado" (interpretacao_p.json/interpretacao_k.json,
    grupos_exigencia[].culturas_texto). Arroz irrigado é fora de escopo do SIRAS e nunca
    aparece com grupo "graos" nesse fallback.
    """
    for grupo in grupos_exigencia:
        if cultura_id in grupo.get("culturas", []):
            return grupo["grupo"]

    entrada = mapa_culturas["culturas"].get(cultura_id)
    if entrada and entrada.get("grupo") == "graos":
        return "grupo_2"

    raise ErroAdubacao(
        f"não foi possível determinar o grupo de exigência em {nome_arquivo} para '{cultura_id}'"
    )


def calcular_nitrogenio(
    cultura_id: str,
    mo: float,
    antecedente: Optional[str] = None,
    dados_graos: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calcula a dose de N (kg/ha) para uma cultura de grãos, por faixa de MO.

    Returns:
        Dict com "n" (kg/ha) e "faixa_mo" usada (None quando modelo == "nao_aplica").

    Raises:
        ErroAdubacao: cultura não encontrada, modelo desconhecido, ou antecedente
            obrigatório ausente/inválido
    """
    dados_graos = dados_graos if dados_graos is not None else carregar_dados_graos()
    culturas = dados_graos["adubacao_n"]["culturas"]

    if cultura_id not in culturas:
        raise ErroAdubacao(f"cultura '{cultura_id}' não encontrada em graos_adubacao_n.json")

    entrada = culturas[cultura_id]
    modelo = entrada["modelo"]

    if modelo == "nao_aplica":
        return {"n": 0, "faixa_mo": None, "motivo": entrada["motivo"]}

    if mo <= 2.5:
        faixa_mo = "mo_ate_2_5"
    elif mo <= 5.0:
        faixa_mo = "mo_2_6_a_5_0"
    else:
        faixa_mo = "mo_acima_5_0"

    if modelo == "mo":
        dose = entrada["doses_kg_n_ha"][faixa_mo]
    elif modelo == "mo_x_antecedente":
        antecedentes_validos = entrada["antecedentes"]
        if antecedente not in antecedentes_validos:
            raise ErroAdubacao(
                f"cultura '{cultura_id}': modelo 'mo_x_antecedente' exige 'antecedente' em "
                f"{antecedentes_validos}, recebido {antecedente!r}"
            )
        dose = entrada["doses_kg_n_ha"][faixa_mo][antecedente]
    else:
        raise ErroAdubacao(f"cultura '{cultura_id}': modelo '{modelo}' desconhecido")

    return {"n": dose, "faixa_mo": faixa_mo, "motivo": None}


def _dose_pk(classe: str, cultivo: int, correcao_nutriente: Optional[float], manutencao_valor: float):
    """Aplica o algoritmo de dose de graos_adubacao_pk.json (algoritmo_dose.regras)."""
    if classe in ("muito_baixo", "baixo"):
        fracao = (2 / 3) if cultivo == 1 else (1 / 3)
        return _arredondar_dezena(fracao * correcao_nutriente) + manutencao_valor
    if classe == "medio":
        if cultivo == 1:
            return _arredondar_dezena(correcao_nutriente) + manutencao_valor
        return manutencao_valor
    if classe == "alto":
        return manutencao_valor
    if classe == "muito_alto":
        # Manual: cultivo 1 = 0 (determinístico). Cultivo 2 = "<= manutencao (reposicao,
        # a criterio do tecnico)" — um TETO, não um valor. Representado no formato de
        # dose do ADR 0004 (D4.1), a mesma forma usada por hortaliças/frutíferas para
        # "qualificador: ate" — não um escalar, para não implicar precisão que o Manual
        # não dá.
        if cultivo == 1:
            return 0.0
        return {"valor": manutencao_valor, "qualificador": "ate"}
    raise ErroAdubacao(f"classe de teor '{classe}' desconhecida")


def calcular_fosforo_potassio(
    cultura_id: str,
    argila: float,
    p_solo: float,
    ctc_ph7: float,
    k_solo: float,
    cultivo: int,
    expectativa_rendimento: Optional[float] = None,
    dados_comuns: Optional[Dict[str, Any]] = None,
    dados_graos: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Classifica o teor de P e K do solo e calcula a dose de P2O5/K2O (kg/ha).

    Args:
        argila: teor de argila (%), para a classe de argila (interpretacao_geral.json)
        p_solo: teor de P no solo (mg/dm3, Mehlich-1)
        ctc_ph7: CTC a pH 7,0 (cmolc/dm3), para a faixa de CTC (interpretacao_k.json)
        k_solo: teor de K no solo (mg/dm3, Mehlich-1)
        cultivo: 1 (dose de correção completa) ou 2 (dose reduzida em rotação)
        expectativa_rendimento: rendimento esperado (t/ha); acima do rendimento de
            referência da cultura, soma o adicional por tonelada à manutenção

    Returns:
        Dict com "classe_p", "classe_k", "p2o5", "k2o". "p2o5"/"k2o" são normalmente
        float; na classe "muito_alto" com cultivo=2, o Manual só dá um teto ("<=
        manutenção"), não um valor, e o retorno é o objeto de dose do ADR 0004
        (`{"valor": ..., "qualificador": "ate"}`).

    Raises:
        ErroAdubacao: cultura/grupo de exigência não encontrados, ou 'cultivo' inválido
    """
    if cultivo not in (1, 2):
        raise ErroAdubacao(f"'cultivo' deve ser 1 ou 2, recebido {cultivo}")

    dados_comuns = dados_comuns if dados_comuns is not None else carregar_dados_comum()
    dados_graos = dados_graos if dados_graos is not None else carregar_dados_graos()

    mapa_culturas = dados_comuns["mapa_culturas"]
    interpretacao_p = dados_comuns["interpretacao_p"]
    interpretacao_k = dados_comuns["interpretacao_k"]
    adubacao_pk = dados_graos["adubacao_pk"]

    manutencao = adubacao_pk["manutencao_por_cultura"]["culturas"].get(cultura_id)
    if manutencao is None:
        raise ErroAdubacao(f"cultura '{cultura_id}' não encontrada em manutencao_por_cultura")

    faixas_argila = next(
        atributo["faixas"]
        for atributo in dados_comuns["interpretacao_geral"]["atributos"]
        if atributo["atributo"] == "argila"
    )
    classe_argila = _classificar_faixa(argila, faixas_argila)

    grupo_p = _grupo_exigencia(cultura_id, mapa_culturas, interpretacao_p["grupos_exigencia"], "interpretacao_p.json")
    tabela_p = next(t for t in interpretacao_p["tabelas"] if t["grupo"] == grupo_p)
    faixas_p = next(
        bloco["faixas"] for bloco in tabela_p["por_classe_argila"] if bloco["classe_argila"] == classe_argila
    )
    classe_p = _classificar_faixa(p_solo, faixas_p)

    faixa_ctc = _classificar_faixa(ctc_ph7, interpretacao_k["faixas_ctc"], chave_rotulo="faixa")

    grupo_k = _grupo_exigencia(cultura_id, mapa_culturas, interpretacao_k["grupos_exigencia"], "interpretacao_k.json")
    tabela_k = next(t for t in interpretacao_k["tabelas"] if t["grupo"] == grupo_k)
    bloco_k = next(bloco for bloco in tabela_k["por_faixa_ctc"] if bloco["faixa_ctc"] == faixa_ctc)
    classe_k = _classificar_faixa(k_solo, bloco_k["faixas"])

    rendimento_referencia = manutencao["rendimento_referencia_t_ha"]
    delta_rendimento = 0.0
    if expectativa_rendimento is not None and expectativa_rendimento > rendimento_referencia:
        delta_rendimento = expectativa_rendimento - rendimento_referencia

    manutencao_p2o5 = manutencao["p2o5_manutencao"] + delta_rendimento * manutencao["p2o5_adicional_por_t"]
    manutencao_k2o = manutencao["k2o_manutencao"] + delta_rendimento * manutencao["k2o_adicional_por_t"]

    correcao_total = adubacao_pk["correcao_total"]
    correcao_p2o5 = correcao_total.get(classe_p, {}).get("p2o5")
    correcao_k2o = correcao_total.get(classe_k, {}).get("k2o")

    p2o5 = _dose_pk(classe_p, cultivo, correcao_p2o5, manutencao_p2o5)
    k2o = _dose_pk(classe_k, cultivo, correcao_k2o, manutencao_k2o)

    return {
        "classe_p": classe_p,
        "classe_k": classe_k,
        "p2o5": p2o5,
        "k2o": k2o,
    }


# ---------------------------------------------------------------------------------
# Utilitários genéricos para os grupos hortaliças/tubérculos/outras/frutíferas/erva-mate
# ---------------------------------------------------------------------------------
#
# Diferente de grãos, esses grupos publicam a dose já pronta por classe de teor/MO
# (sem correção + manutenção separadas). O formato de cada tabela varia só na
# QUANTIDADE e na ORDEM dos índices (classe/faixa de MO, mais opcionalmente fase, tipo,
# faixa de produtividade ou momento) — não no mecanismo de leitura. `_navegar` cobre
# esse mecanismo uma vez só, e cada função de grupo só precisa dizer qual índice extra
# (se algum) usar, conforme `entrada["n"/"pk"]["tipo"]` documenta no próprio dado.


def _resolver_dose(dose: Any):
    """Resolve um nó-folha de dose para o valor de saída (ADR 0004, D4.1).

    {"valor": X} -> X (float). Formas com mais informação que um único número —
    {"min","max"} ou {"valor","qualificador":"ate"} — são preservadas como dict: o
    domínio e o laudo mantêm a forma original (só a comparação com o oráculo, no
    teste, normaliza em intervalo).
    """
    if not isinstance(dose, dict):
        return dose
    if "qualificador" in dose or "min" in dose:
        return dict(dose)
    if "valor" in dose:
        return float(dose["valor"])
    raise ErroAdubacao(f"formato de dose desconhecido: {dose}")


def _navegar(bloco: Dict[str, Any], *chaves: str):
    """Desce em `bloco` pela sequência de chaves e resolve a dose na folha."""
    valor: Any = bloco
    for chave in chaves:
        if not isinstance(valor, dict) or chave not in valor:
            raise ErroAdubacao(
                f"chave '{chave}' não encontrada (disponíveis: "
                f"{list(valor.keys()) if isinstance(valor, dict) else valor})"
            )
        valor = valor[chave]
    return _resolver_dose(valor)


def _classe_mo(mo: float, classes_mo: List[Dict[str, Any]]) -> str:
    """Classifica MO pelas faixas do próprio arquivo de dados — nunca hardcoded em
    Python (D4.4, docs/decisoes/0004): o tabaco usa 6 faixas próprias, não as 3 comuns
    às demais culturas, e reaproveitar faixas fixas quebraria esse caso silenciosamente.
    """
    return _classificar_faixa(mo, classes_mo, chave_rotulo="id")


def _classificar_p_e_k(
    entrada: Dict[str, Any],
    cultura_id: str,
    argila: float,
    p_solo: float,
    k_solo: float,
    ctc_ph7: float,
    dados_comuns: Dict[str, Any],
) -> Tuple[str, str]:
    """Classifica P e K lendo `entrada["grupo_exigencia"]` (declarado explicitamente em
    cada cultura de dados/culturas/<grupo>/*.json — sem fallback: cultura sem o campo é
    erro de dado, não suposição de grupo)."""
    grupo_exigencia = entrada.get("grupo_exigencia")
    if grupo_exigencia is None:
        raise ErroAdubacao(f"cultura '{cultura_id}' não declara 'grupo_exigencia'")

    interpretacao_p = dados_comuns["interpretacao_p"]
    faixas_argila = next(
        atributo["faixas"]
        for atributo in dados_comuns["interpretacao_geral"]["atributos"]
        if atributo["atributo"] == "argila"
    )
    classe_argila = _classificar_faixa(argila, faixas_argila)
    grupo_p = f"grupo_{grupo_exigencia['p']}"
    tabela_p = next(t for t in interpretacao_p["tabelas"] if t["grupo"] == grupo_p)
    faixas_p = next(
        bloco["faixas"] for bloco in tabela_p["por_classe_argila"] if bloco["classe_argila"] == classe_argila
    )
    classe_p = _classificar_faixa(p_solo, faixas_p)

    interpretacao_k = dados_comuns["interpretacao_k"]
    faixa_ctc = _classificar_faixa(ctc_ph7, interpretacao_k["faixas_ctc"], chave_rotulo="faixa")
    grupo_k = f"grupo_{grupo_exigencia['k']}"
    tabela_k = next(t for t in interpretacao_k["tabelas"] if t["grupo"] == grupo_k)
    bloco_k = next(bloco for bloco in tabela_k["por_faixa_ctc"] if bloco["faixa_ctc"] == faixa_ctc)
    classe_k = _classificar_faixa(k_solo, bloco_k["faixas"])

    return classe_p, classe_k


def _nome_indice_extra(tipo: str) -> Optional[str]:
    """Extrai o nome do índice extra do sufixo de um 'tipo' (ex.: 'por_classe_mo_e_fase'
    -> 'fase'), para mensagens de erro claras quando o chamador não o informou."""
    if "_e_" not in tipo:
        return None
    return tipo.rsplit("_e_", 1)[1]


def _calcular_n_generico(
    bloco_n: Dict[str, Any], classes_mo: Dict[str, Any], mo: float, indice_extra: Optional[str]
) -> Tuple[Any, Optional[str]]:
    """Resolve a dose de N de um bloco `{"tipo": "por_classe_mo[_e_X]", ...}`.

    Retorna (dose, motivo) — motivo não-None só quando o N não é recomendado
    (leguminosas: fixação biológica) ou não se aplica na fase (P/K do pré-plantio já
    bastam).
    """
    tipo = bloco_n.get("tipo", "")
    if tipo in ("nao_recomendado", "nao_aplicar"):
        return 0.0, bloco_n.get("motivo", tipo)

    nome_extra = _nome_indice_extra(tipo)
    if nome_extra is not None and indice_extra is None:
        raise ErroAdubacao(f"'{nome_extra}' é obrigatório para o cálculo de N (tipo '{tipo}')")

    faixa_mo = _classe_mo(mo, classes_mo[bloco_n["classes_mo"]])
    if indice_extra is not None:
        return _navegar(bloco_n["doses"], faixa_mo, indice_extra), None
    return _navegar(bloco_n["doses"], faixa_mo), None


def _calcular_pk_generico(
    bloco_pk: Dict[str, Any], classe_p: str, classe_k: str, indice_extra: Optional[str]
) -> Tuple[Any, Any]:
    """Resolve P2O5/K2O de um bloco `{"tipo": "por_classe_teor[_e_X]", "p": ..., "k": ...}`."""
    tipo = bloco_pk.get("tipo", "")
    if tipo == "nao_aplicar":
        return 0.0, 0.0

    nome_extra = _nome_indice_extra(tipo)
    if nome_extra is not None and indice_extra is None:
        raise ErroAdubacao(f"'{nome_extra}' é obrigatório para o cálculo de P/K (tipo '{tipo}')")

    if indice_extra is not None:
        return _navegar(bloco_pk["p"], classe_p, indice_extra), _navegar(bloco_pk["k"], classe_k, indice_extra)
    return _navegar(bloco_pk["p"], classe_p), _navegar(bloco_pk["k"], classe_k)


def _somar_incremento(dose: Any, incremento: float):
    """Soma um incremento linear (ajuste_expectativa_rendimento) a uma dose já
    resolvida, preservando a forma (escalar, ou dict com min/max/qualificador)."""
    if isinstance(dose, dict):
        nova = dict(dose)
        if "valor" in nova:
            nova["valor"] = nova["valor"] + incremento
        if "min" in nova:
            nova["min"] = nova["min"] + incremento
            nova["max"] = nova["max"] + incremento
        return nova
    return dose + incremento


def _aplicar_ajuste_expectativa(
    entrada: Dict[str, Any], expectativa_rendimento: Optional[float], n: Any, p2o5: Any, k2o: Any
) -> Tuple[Any, Any, Any]:
    """Aplica `ajuste_expectativa_rendimento` (incremento linear acima de um limiar de
    produtividade) quando a cultura o declara e a expectativa informada o ultrapassa."""
    ajuste = entrada.get("ajuste_expectativa_rendimento")
    if not ajuste or expectativa_rendimento is None or expectativa_rendimento <= ajuste["acima_de_t_ha"]:
        return n, p2o5, k2o
    delta = expectativa_rendimento - ajuste["acima_de_t_ha"]
    n = _somar_incremento(n, delta * ajuste["n_kg_por_t"])
    p2o5 = _somar_incremento(p2o5, delta * ajuste["p_kg_por_t"])
    k2o = _somar_incremento(k2o, delta * ajuste["k_kg_por_t"])
    return n, p2o5, k2o


def calcular_adubacao_hortalicas(
    cultura_id: str,
    mo: float,
    argila: float,
    p_solo: float,
    k_solo: float,
    ctc_ph7: float,
    expectativa_rendimento: Optional[float] = None,
    fase: Optional[str] = None,
    fase_n: Optional[str] = None,
    fase_pk: Optional[str] = None,
    dados_hortalicas: Optional[Dict[str, Any]] = None,
    dados_comuns: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calcula N/P2O5/K2O para uma hortaliça (dados/culturas/hortalicas/).

    Só o aspargo usa fase de cultivo (além da classe de teor/MO), e com um detalhe: o
    Manual nomeia as fases de N ('instalacao'/'formacao'/'manutencao') diferente das de
    P/K ('pre_plantio'/'formacao'/'manutencao') — não é o mesmo eixo de 3 fases. `fase`
    cobre o caso comum (mesma fase para os dois, ex.: 'formacao'/'manutencao');
    `fase_n`/`fase_pk` sobrescrevem individualmente quando os nomes divergem (ex.: N em
    'instalacao' com P/K em 'pre_plantio').
    """
    dados_hortalicas = dados_hortalicas if dados_hortalicas is not None else carregar_dados_hortalicas()
    dados_comuns = dados_comuns if dados_comuns is not None else carregar_dados_comum()
    adubacao = dados_hortalicas["adubacao"]

    entrada = adubacao["culturas"].get(cultura_id)
    if entrada is None:
        raise ErroAdubacao(f"cultura '{cultura_id}' não encontrada em hortalicas_adubacao.json")

    classe_p, classe_k = _classificar_p_e_k(entrada, cultura_id, argila, p_solo, k_solo, ctc_ph7, dados_comuns)

    fase_n = fase_n if fase_n is not None else fase
    fase_pk = fase_pk if fase_pk is not None else fase

    indice_n = fase_n if entrada["n"].get("tipo", "").endswith("_e_fase") else None
    n, motivo_n = _calcular_n_generico(entrada["n"], adubacao["classes_mo"], mo, indice_n)

    indice_pk = fase_pk if entrada["pk"].get("tipo", "").endswith("_e_fase") else None
    p2o5, k2o = _calcular_pk_generico(entrada["pk"], classe_p, classe_k, indice_pk)

    n, p2o5, k2o = _aplicar_ajuste_expectativa(entrada, expectativa_rendimento, n, p2o5, k2o)

    return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "motivo_n": motivo_n, "p2o5": p2o5, "k2o": k2o}


def calcular_adubacao_tuberculos(
    cultura_id: str,
    mo: float,
    argila: float,
    p_solo: float,
    k_solo: float,
    ctc_ph7: float,
    expectativa_rendimento: Optional[float] = None,
    dados_tuberculos: Optional[Dict[str, Any]] = None,
    dados_comuns: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calcula N/P2O5/K2O para batata ou batata-doce (dados/culturas/tuberculos/)."""
    dados_tuberculos = dados_tuberculos if dados_tuberculos is not None else carregar_dados_tuberculos()
    dados_comuns = dados_comuns if dados_comuns is not None else carregar_dados_comum()
    adubacao = dados_tuberculos["adubacao"]

    entrada = adubacao["culturas"].get(cultura_id)
    if entrada is None:
        raise ErroAdubacao(f"cultura '{cultura_id}' não encontrada em tuberculos_adubacao.json")

    classe_p, classe_k = _classificar_p_e_k(entrada, cultura_id, argila, p_solo, k_solo, ctc_ph7, dados_comuns)
    n, motivo_n = _calcular_n_generico(entrada["n"], adubacao["classes_mo"], mo, None)
    p2o5, k2o = _calcular_pk_generico(entrada["pk"], classe_p, classe_k, None)
    n, p2o5, k2o = _aplicar_ajuste_expectativa(entrada, expectativa_rendimento, n, p2o5, k2o)

    return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "motivo_n": motivo_n, "p2o5": p2o5, "k2o": k2o}


def calcular_adubacao_outras(
    cultura_id: str,
    mo: float,
    argila: float,
    p_solo: float,
    k_solo: float,
    ctc_ph7: float,
    ciclo: Optional[str] = None,
    tipo: Optional[str] = None,
    produtividade_t_ha: Optional[float] = None,
    dados_outras: Optional[Dict[str, Any]] = None,
    dados_comuns: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calcula N/P2O5/K2O para cana-de-açúcar ou tabaco (dados/culturas/outras/).

    Cana exige `ciclo` ('cana_planta' ou 'cana_soca') e `produtividade_t_ha`; tabaco
    exige `tipo` ('virginia' ou 'burley'). As duas culturas têm formatos diferentes
    demais para uma única função genérica além da classificação de P/K.
    """
    dados_outras = dados_outras if dados_outras is not None else carregar_dados_outras()
    dados_comuns = dados_comuns if dados_comuns is not None else carregar_dados_comum()
    adubacao = dados_outras["adubacao"]

    entrada = adubacao["culturas"].get(cultura_id)
    if entrada is None:
        raise ErroAdubacao(f"cultura '{cultura_id}' não encontrada em outras_comerciais_adubacao.json")

    classe_p, classe_k = _classificar_p_e_k(entrada, cultura_id, argila, p_solo, k_solo, ctc_ph7, dados_comuns)

    if cultura_id == "cana_de_acucar":
        if ciclo not in ("cana_planta", "cana_soca"):
            raise ErroAdubacao("cana-de-açúcar exige 'ciclo' em ('cana_planta', 'cana_soca')")
        bloco = entrada[ciclo]

        indice_produtividade = None
        if produtividade_t_ha is not None:
            indice_produtividade = _classificar_faixa(
                produtividade_t_ha, bloco["pk"]["faixas_produtividade"], chave_rotulo="id"
            )

        indice_n = indice_produtividade if bloco["n"].get("tipo", "").endswith("_e_produtividade") else None
        n, motivo_n = _calcular_n_generico(bloco["n"], adubacao["classes_mo"], mo, indice_n)

        if indice_produtividade is None:
            raise ErroAdubacao("cana-de-açúcar exige 'produtividade_t_ha' para a dose de P/K")
        p2o5, k2o = _calcular_pk_generico(bloco["pk"], classe_p, classe_k, indice_produtividade)

        return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "motivo_n": motivo_n, "p2o5": p2o5, "k2o": k2o}

    if cultura_id == "tabaco":
        if tipo not in ("virginia", "burley"):
            raise ErroAdubacao("tabaco exige 'tipo' em ('virginia', 'burley')")

        n, motivo_n = _calcular_n_generico(entrada["n"], adubacao["classes_mo"], mo, tipo)
        # P e "comum aos tipos" (Tab. 6.9.2, p_comum_aos_tipos): sem indice de tipo. K
        # depende do tipo (virginia/burley tem colunas de K distintas).
        p2o5 = _navegar(entrada["pk"]["p"], classe_p)
        k2o = _navegar(entrada["pk"]["k"], classe_k, tipo)

        return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "motivo_n": motivo_n, "p2o5": p2o5, "k2o": k2o}

    raise ErroAdubacao(f"cultura '{cultura_id}' não implementada em calcular_adubacao_outras")


def _dose_taxa_por_tonelada(taxa: Dict[str, Any], produtividade: float):
    """Multiplica uma taxa por tonelada estimada (frutíferas de manutenção, Seção 6.5)
    pela produtividade — preservando min/max quando a taxa é uma faixa."""
    if taxa.get("tipo") == "nao_aplicar":
        return 0.0
    dose = _resolver_dose(taxa)
    if isinstance(dose, dict):
        resultado = dict(dose)
        if "valor" in resultado:
            resultado["valor"] = resultado["valor"] * produtividade
        if "min" in resultado:
            resultado["min"] = resultado["min"] * produtividade
            resultado["max"] = resultado["max"] * produtividade
        return resultado
    return dose * produtividade


# Videira (Tab. 6.5.18, p. 230-231, nota 1): correspondência solo -> classe de tecido
# usada só na AUSÊNCIA de análise de tecido. N deriva da MO (mesmos limiares de
# classes_mo.padrao); P deriva da própria classe de teor de P no solo. São fontes
# DIFERENTES — não derive uma da outra (ver ADU-19, docs/decisoes).
_TECIDO_POR_MO = {"ate_2_5": "insuficiente", "de_2_6_a_5_0": "normal", "acima_5_0": "excessivo"}
_TECIDO_POR_CLASSE_P = {
    "muito_baixo": "insuficiente", "baixo": "insuficiente",
    "medio": "normal", "alto": "normal",
    "muito_alto": "excessivo",
}


def calcular_adubacao_frutiferas(
    cultura_id: str,
    fase: str,
    mo: Optional[float] = None,
    argila: Optional[float] = None,
    p_solo: Optional[float] = None,
    k_solo: Optional[float] = None,
    ctc_ph7: Optional[float] = None,
    ano: Optional[int] = None,
    produtividade_estimada: Optional[float] = None,
    tipo_uva: Optional[str] = None,
    analise_de_tecido: Optional[Dict[str, str]] = None,
    ano_de_alternancia: bool = False,
    dados_frutiferas: Optional[Dict[str, Any]] = None,
    dados_comuns: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calcula N/P2O5/K2O para uma frutífera, por fase ('pre_plantio', 'crescimento' ou
    'manutencao' — Seção 6.5).

    Cobre pré-plantio (referência comum, Tab. 6.5.1) e crescimento (N por classe de MO,
    com ou sem 'ano') para todas as frutíferas do escopo. Manutenção cobre: taxa por
    tonelada estimada (abacateiro, bananeira, caquizeiro, citros, figueira, oliveira,
    pereira, quivizeiro); amoreira-preta (N por MO x ano x produtividade, colunas
    nomeadas — 'ano' identifica o ano após o plantio); mirtileiro e morangueiro
    (crescimento e manutenção unificados — chamar direto com fase='manutencao'; N do
    morangueiro ignora a MO de propósito, ver p. 214); nogueira-pecã (N por
    produtividade simples, com redução de 50% quando `ano_de_alternancia=True`; PK por
    taxa/tonelada); e videira (`tipo_uva` obrigatório — N e P por correspondência
    solo-tecido, cada um com fonte própria (MO para N, classe de P para P — não derive
    uma da outra); `analise_de_tecido` (dict opcional {"n":.., "p":..}) sobrepõe a
    correspondência quando há análise de tecido real. K da videira não tem
    correspondência declarada pelo Manual — sempre retorna pendente, nunca uma dose.

    Ameixeira, macieira e pêssego/nectarina, e a própria videira em K, seguem sem
    solução por análise de solo — levantam NotImplementedError (foliar) ou retornam
    "k2o": None com uma explicação (videira): ver docstring do módulo.
    """
    dados_frutiferas = dados_frutiferas if dados_frutiferas is not None else carregar_dados_frutiferas()
    dados_comuns = dados_comuns if dados_comuns is not None else carregar_dados_comum()
    adubacao = dados_frutiferas["adubacao"]

    entrada = adubacao["culturas"].get(cultura_id)
    if entrada is None:
        raise ErroAdubacao(f"cultura '{cultura_id}' não encontrada em frutiferas_adubacao.json")

    if fase == "pre_plantio":
        bloco_pk = entrada["pre_plantio"]["pk"]
        if bloco_pk.get("tipo") != "referencia":
            raise NotImplementedError(
                f"cultura '{cultura_id}': pre_plantio.pk.tipo='{bloco_pk.get('tipo')}' inesperado"
            )
        chave_tabela = "tabela_" + bloco_pk["tabela"].replace(".", "_")
        tabela = adubacao[chave_tabela]
        classe_p, classe_k = _classificar_p_e_k(entrada, cultura_id, argila, p_solo, k_solo, ctc_ph7, dados_comuns)
        p2o5 = _navegar(tabela["p"], classe_p)
        k2o = _navegar(tabela["k"], classe_k)
        return {"classe_p": classe_p, "classe_k": classe_k, "n": 0.0, "p2o5": p2o5, "k2o": k2o}

    if fase == "crescimento":
        bloco = entrada["crescimento"]
        n_bloco = bloco["n"]
        tipo_n = n_bloco.get("tipo")
        if tipo_n == "ver_manutencao":
            raise ErroAdubacao(
                f"cultura '{cultura_id}': crescimento e manutenção são unificados — use fase='manutencao'"
            )
        if tipo_n in ("nao_aplicar", "nao_recomendado"):
            n = 0.0
        elif tipo_n == "por_classe_mo":
            n = _navegar(n_bloco["doses"], _classe_mo(mo, adubacao["classes_mo"][n_bloco["classes_mo"]]))
        elif tipo_n == "por_classe_mo_e_ano":
            if ano is None:
                raise ErroAdubacao(f"cultura '{cultura_id}': 'ano' é obrigatório na fase de crescimento")
            faixa_mo = _classe_mo(mo, adubacao["classes_mo"][n_bloco["classes_mo"]])
            n = _navegar(n_bloco["doses"], faixa_mo, str(ano))
        else:
            raise NotImplementedError(
                f"cultura '{cultura_id}': crescimento.n.tipo='{tipo_n}' ainda não implementado"
            )

        tipo_pk = bloco["pk"].get("tipo")
        if tipo_pk != "nao_aplicar":
            raise NotImplementedError(
                f"cultura '{cultura_id}': crescimento.pk.tipo='{tipo_pk}' ainda não implementado"
            )
        return {"n": n, "p2o5": 0.0, "k2o": 0.0}

    if fase == "manutencao":
        bloco = entrada["manutencao"]
        if bloco.get("requer_analise_foliar"):
            raise NotImplementedError(
                f"cultura '{cultura_id}': manutenção depende de análise foliar sem "
                f"correspondência solo-tecido declarada pelo Manual "
                f"({bloco.get('motivo_nao_implementado', 'ver dados/culturas/frutiferas/')})"
            )

        if cultura_id == "amoreira_preta":
            if ano is None or produtividade_estimada is None:
                raise ErroAdubacao("amoreira_preta: 'ano' e 'produtividade_estimada' são obrigatórios na manutenção")
            classe_p, classe_k = _classificar_p_e_k(entrada, cultura_id, argila, p_solo, k_solo, ctc_ph7, dados_comuns)

            n_bloco = bloco["n"]
            faixa_mo = _classe_mo(mo, adubacao["classes_mo"][n_bloco["classes_mo"]])
            if ano == 1:
                n = 0.0  # nota (1): 1o ano é o ano de plantio, "nao_aplicar"
            else:
                faixa_prod_n = _classificar_faixa(produtividade_estimada, n_bloco["faixas_produtividade"], chave_rotulo="id")
                coluna = f"ano_2_{faixa_prod_n}" if ano == 2 else f"ano_3_mais_{faixa_prod_n}"
                n = _navegar(n_bloco["doses"], faixa_mo, coluna)

            pk_bloco = bloco["pk"]
            faixa_prod_pk = _classificar_faixa(produtividade_estimada, pk_bloco["faixas_produtividade"], chave_rotulo="id")
            p2o5 = _navegar(pk_bloco["p"], classe_p, faixa_prod_pk)
            k2o = _navegar(pk_bloco["k"], classe_k, faixa_prod_pk)
            return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "p2o5": p2o5, "k2o": k2o}

        if cultura_id == "mirtileiro":
            if produtividade_estimada is None:
                raise ErroAdubacao("mirtileiro: 'produtividade_estimada' é obrigatória na manutenção")
            classe_p, classe_k = _classificar_p_e_k(entrada, cultura_id, argila, p_solo, k_solo, ctc_ph7, dados_comuns)

            n_bloco = bloco["n"]
            faixa_mo = _classe_mo(mo, adubacao["classes_mo"][n_bloco["classes_mo"]])
            faixa_prod_n = _classificar_faixa(produtividade_estimada, n_bloco["faixas_produtividade"], chave_rotulo="id")
            n = _navegar(n_bloco["doses"], faixa_mo, faixa_prod_n)

            pk_bloco = bloco["pk"]
            faixa_prod_pk = _classificar_faixa(produtividade_estimada, pk_bloco["faixas_produtividade"], chave_rotulo="id")
            p2o5 = _navegar(pk_bloco["p"], classe_p, faixa_prod_pk)
            k2o = _navegar(pk_bloco["k"], classe_k, faixa_prod_pk)
            return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "p2o5": p2o5, "k2o": k2o}

        if cultura_id == "morangueiro":
            if produtividade_estimada is None:
                raise ErroAdubacao("morangueiro: 'produtividade_estimada' é obrigatória na manutenção")
            classe_p, classe_k = _classificar_p_e_k(entrada, cultura_id, argila, p_solo, k_solo, ctc_ph7, dados_comuns)

            # N ignora a MO de propósito (p. 214): substrato orgânico contribui pouco.
            n_bloco = bloco["n"]
            faixa_prod_n = _classificar_faixa(produtividade_estimada, n_bloco["faixas_produtividade"], chave_rotulo="id")
            n = _navegar(n_bloco["doses"], faixa_prod_n)

            pk_bloco = bloco["pk"]
            p2o5 = _navegar(pk_bloco["p"], classe_p)  # P: só classe, sem produtividade
            faixa_prod_k = _classificar_faixa(produtividade_estimada, pk_bloco["faixas_produtividade"], chave_rotulo="id")
            k2o = _navegar(pk_bloco["k"], classe_k, faixa_prod_k)
            return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "p2o5": p2o5, "k2o": k2o}

        if cultura_id == "nogueira_peca":
            if produtividade_estimada is None:
                raise ErroAdubacao("nogueira_peca: 'produtividade_estimada' é obrigatória na manutenção")
            n_bloco = bloco["n"]
            faixa_prod = _classificar_faixa(produtividade_estimada, n_bloco["faixas_produtividade"], chave_rotulo="id")
            n = _navegar(n_bloco["doses"], faixa_prod)
            if ano_de_alternancia:
                # Ajuste (p. 217, cultivares Barton/Cheyenne/Elliott/Jackson/Mahan/
                # Moneymaker/Shoshoni/Shawnee/Success): reduz N em 50% no ano de baixa
                # produtividade por alternância. Só P/K seguem a taxa normal.
                n = n * 0.5
            pk_bloco = bloco["pk"]
            p2o5 = _dose_taxa_por_tonelada(pk_bloco["p"], produtividade_estimada)
            k2o = _dose_taxa_por_tonelada(pk_bloco["k"], produtividade_estimada)
            return {"n": n, "p2o5": p2o5, "k2o": k2o}

        if cultura_id == "videira":
            if tipo_uva not in ("vinho", "mesa"):
                raise ErroAdubacao("videira exige 'tipo_uva' em ('vinho', 'mesa') na manutenção")
            if produtividade_estimada is None:
                raise ErroAdubacao("videira: 'produtividade_estimada' é obrigatória na manutenção")

            analise = analise_de_tecido or {}
            classe_p = classe_k = None

            classe_tecido_n = analise.get("n")
            if classe_tecido_n is None:
                if mo is None:
                    raise ErroAdubacao("videira: 'mo' é obrigatória para derivar a classe de tecido de N (sem analise_de_tecido)")
                faixa_mo = _classe_mo(mo, adubacao["classes_mo"]["padrao"])
                classe_tecido_n = _TECIDO_POR_MO[faixa_mo]

            classe_tecido_p = analise.get("p")
            if classe_tecido_p is None:
                classe_p, classe_k = _classificar_p_e_k(entrada, cultura_id, argila, p_solo, k_solo, ctc_ph7, dados_comuns)
                classe_tecido_p = _TECIDO_POR_CLASSE_P[classe_p]

            faixa_prod = _classificar_faixa(produtividade_estimada, bloco["faixas_produtividade"], chave_rotulo="id")

            # "excessivo" usa a chave especial 'qualquer_produtividade' (Tab. 6.5.18) —
            # não a faixa de produtividade normal.
            faixa_n = "qualquer_produtividade" if classe_tecido_n == "excessivo" else faixa_prod
            n = _navegar(bloco["n"]["doses"], classe_tecido_n, faixa_n, tipo_uva)

            faixa_p = "qualquer_produtividade" if classe_tecido_p == "excessivo" else faixa_prod
            p2o5 = _navegar(bloco["pk"]["p"], classe_tecido_p, faixa_p)

            resultado = {
                "n": n,
                "p2o5": p2o5,
                "k2o": None,
                "classe_tecido_n": classe_tecido_n,
                "classe_tecido_p": classe_tecido_p,
                "k2o_pendente": (
                    "O Manual não declara correspondência solo->tecido para K (Tab. "
                    "6.5.18, p. 231, nota 1, cobre só P) — exige análise de tecido "
                    "(peciolos: Tab. 6.5.18; folhas: Tab. 6.5.19). Doses de K acima do "
                    "tabelado favorecem a elevação do pH do vinho, sobretudo em tintos "
                    "(p. 230) — não extrapolar a partir do P."
                ),
            }
            if classe_p is not None:
                resultado["classe_p"] = classe_p
                resultado["classe_k"] = classe_k
            return resultado

        if bloco.get("tipo") == "taxa_por_tonelada_estimada":
            if produtividade_estimada is None:
                raise ErroAdubacao(f"cultura '{cultura_id}': 'produtividade_estimada' é obrigatória na manutenção")
            n = _dose_taxa_por_tonelada(bloco["n"], produtividade_estimada)
            p2o5 = _dose_taxa_por_tonelada(bloco["p"], produtividade_estimada)
            k2o = _dose_taxa_por_tonelada(bloco["k"], produtividade_estimada)
            return {"n": n, "p2o5": p2o5, "k2o": k2o}
        raise NotImplementedError(
            f"cultura '{cultura_id}': manutenção com indexação '{bloco.get('indexacao')}' ainda não "
            f"implementada — formato próprio da cultura, precisa de caso de teste calculado à mão "
            f"antes de codificar (mesma política de graos_pd_com_restricoes)"
        )

    raise ErroAdubacao(f"'fase' deve ser 'pre_plantio', 'crescimento' ou 'manutencao', recebido {fase!r}")


def calcular_adubacao_erva_mate(
    programa: str,
    mo: Optional[float] = None,
    argila: Optional[float] = None,
    p_solo: Optional[float] = None,
    k_solo: Optional[float] = None,
    ctc_ph7: Optional[float] = None,
    fase: Optional[str] = None,
    momento: Optional[str] = None,
    manejo_galho_grosso: Optional[str] = None,
    massa_verde_t_ha: Optional[float] = None,
    dados_erva_mate: Optional[Dict[str, Any]] = None,
    dados_comuns: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calcula N/P2O5/K2O para erva-mate (Seção 6.6.5), programa 'desde_o_plantio'
    (fases 'plantio_e_crescimento', 'formacao_da_copa' ou 'producao') ou 'recuperacao'.
    """
    dados_erva_mate = dados_erva_mate if dados_erva_mate is not None else carregar_dados_erva_mate()
    dados_comuns = dados_comuns if dados_comuns is not None else carregar_dados_comum()
    adubacao = dados_erva_mate["adubacao"]
    entrada = adubacao["culturas"]["erva_mate"]
    classes_mo = adubacao["classes_mo"]

    if programa == "desde_o_plantio":
        bloco_programa = entrada["programa_desde_o_plantio"]
        if fase not in bloco_programa:
            raise ErroAdubacao(f"fase '{fase}' inválida para programa 'desde_o_plantio'")
        bloco_fase = bloco_programa[fase]

        if fase == "plantio_e_crescimento":
            if momento is None:
                raise ErroAdubacao("'momento' é obrigatório na fase 'plantio_e_crescimento'")
            classe_p, classe_k = _classificar_p_e_k(entrada, "erva_mate", argila, p_solo, k_solo, ctc_ph7, dados_comuns)
            n, _ = _calcular_n_generico(bloco_fase["n"], classes_mo, mo, momento)
            p2o5 = _navegar(bloco_fase["p"]["doses"], classe_p, momento)
            k2o = _navegar(bloco_fase["k"]["doses"], classe_k, momento)
            return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "p2o5": p2o5, "k2o": k2o}

        if fase == "formacao_da_copa":
            classe_p, classe_k = _classificar_p_e_k(entrada, "erva_mate", argila, p_solo, k_solo, ctc_ph7, dados_comuns)
            n, _ = _calcular_n_generico(bloco_fase["n"], classes_mo, mo, None)
            p2o5, k2o = _calcular_pk_generico(bloco_fase["pk"], classe_p, classe_k, None)
            return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "p2o5": p2o5, "k2o": k2o}

        if fase == "producao":
            if manejo_galho_grosso is None or massa_verde_t_ha is None:
                raise ErroAdubacao("'manejo_galho_grosso' e 'massa_verde_t_ha' são obrigatórios na fase 'producao'")
            # producao/recuperacao nao declaram "classes_mo" no proprio bloco (as
            # chaves de coeficientes/parametros ja usam os ids de "padrao" direto).
            faixa_mo = _classe_mo(mo, classes_mo["padrao"])
            coef_n = bloco_fase["n"]["coeficientes"][faixa_mo][manejo_galho_grosso]
            n = coef_n * massa_verde_t_ha
            coef_pk = bloco_fase["pk"]["coeficientes"][manejo_galho_grosso]
            p2o5 = coef_pk["p"] * massa_verde_t_ha
            k2o = coef_pk["k"] * massa_verde_t_ha
            return {"n": n, "p2o5": p2o5, "k2o": k2o}

        raise NotImplementedError(f"fase '{fase}' ainda não implementada")

    if programa == "recuperacao":
        bloco = entrada["programa_recuperacao"]
        if manejo_galho_grosso is None or massa_verde_t_ha is None:
            raise ErroAdubacao("'manejo_galho_grosso' e 'massa_verde_t_ha' são obrigatórios no programa 'recuperacao'")

        classe_p, classe_k = _classificar_p_e_k(entrada, "erva_mate", argila, p_solo, k_solo, ctc_ph7, dados_comuns)

        faixa_mo = _classe_mo(mo, classes_mo["padrao"])
        parametros_n = bloco["n"]["parametros"][faixa_mo][manejo_galho_grosso]
        n = parametros_n["base"] + parametros_n["coeficiente"] * massa_verde_t_ha

        classes_atendidas = bloco["pk"]["classes_atendidas"]

        def _dose_recuperacao(classe: str, nutriente: str) -> float:
            if classe not in classes_atendidas:
                raise ErroAdubacao(
                    f"classe '{classe}' não está no programa de recuperação para '{nutriente}' "
                    f"(fora de {classes_atendidas}) — o nutriente segue o regime normal de produção"
                )
            base = bloco["pk"]["parametros"][classe][nutriente]["base"]
            coeficiente = bloco["pk"]["coeficientes_por_manejo"][manejo_galho_grosso][nutriente]
            return base + coeficiente * massa_verde_t_ha

        p2o5 = _dose_recuperacao(classe_p, "p")
        k2o = _dose_recuperacao(classe_k, "k")
        return {"classe_p": classe_p, "classe_k": classe_k, "n": n, "p2o5": p2o5, "k2o": k2o}

    raise ErroAdubacao(f"'programa' deve ser 'desde_o_plantio' ou 'recuperacao', recebido {programa!r}")
