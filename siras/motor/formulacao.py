"""
Como atender a recomendação com produto — três caminhos (ADR 0009).

O laudo entrega a recomendação em nutriente; a revenda vende adubo. A ponte entre as duas
coisas não tem resposta única, porque **não existe catálogo oficial de fórmulas
comercializadas no Brasil**: o MAPA registra milhares de produtos, boa parte é feita sob
encomenda, e fabricantes sequer publicam garantias. Em vez de fingir que uma lista fechada
resolve, o módulo entrega três respostas e deixa a escolha com quem compra:

    A. fórmula ideal ....... a proporção exata, em três concentrações. Para encomendar
    B. melhores do catálogo  o que se encontra na revenda, inclusive o que o usuário tem
    C. mistura de simples .. ureia + superfosfato triplo + KCl. Sempre exata, sempre há

A REGRA DE DOSE (D1). Para uma fórmula de teores f e dose d, o custo é

    custo(d) = W_EXC·Σ max(0, d·fᵢ/100 − rᵢ)        sobre N, P, K
             + W_FALTA·Σ max(0, rᵢ − d·fᵢ/100)      sobre P, K
             + W_OP·(nº de complementos de P e K)

Os dois primeiros termos são lineares por partes e convexos em d; soma de convexas é
convexa; e o mínimo de uma função linear por partes convexa está num ponto de quebra.
Basta então avaliar d ∈ {r_P·100/f_P, r_K·100/f_K}. A regra do Manual ("ajustar ao
nutriente mais deficiente") é UM desses dois pontos — avaliar os dois nunca piora o
resultado, o que o teste T8 verifica sobre uma grade em vez de afirmar.

FRONTEIRA DE FONTE. O método é do Manual (§8.3, p. 310-311) e as garantias dos simples são
da Tab. 8.4, p. 304. O catálogo de fórmulas NÃO é: é dado de mercado, com fonte por
entrada. Os pesos de D4 são decisão do autor, declarada na ADR com sua fragilidade.

O que o Manual manda e este módulo não faz: escolher pelo menor custo por unidade de NPK
(p. 310). O SIRAS não tem preços — são de quem compra — e o laudo diz isso.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from siras.dominio.laudo import (
    Complemento,
    OpcaoAdubacao,
    RecomendacaoAdubacao,
    ResultadoFormulacao,
)
from siras.motor.trace import Trace

# --- constantes do método (ADR 0009) ------------------------------------------------
#
# Nomeadas e num lugar só, de propósito. Não são configuráveis pela interface: são
# parâmetros do método, não preferência de uso.

#: Peso do nutriente aplicado acima do recomendado, por kg. É o mais caro: já foi
#: comprado e aplicado, e não há como desfazer.
W_EXC = 1.0
#: Peso do nutriente que falta, por kg. Menor que o excesso porque a falta ainda pode ser
#: corrigida com fonte simples — o que é justamente o que o módulo faz.
W_FALTA = 0.2
#: Custo de cada produto de complemento de P ou K. Representa a operação de campo a mais.
#: Mistura unidades com os dois acima de propósito, e a ADR declara a fragilidade: afirma
#: que uma operação custa o mesmo que 10 kg de nutriente desperdiçado.
W_OP = 10.0

#: Abaixo disto o complemento não compensa uma passada de máquina.
COMPLEMENTO_MINIMO_KG_HA = 0.5

#: Concentrações alvo da fórmula ideal: o maior entre P2O5 e K2O vale T (D10). Os três
#: valores reproduzem as três fórmulas do exemplo do Manual, p. 311.
ALVOS_DE_CONCENTRACAO = (18, 24, 30)

#: Fontes simples de cada nutriente, por id em fertilizantes_simples (D6).
FONTE_DE_P = "superfosfato_triplo"
FONTE_DE_K = "cloreto_de_potassio"
FONTE_DE_N = "ureia"

#: Quantas fórmulas do catálogo o laudo mostra (D7).
TOP_DO_CATALOGO = 3

#: Uso filtrado no catálogo: o laudo publica a recomendação de implantação, e o N de
#: cobertura sai nomeado, como complemento.
USO_PADRAO = "plantio"

CRITERIO = (
    "dose no ponto de quebra de menor custo, com excesso pesando 1,0/kg, falta 0,2/kg e "
    "cada operação de complemento 10; desempate pela menor massa total aplicada "
    "(ADR 0009; método do Manual, §8.3, p. 311)"
)

#: Avisos fixos do laudo (D12). Ficam aqui, e não no template, para que a regra e o texto
#: que a descreve não possam divergir.
AVISOS = (
    "O critério de escolha é nutricional, não financeiro: o SIRAS não tem preços. O "
    "Manual (p. 310) orienta comparar o custo por unidade de NPK, somado a frete e "
    "aplicação — faça essa conta com os preços da sua revenda.",
    "Fórmulas mais concentradas tendem a trazer menos enxofre. Confira o teor e a forma "
    "do S no rótulo (Manual, p. 311).",
    "Ao misturar adubos simples, confira a compatibilidade entre os produtos antes de "
    "homogeneizar (Manual, Fig. 8.2).",
)

#: Formato aceito para a fórmula que o usuário informa (D11).
_FORMATO_FORMULA = re.compile(r"^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*$")

#: Mínimos legais de soma NPK da IN 39/2018, art. 9. Abaixo disso é aviso, não erro: pode
#: ser organomineral, cujo mínimo é menor.
SOMA_MINIMA_TERNARIA = 18
SOMA_MINIMA_BINARIA = 15

NUTRIENTES = ("n", "p2o5", "k2o")


class ErroFormulacao(Exception):
    """Fórmula do usuário em formato que não dá para interpretar."""


# --- entrada ------------------------------------------------------------------------

def _dose_numerica(dose: Any) -> Optional[float]:
    """O valor da dose quando ela É um número, e None quando não é.

    Mesma regra do total a comprar: o Manual nem sempre publica um número — há teto
    ("<= manutenção"), intervalo e lacuna declarada (ADR 0004). Dividir qualquer um deles
    pela garantia de um adubo produziria uma dose com precisão que a fonte não dá.
    """
    if isinstance(dose, bool) or not isinstance(dose, (int, float)):
        return None
    return float(dose)


def interpretar_formula_do_usuario(texto: str) -> Dict[str, Any]:
    """Converte "NN-NN-NN" numa entrada de catálogo, com os avisos que couberem (D11).

    Formato inválido levanta erro: não há como adivinhar o que a pessoa quis dizer. Soma
    abaixo do mínimo legal é só AVISO, porque pode ser organomineral, cujo mínimo é menor.

    Raises:
        ErroFormulacao: texto fora do formato N-P-K.
    """
    casamento = _FORMATO_FORMULA.match(texto or "")
    if not casamento:
        raise ErroFormulacao(
            f"'{texto}' não está no formato de uma fórmula. Escreva as três garantias do "
            f"rótulo separadas por hífen, como em 05-20-20"
        )
    n, p, k = (int(g) for g in casamento.groups())
    soma = n + p + k
    avisos: List[str] = []
    if soma > 100:
        raise ErroFormulacao(
            f"as garantias de '{texto}' somam {soma}% — são porcentagens em massa do "
            f"mesmo produto e não podem passar de 100%"
        )
    if soma <= 0:
        raise ErroFormulacao(f"'{texto}' não entrega N, P2O5 nem K2O")

    ternaria = all(v > 0 for v in (n, p, k))
    minimo = SOMA_MINIMA_TERNARIA if ternaria else SOMA_MINIMA_BINARIA
    if soma < minimo:
        avisos.append(
            f"A fórmula {n:02d}-{p:02d}-{k:02d} soma {soma}%, abaixo do mínimo de "
            f"{minimo}% que a IN 39/2018 exige de um fertilizante mineral "
            f"{'ternário' if ternaria else 'binário'}. Confira o rótulo — se for "
            f"organomineral, o mínimo é outro."
        )
    return {
        "id": f"{n:02d}-{p:02d}-{k:02d}",
        "n": float(n), "p2o5": float(p), "k2o": float(k),
        "uso": [USO_PADRAO],
        "fontes": [], "origem": "informada_pelo_usuario",
        "_avisos": avisos,
    }


# --- custo e avaliação ---------------------------------------------------------------

def _complementos(
    falta: Dict[str, float], n_cobertura: float, simples: Dict[str, Dict[str, Any]]
) -> Tuple[Complemento, ...]:
    """Fertilizantes simples para o que a fórmula não cobriu."""
    itens: List[Complemento] = []
    for nutriente, id_fonte in (("p2o5", FONTE_DE_P), ("k2o", FONTE_DE_K)):
        kg = falta.get(nutriente, 0.0)
        fonte = simples.get(id_fonte)
        if kg <= COMPLEMENTO_MINIMO_KG_HA or not fonte or not fonte.get(nutriente):
            continue
        itens.append(Complemento(
            produto=id_fonte, dose_kg_ha=kg * 100.0 / fonte[nutriente],
            nutriente=nutriente, momento="plantio",
        ))
    fonte_n = simples.get(FONTE_DE_N)
    if n_cobertura > COMPLEMENTO_MINIMO_KG_HA and fonte_n and fonte_n.get("n"):
        itens.append(Complemento(
            produto=FONTE_DE_N, dose_kg_ha=n_cobertura * 100.0 / fonte_n["n"],
            nutriente="n", momento="cobertura",
        ))
    return tuple(itens)


def _avaliar_dose(
    teores: Dict[str, float], rec: Dict[str, float], dose: float,
    simples: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Fornecido, excesso, falta, complementos, custo e massa total de uma dose."""
    fornecido = {i: dose * teores[i] / 100.0 for i in NUTRIENTES}

    excesso, falta = {}, {}
    for i in NUTRIENTES:
        saldo = rec[i] - fornecido[i]
        # O 0.0 primeiro de propósito: max(-0.0, 0.0) devolveria -0.0, que imprime "-0".
        falta[i] = max(0.0, saldo)
        excesso[i] = max(0.0, -saldo)

    # O N que falta não é "falta" para efeito de custo: vai para cobertura, que existe em
    # qualquer opção e por isso não distingue uma da outra (D5). Só o excesso de N pesa.
    n_cobertura = falta["n"]
    complementos = _complementos(falta, n_cobertura, simples)
    operacoes = sum(1 for c in complementos if c.momento == "plantio")

    custo = (
        W_EXC * sum(excesso[i] for i in NUTRIENTES)
        + W_FALTA * (falta["p2o5"] + falta["k2o"])
        + W_OP * operacoes
    )
    massa = dose + sum(c.dose_kg_ha for c in complementos)

    return {
        "dose": dose, "fornecido": fornecido, "excesso": excesso, "falta": falta,
        "complementos": complementos, "custo": custo, "massa": massa,
    }


