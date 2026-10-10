"""
Escolha do adubo formulado que atende a recomendação — método do Manual, §8.3, p. 311.

O laudo entrega a recomendação em nutriente: tantos kg/ha de N, P2O5 e K2O. A revenda
vende adubo formulado. Este módulo faz a ponte, e faz pelo procedimento que o próprio
Manual descreve, em quatro passos:

1. a fórmula adequada é múltipla da **proporção** da recomendação;
2. quando não há fórmula exata, a dose se ajusta ao **nutriente mais deficiente no
   solo**, que por isso é atendido exatamente;
3. o N que a fórmula traz é descontado do N total, e o **saldo vai para cobertura**;
4. o que faltar de P ou K vai para **complemento** com fertilizante simples; o que
   sobrar é adubo pago e não aproveitado.

Fronteira de fonte, que importa para a banca. O **método** é do Manual. O **catálogo**
(dados/mercado/formulas_npk.json) não é: é dado de mercado, com fonte declarada por
entrada, porque o Manual não publica — e não teria por que publicar — a lista de
formulações que a indústria vende. As garantias dos fertilizantes simples usados nos
complementos vêm da Tab. 8.4, p. 304.

O que o Manual manda e este módulo **não** faz: escolher pelo menor custo por unidade de
NPK (p. 310). O SIRAS não tem preços — eles são de quem compra, e entram na calculadora
de custo, fora do laudo. O ranking aqui é **nutricional**, e o laudo diz isso.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from siras.dominio.laudo import Complemento, IndicacaoFormulacao, OpcaoFormulacao, RecomendacaoAdubacao
from siras.motor.trace import Trace

#: Ordem das classes de disponibilidade do Manual. Índice menor = mais deficiente, e é
#: essa ordem que decide a âncora da dose.
ORDEM_CLASSES = ("muito_baixo", "baixo", "medio", "alto", "muito_alto")

#: Fonte simples usada para cobrir o que a fórmula não entregou, por nutriente. Decisão
#: do autor entre as fontes da Tab. 8.4: as mais concentradas de cada nutriente, para
#: minimizar massa transportada. Registrada na ADR 0008.
FONTE_DE_COMPLEMENTO = {"p2o5": "superfosfato_triplo", "k2o": "cloreto_de_potassio"}
FONTE_DE_COBERTURA_N = "ureia"

#: Abaixo disto o complemento não compensa uma operação de campo a mais. Decisão do
#: autor, ADR 0008.
COMPLEMENTO_MINIMO_KG_HA = 0.5

#: Uso da fórmula que o laudo indica. O laudo publica a recomendação de implantação da
#: cultura, não a de cobertura — o N de cobertura sai como complemento, nomeado.
USO_PADRAO = "plantio"

CRITERIO = (
    "dose ancorada no nutriente mais deficiente no solo, que é atendido exatamente "
    "(Manual, §8.3, p. 311); o que faltar do outro vai para complemento e o N restante "
    "para cobertura; ranking pelo menor desvio relativo, com desempate pela fórmula mais "
    "concentrada"
)


class ErroFormulacao(Exception):
    """Catálogo malformado a ponto de a aritmética não fazer sentido."""


def _dose_numerica(dose: Any) -> Optional[float]:
    """O valor da dose quando ela É um número, e None quando não é.

    Mesma regra do total a comprar (relatorio/apresentacao.py, _dose_somavel): o Manual
    nem sempre publica um número — há teto ("<= manutenção"), intervalo e lacuna
    declarada. Dividir qualquer um deles pela garantia de um adubo produziria uma dose de
    produto com precisão que a fonte não dá.
    """
    if isinstance(dose, bool) or not isinstance(dose, (int, float)):
        return None
    return float(dose)


def escolher_ancora(
    p2o5: float, k2o: float, classe_p: Optional[str], classe_k: Optional[str]
) -> Tuple[Optional[str], bool]:
    """O nutriente que define a dose, e se a escolha caiu no fallback.

    O Manual manda ancorar no "nutriente mais deficiente no solo" — isto é, o de classe
    de teor mais baixa. Duas situações que o Manual não trata e que são decisão do autor,
    declaradas na ADR 0008:

    - **empate de classe:** ancora no de MAIOR dose recomendada;
    - **classe ausente:** há fases de frutífera que não dosam por classe de teor, e nelas
      não há como saber qual nutriente está mais deficiente. Ancora no de maior dose e
      devolve `True` no segundo elemento, para que a trilha e o laudo digam que a âncora
      não veio da classe. Mentir por omissão aqui seria pior do que não indicar.
    """
    candidatos = [
        (chave, dose, classe)
        for chave, dose, classe in (("p2o5", p2o5, classe_p), ("k2o", k2o, classe_k))
        if dose > 0
    ]
    if not candidatos:
        return None, False

    fallback = any(classe not in ORDEM_CLASSES for _c, _d, classe in candidatos)
    if fallback:
        candidatos.sort(key=lambda c: -c[1])
    else:
        candidatos.sort(key=lambda c: (ORDEM_CLASSES.index(c[2]), -c[1]))
    return candidatos[0][0], fallback


def _complementos(
    falta: Dict[str, float], n_cobertura: float, simples: Dict[str, Dict[str, Any]]
) -> List[Complemento]:
    """Fertilizantes simples para o que a fórmula não cobriu."""
    itens: List[Complemento] = []
    for nutriente in ("p2o5", "k2o"):
        kg = falta[nutriente]
        if kg <= COMPLEMENTO_MINIMO_KG_HA:
            continue
        fonte = simples.get(FONTE_DE_COMPLEMENTO[nutriente])
        if not fonte or not fonte.get(nutriente):
            continue
        itens.append(Complemento(
            produto=fonte["id"],
            dose_kg_ha=kg * 100.0 / fonte[nutriente],
            nutriente=nutriente,
        ))
    if n_cobertura > COMPLEMENTO_MINIMO_KG_HA:
        fonte = simples.get(FONTE_DE_COBERTURA_N)
        if fonte and fonte.get("n"):
            itens.append(Complemento(
                produto=fonte["id"],
                dose_kg_ha=n_cobertura * 100.0 / fonte["n"],
                nutriente="n",
                momento="cobertura",
            ))
    return itens


def _avaliar(
    formula: Dict[str, Any],
    rec_n: Optional[float],
    rec_p: float,
    rec_k: float,
    ancora: str,
    por_fallback: bool,
    simples: Dict[str, Dict[str, Any]],
) -> Optional[OpcaoFormulacao]:
    """Dose, entrega, falta, excesso e complementos de uma fórmula. None se ela não serve.

    Uma fórmula sem o nutriente-âncora não serve: a regra de três da dose dividiria por
    zero, e ancorar no outro nutriente mudaria o método no meio do ranking.
    """
    teor = {chave: float(formula[chave]) for chave in ("n", "p2o5", "k2o")}
    if teor[ancora] <= 0:
        return None

    necessidade = {"p2o5": rec_p, "k2o": rec_k}
    dose = necessidade[ancora] * 100.0 / teor[ancora]
    entrega = {chave: dose * teor[chave] / 100.0 for chave in ("n", "p2o5", "k2o")}

    falta: Dict[str, float] = {}
    excesso: Dict[str, float] = {}
    for chave in ("p2o5", "k2o"):
        saldo = necessidade[chave] - entrega[chave]
        # O 0.0 vem primeiro de propósito: max(-0.0, 0.0) devolveria -0.0, que imprime
        # como "-0" no laudo.
        falta[chave] = max(0.0, saldo)
        excesso[chave] = max(0.0, -saldo)

    # N sem número publicado (teto, intervalo, lacuna) não tem com o que ser comparado:
    # não há excesso a afirmar, nem saldo de cobertura a calcular.
    if rec_n is None:
        excesso_n = 0.0
        n_cobertura = 0.0
    else:
        excesso_n = max(0.0, entrega["n"] - rec_n)
        n_cobertura = max(0.0, rec_n - entrega["n"])

    # Falta e excesso pesam igual: falta exige uma operação a mais, excesso é adubo pago
    # e não aproveitado. Peso igual é decisão do autor (ADR 0008).
    alvo = rec_p + rec_k
    desvio = (
        falta["p2o5"] + falta["k2o"] + excesso["p2o5"] + excesso["k2o"] + excesso_n
    ) / alvo

    return OpcaoFormulacao(
        id=formula["id"],
        n=teor["n"], p2o5=teor["p2o5"], k2o=teor["k2o"],
        dose_kg_ha=dose,
        entrega_n=entrega["n"], entrega_p2o5=entrega["p2o5"], entrega_k2o=entrega["k2o"],
        falta_p2o5=falta["p2o5"], falta_k2o=falta["k2o"],
        excesso_p2o5=excesso["p2o5"], excesso_k2o=excesso["k2o"], excesso_n=excesso_n,
        n_cobertura=n_cobertura,
        desvio_relativo=desvio,
        ancora=ancora,
        ancora_por_fallback=por_fallback,
        complementos=_complementos(falta, n_cobertura, simples),
        fontes=list(formula.get("fontes") or []),
        origem=formula.get("origem", ""),
    )


def indicar_formulacao(
    adubacao: RecomendacaoAdubacao,
    catalogo: Dict[str, Any],
    trace: Optional[Trace] = None,
    uso: str = USO_PADRAO,
) -> IndicacaoFormulacao:
    """Escolhe a formulação NPK que melhor atende a recomendação de adubação.

    Args:
        adubacao: a recomendação já emitida. `n` é o N **total** — a base publica a dose
            de N como "semeadura + cobertura" (graos_adubacao_n.json), e é sobre o total
            que o passo 3 do Manual desconta o N da fórmula
        catalogo: conteúdo de dados/mercado/formulas_npk.json
        trace: opcional; recebe o passo R-FOR-01 quando informado
        uso: filtra o catálogo por momento de aplicação ("plantio" ou "cobertura")

    Returns:
        IndicacaoFormulacao. Quando não há o que indicar — catálogo vazio, recomendação
        sem dose numérica de P e K, ou nenhuma fórmula com o nutriente-âncora —,
        `indicada` é None e `motivo_sem_indicacao` diz por quê. Nunca levanta exceção por
        catálogo vazio: um laudo sem indicação de formulação continua completo.

    As doses saem em kg/ha SEM arredondamento. Arredondar aqui repetiria o defeito B-8 do
    CCAE, em que um valor arredondado cedo passou a decidir um corte; a apresentação
    arredonda para exibir, e a comparação entre fórmulas roda sobre o valor cheio.
    """
    bloco_formulas = (catalogo.get("formulas") or {}).get("itens") or []
    simples = {
        item["id"]: item
        for item in (catalogo.get("fertilizantes_simples") or {}).get("itens") or []
    }

    rec_p = _dose_numerica(adubacao.p2o5) or 0.0
    rec_k = _dose_numerica(adubacao.k2o) or 0.0
    rec_n = _dose_numerica(adubacao.n)

    def sem_indicacao(motivo: str) -> IndicacaoFormulacao:
        if trace is not None:
            trace.registrar(
                regra="R-FOR-01: escolha do adubo formulado",
                entradas={"p2o5": adubacao.p2o5, "k2o": adubacao.k2o, "n": adubacao.n,
                          "formulas_no_catalogo": len(bloco_formulas), "uso": uso},
                saida={"indicada": None, "motivo": motivo},
                fonte=(
                    "Método: Manual 2016, §8.3, p. 311. Catálogo: "
                    "dados/mercado/formulas_npk.json (dado de mercado, não do Manual)"
                ),
            )
        return IndicacaoFormulacao(
            indicada=None, ranking=[], motivo_sem_indicacao=motivo, criterio=CRITERIO
        )

    if not bloco_formulas:
        return sem_indicacao(
            "o catálogo de fórmulas está vazio — nenhuma fórmula foi cadastrada"
        )

    ancora, por_fallback = escolher_ancora(rec_p, rec_k, adubacao.classe_p, adubacao.classe_k)
    if ancora is None:
        return sem_indicacao(
            "a recomendação não traz dose numérica de P2O5 nem de K2O, e é por um desses "
            "dois que a dose de um adubo formulado se ancora"
        )

    candidatas = [f for f in bloco_formulas if uso in (f.get("uso") or [])]
    if not candidatas:
        return sem_indicacao(f"nenhuma fórmula do catálogo é indicada para {uso}")

    avaliadas = [
        opcao for opcao in (
            _avaliar(f, rec_n, rec_p, rec_k, ancora, por_fallback, simples)
            for f in candidatas
        ) if opcao is not None
    ]
    if not avaliadas:
        rotulo = "P2O5" if ancora == "p2o5" else "K2O"
        return sem_indicacao(
            f"nenhuma fórmula de {uso} no catálogo contém {rotulo}, que é o nutriente "
            f"mais deficiente nesta análise e por isso ancora a dose"
        )

    # Desempate pela menor dose: fórmula mais concentrada é menos frete, menos embalagem
    # e menos operação, como o Manual observa na p. 310. O id entra em último lugar só
    # para a ordem ser determinística quando duas fórmulas empatam em tudo — sem ele, a
    # saída dependeria da ordem do arquivo e o laudo deixaria de ser reprodutível.
    ranking = sorted(avaliadas, key=lambda o: (o.desvio_relativo, o.dose_kg_ha, o.id))
    indicada = ranking[0]

    if trace is not None:
        trace.registrar(
            regra="R-FOR-01: escolha do adubo formulado",
            entradas={
                "n_total": adubacao.n, "p2o5": rec_p, "k2o": rec_k,
                "classe_p": adubacao.classe_p, "classe_k": adubacao.classe_k,
                "ancora": ancora,
                "ancora_por_fallback": por_fallback,
                "formulas_avaliadas": len(avaliadas),
                "uso": uso,
            },
            saida={
                "indicada": indicada.id,
                "dose_kg_ha": indicada.dose_kg_ha,
                "desvio_relativo": indicada.desvio_relativo,
                "falta_p2o5": indicada.falta_p2o5,
                "falta_k2o": indicada.falta_k2o,
                "n_cobertura": indicada.n_cobertura,
            },
            fonte=(
                "Método: Manual 2016, §8.3, p. 311 (dose pelo nutriente mais deficiente); "
                "fertilizantes simples da Tab. 8.4, p. 304. Catálogo de fórmulas: "
                "dados/mercado/formulas_npk.json — dado de mercado, não é fonte do Manual"
            ),
        )

    return IndicacaoFormulacao(
        indicada=indicada, ranking=ranking, motivo_sem_indicacao=None, criterio=CRITERIO
    )


__all__ = ["CRITERIO", "ORDEM_CLASSES", "ErroFormulacao", "escolher_ancora", "indicar_formulacao"]
