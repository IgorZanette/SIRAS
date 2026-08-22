"""
Cálculo de adubação de grãos: nitrogênio (por MO/antecedente) e fósforo/potássio
(classificação do teor do solo + algoritmo de dose por classe, Cap. 6 do Manual).

Escopo atual: apenas grupo "graos", cultivo 1 e 2 (dose de correção completa / reduzida em
rotação). Hortaliças, frutíferas e demais grupos ainda não estão implementados.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from siras.conhecimento.carregador import carregar_dados_comum, carregar_dados_graos


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


def _dose_pk(classe: str, cultivo: int, correcao_nutriente: Optional[float], manutencao_valor: float) -> float:
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
        # Manual: cultivo 1 = 0; cultivo 2 = "<= manutencao (reposicao, a criterio do
        # tecnico)" — facultativo, não determinístico. Decisão do SIRAS (a registrar em
        # ADR, análoga a D8): usar a manutenção como teto e sinalizar que é opcional.
        return 0.0 if cultivo == 1 else manutencao_valor
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
        Dict com "classe_p", "classe_k", "p2o5", "k2o"

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