def _pontos_de_quebra(teores: Dict[str, float], rec: Dict[str, float]) -> List[Tuple[str, float]]:
    """As doses candidatas: a que cobre o P e a que cobre o K, quando existirem (D1)."""
    candidatos = []
    for nutriente in ("p2o5", "k2o"):
        if rec[nutriente] > 0 and teores[nutriente] > 0:
            candidatos.append((nutriente, rec[nutriente] * 100.0 / teores[nutriente]))
    return candidatos


def _montar_opcao(
    tipo: str, formula: Dict[str, Any], rec: Dict[str, float],
    simples: Dict[str, Dict[str, Any]],
) -> Optional[OpcaoAdubacao]:
    """Avalia uma fórmula nos seus pontos de quebra e devolve o melhor.

    None quando a fórmula não contém nenhum dos nutrientes exigidos: sem ponto de quebra
    não há dose a propor, e arbitrar uma seria inventar a resposta.
    """
    teores = {i: float(formula[i]) for i in NUTRIENTES}
    candidatos = _pontos_de_quebra(teores, rec)
    if not candidatos:
        return None

    avaliados = [(ancora, _avaliar_dose(teores, rec, dose, simples))
                 for ancora, dose in candidatos]
    # Empate de custo entre os dois pontos resolve pela menor massa, como no desempate
    # entre fórmulas (D9) — coerência, e evita depender da ordem da lista.
    ancora, melhor = min(avaliados, key=lambda par: (par[1]["custo"], par[1]["massa"]))
    melhor["candidatos"] = {a: (d["dose"], d["custo"]) for a, d in avaliados}

    return OpcaoAdubacao(
        tipo=tipo, formula_id=formula["id"], dose_kg_ha=melhor["dose"], ancora=ancora,
        fornecido=melhor["fornecido"], excesso=melhor["excesso"], falta=melhor["falta"],
        complementos=melhor["complementos"], custo=melhor["custo"],
        massa_total_kg_ha=melhor["massa"], teores=teores,
        fontes=list(formula.get("fontes") or []), origem=formula.get("origem", ""),
        candidatos=melhor["candidatos"],
    )


# --- caminho A: fórmula ideal ---------------------------------------------------------

def formula_ideal(
    rec: Dict[str, float], n_plantio: float, simples: Dict[str, Dict[str, Any]],
) -> List[OpcaoAdubacao]:
    """A proporção exata da recomendação, em três concentrações (D10).

    Escala a recomendação para que o maior entre P2O5 e K2O valha T, arredonda as
    garantias ao inteiro e calcula a dose pelo nutriente de maior valor. Com N de plantio
    10, P2O5 120 e K2O 80, produz 02-18-12 (667), 02-24-16 (500) e 03-30-20 (400) — as
    três fórmulas do exemplo do Manual, p. 311, com as doses que ele publica.

    A soma das garantias é sempre ≥ T, porque o maior teor já vale T, o que atende o
    mínimo legal da IN 39/2018 para os três alvos.

    `n_plantio` zero produz fórmula binária P-K e manda todo o N para cobertura: é o que
    acontece quando o usuário não informa a parcela de semeadura, e o laudo declara.
    """
    maior = max(rec["p2o5"], rec["k2o"])
    if maior <= 0:
        return []

    proporcao = {"n": n_plantio / maior, "p2o5": rec["p2o5"] / maior, "k2o": rec["k2o"] / maior}
    eixo = "p2o5" if rec["p2o5"] >= rec["k2o"] else "k2o"

    opcoes: List[OpcaoAdubacao] = []
    vistos = set()
    for alvo in ALVOS_DE_CONCENTRACAO:
        # Arredondamento de meio para cima, como a política do trabalho: int(x + 0.5)
        # em vez de round(), que em Python arredonda meio para o par.
        teores = {i: float(int(proporcao[i] * alvo + 0.5)) for i in NUTRIENTES}
        if teores[eixo] <= 0:
            continue
        identificador = "-".join(f"{int(teores[i]):02d}" for i in NUTRIENTES)
        if identificador in vistos:
            continue
        vistos.add(identificador)

        dose = rec[eixo] * 100.0 / teores[eixo]
        avaliado = _avaliar_dose(teores, rec, dose, simples)
        opcoes.append(OpcaoAdubacao(
            tipo="ideal", formula_id=identificador, dose_kg_ha=dose, ancora=eixo,
            fornecido=avaliado["fornecido"], excesso=avaliado["excesso"],
            falta=avaliado["falta"], complementos=avaliado["complementos"],
            custo=avaliado["custo"], massa_total_kg_ha=avaliado["massa"], teores=teores,
        ))
    return opcoes


# --- caminho C: mistura de simples ----------------------------------------------------

def mistura_simples(
    rec: Dict[str, float], simples: Dict[str, Dict[str, Any]],
) -> Optional[OpcaoAdubacao]:
    """Ureia, superfosfato triplo e cloreto de potássio, nas doses exatas.

    É a régua das outras duas: sempre atende a recomendação na medida, e sempre está
    disponível. O custo é zero por construção, e por isso ela não entra no ranking do
    catálogo — ela é a referência contra a qual os desvios das outras se leem.
    """
    itens: List[Complemento] = []
    for nutriente, id_fonte, momento in (
        ("p2o5", FONTE_DE_P, "plantio"),
        ("k2o", FONTE_DE_K, "plantio"),
        ("n", FONTE_DE_N, "cobertura"),
    ):
        kg = rec[nutriente]
        fonte = simples.get(id_fonte)
        if kg <= COMPLEMENTO_MINIMO_KG_HA or not fonte or not fonte.get(nutriente):
            continue
        itens.append(Complemento(
            produto=id_fonte, dose_kg_ha=kg * 100.0 / fonte[nutriente],
            nutriente=nutriente, momento=momento,
        ))
    if not itens:
        return None

    zerado = {i: 0.0 for i in NUTRIENTES}
    return OpcaoAdubacao(
        tipo="mistura_simples", formula_id=None, dose_kg_ha=0.0, ancora=None,
        fornecido=dict(rec), excesso=dict(zerado), falta=dict(zerado),
        complementos=tuple(itens), custo=0.0,
        massa_total_kg_ha=sum(c.dose_kg_ha for c in itens),
    )


# --- ponto de entrada -----------------------------------------------------------------

def _chave_de_ordem(opcao: OpcaoAdubacao):
    """Menor custo; empate pela menor massa total (D9); depois dose; depois id.

    O id entra por último só para a ordem ser determinística quando duas fórmulas empatam
    em tudo — sem ele a saída dependeria da ordem do arquivo, e o laudo deixaria de ser
    reprodutível.
    """
    return (opcao.custo, opcao.massa_total_kg_ha, opcao.dose_kg_ha, opcao.formula_id or "")


def recomendar_formulacao(
    adubacao: RecomendacaoAdubacao,
    catalogo: Dict[str, Any],
    trace: Optional[Trace] = None,
    n_plantio: Optional[float] = None,
    formulas_usuario: Sequence[str] = (),
    uso: str = USO_PADRAO,
) -> ResultadoFormulacao:
    """Os três caminhos para atender a recomendação (ADR 0009).

    Args:
        adubacao: a recomendação emitida. `n` é o N **total** — a base publica a dose como
            "semeadura + cobertura", e é sobre o total que o saldo de cobertura se calcula
        catalogo: conteúdo de dados/mercado/formulas_npk.json
        trace: opcional; recebe os passos R-FOR-01 e R-FOR-02
        n_plantio: parcela do N na semeadura, informada pelo usuário. None vale 0 e a
            fórmula ideal sai binária, com a ressalva declarada na saída
        formulas_usuario: fórmulas que o usuário tem, no formato "NN-NN-NN" (D11)
        uso: filtra o catálogo por momento de aplicação

    Returns:
        ResultadoFormulacao com os três caminhos. Catálogo vazio deixa `catalogo` vazia e
        os outros dois seguem; sem dose numérica de P e K os três vêm vazios e
        `motivo_sem_indicacao` diz por quê. Nunca levanta exceção por falta de dado — um
        laudo sem formulação continua completo.

    As doses saem SEM arredondamento. Arredondar aqui repetiria o defeito B-8 do CCAE, em
    que um valor arredondado cedo passou a decidir um corte.
    """
    rec = {
        "n": _dose_numerica(adubacao.n) or 0.0,
        "p2o5": _dose_numerica(adubacao.p2o5) or 0.0,
        "k2o": _dose_numerica(adubacao.k2o) or 0.0,
    }
    simples = {
        item["id"]: item
        for item in (catalogo.get("fertilizantes_simples") or {}).get("itens") or []
    }
    avisos = list(AVISOS)

    if rec["p2o5"] <= 0 and rec["k2o"] <= 0:
        motivo = (
            "a recomendação não traz dose numérica de P2O5 nem de K2O, e é por esses dois "
            "que a dose de um adubo formulado se dimensiona"
        )
        if trace is not None:
            trace.registrar(
                regra="R-FOR-01: formulação do adubo",
                entradas={"p2o5": adubacao.p2o5, "k2o": adubacao.k2o, "n": adubacao.n},
                saida={"caminhos": 0, "motivo": motivo},
                fonte="Método: Manual 2016, §8.3, p. 311",
            )
        # A mistura de simples ainda faz sentido quando só há N: ureia resolve.
        return ResultadoFormulacao(
            mistura=mistura_simples(rec, simples), avisos=avisos,
            motivo_sem_indicacao=motivo, criterio=CRITERIO,
        )

    # --- caminho A
    sem_n = n_plantio is None
    ideais = formula_ideal(rec, 0.0 if sem_n else float(n_plantio), simples)

    # --- caminho B
    do_catalogo = [
        ("catalogo", f) for f in ((catalogo.get("formulas") or {}).get("itens") or [])
        if uso in (f.get("uso") or [])
    ]
    for texto in formulas_usuario:
        entrada = interpretar_formula_do_usuario(texto)
        avisos.extend(entrada.pop("_avisos", []))
        do_catalogo.append(("usuario", entrada))

    avaliadas = [
        opcao for opcao in (
            _montar_opcao(tipo, f, rec, simples) for tipo, f in do_catalogo
        ) if opcao is not None
    ]
    melhores = sorted(avaliadas, key=_chave_de_ordem)[:TOP_DO_CATALOGO]

    # A trilha registra os pontos de quebra SÓ das fórmulas que o laudo mostra. Registrar
    # as 38 avaliadas encheria o documento impresso com a varredura inteira, e a
    # deduplicação por (regra, fonte) ainda juntaria todas numa linha só — exibindo os
    # números de uma delas com a contagem de todas, que é pior do que não registrar.
    # Quantas foram avaliadas fica dito no passo R-FOR-01, logo abaixo.
    if trace is not None:
        for opcao in melhores:
            trace.registrar(
                regra=f"R-FOR-02 ({opcao.formula_id}): pontos de quebra",
                entradas={"tipo": opcao.tipo,
                          "doses_candidatas": {a: round(d, 2)
                                               for a, (d, _c) in opcao.candidatos.items()}},
                saida={"ancora": opcao.ancora, "dose_kg_ha": opcao.dose_kg_ha,
                       "custos": {a: round(c, 3) for a, (_d, c) in opcao.candidatos.items()}},
                fonte="ADR 0009, D1 — mínimo de função convexa linear por partes",
            )

    # --- caminho C
    mistura = mistura_simples(rec, simples)

    if trace is not None:
        trace.registrar(
            regra="R-FOR-01: formulação do adubo",
            entradas={
                "n_total": rec["n"], "p2o5": rec["p2o5"], "k2o": rec["k2o"],
                "n_plantio": n_plantio, "formulas_avaliadas": len(avaliadas),
                "formulas_do_usuario": len(formulas_usuario), "uso": uso,
            },
            saida={
                "ideais": [o.formula_id for o in ideais],
                "catalogo": [o.formula_id for o in melhores],
                "melhor_custo": melhores[0].custo if melhores else None,
                "mistura": bool(mistura),
            },
            fonte=(
                "Método: Manual 2016, §8.3, p. 311 e Tab. 8.4, p. 304; dose no ponto de "
                "quebra de menor custo (ADR 0009). Catálogo de fórmulas: "
                "dados/mercado/formulas_npk.json — dado de mercado, não é fonte do Manual"
            ),
        )

    return ResultadoFormulacao(
        ideais=ideais, catalogo=melhores, mistura=mistura, avisos=avisos,
        sem_n_de_plantio=sem_n, criterio=CRITERIO,
    )


__all__ = [
    "ALVOS_DE_CONCENTRACAO",
    "AVISOS",
    "CRITERIO",
    "ErroFormulacao",
    "W_EXC",
    "W_FALTA",
    "W_OP",
    "formula_ideal",
    "interpretar_formula_do_usuario",
    "mistura_simples",
    "recomendar_formulacao",
]
