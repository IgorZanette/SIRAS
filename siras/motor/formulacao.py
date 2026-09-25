"""
Indicação do adubo formulado que atende a recomendação.

O laudo diz quanto aplicar de N, P2O5 e K2O. Quem vai à revenda precisa da pergunta
seguinte respondida: *qual* adubo comprar e *quanto* dele. Este módulo faz essa ponte.

Fronteira de fonte — importa para a banca. Tudo o que entra aqui vindo do Manual são as
doses de nutriente já calculadas pelos módulos de adubação. O catálogo de formulações
(dados/mercado/formulacoes.json) **não é do Manual**: é dado de mercado, com fonte própria
por entrada. Este módulo não cria nenhum dos dois — só resolve a aritmética entre eles.

Critério de dose (decisão do autor, 13/09/2026, já em uso na calculadora de custo): a dose
da formulação é a MAIOR entre a quantidade que cobre o P2O5 e a que cobre o K2O. Assim
nenhum dos dois fica devendo, e o que sobra aparece declarado.

Critério de escolha (decisão do autor, 24/09/2026 — ADR 0007): entre as formulações que
atendem P e K, vence a de MENOR EXCESSO TOTAL de P2O5 + K2O entregue acima da
recomendação; empate se desfaz pela MENOR FALTA de N.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from siras.dominio.laudo import IndicacaoFormulacao, OpcaoFormulacao, RecomendacaoAdubacao
from siras.motor.trace import Trace

#: Texto do critério, exibido no laudo e registrado no Trace. Fica aqui, e não no
#: template, para que a regra e a sua descrição não possam divergir.
CRITERIO = (
    "dose pela maior quantidade entre a que cobre o P2O5 e a que cobre o K2O; "
    "escolha pelo menor excesso total de P2O5 + K2O, com desempate pela menor falta de N"
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


def _avaliar(
    formulacao: Dict[str, Any], rec_p: float, rec_k: float, rec_n: Optional[float]
) -> OpcaoFormulacao:
    """Dose, entrega, excesso e falta de uma formulação frente à recomendação."""
    teor_n = float(formulacao["n"])
    teor_p = float(formulacao["p2o5"])
    teor_k = float(formulacao["k2o"])

    # Quantidade de produto que cobre cada nutriente exigido. Nutriente com dose zero não
    # impõe quantidade nenhuma; nutriente exigido de uma formulação que não o contém é o
    # que torna a formulação incapaz de atender.
    faltantes: List[str] = []
    candidatas: List[float] = []
    for rotulo, exigido, teor in (("P2O5", rec_p, teor_p), ("K2O", rec_k, teor_k)):
        if exigido <= 0:
            continue
        if teor <= 0:
            faltantes.append(rotulo)
            continue
        candidatas.append(exigido * 100.0 / teor)

    if faltantes:
        return OpcaoFormulacao(
            id=formulacao["id"],
            rotulo=formulacao["rotulo"],
            n=teor_n, p2o5=teor_p, k2o=teor_k,
            dose_kg_ha=None,
            entrega_n=None, entrega_p2o5=None, entrega_k2o=None,
            excesso_p2o5=None, excesso_k2o=None, falta_n=None, excesso_n=None,
            atende=False,
            motivo_nao_atende=(
                f"não contém {' nem '.join(faltantes)}, que a recomendação exige"
            ),
            fonte=formulacao["_fonte"],
        )

    dose = max(candidatas)
    entrega_n = dose * teor_n / 100.0
    entrega_p = dose * teor_p / 100.0
    entrega_k = dose * teor_k / 100.0

    return OpcaoFormulacao(
        id=formulacao["id"],
        rotulo=formulacao["rotulo"],
        n=teor_n, p2o5=teor_p, k2o=teor_k,
        dose_kg_ha=dose,
        entrega_n=entrega_n, entrega_p2o5=entrega_p, entrega_k2o=entrega_k,
        # Nunca negativos: a dose é a maior das duas coberturas, então cada nutriente é
        # entregue na medida ou acima dela.
        excesso_p2o5=max(0.0, entrega_p - rec_p),
        excesso_k2o=max(0.0, entrega_k - rec_k),
        # N fica fora do critério de dose de propósito: é o nutriente que se completa com
        # fonte à parte. Falta e excesso ficam declarados, e o excesso não é indiferente —
        # N a mais tem custo e efeito agronômico próprios.
        falta_n=None if rec_n is None else max(0.0, rec_n - entrega_n),
        excesso_n=None if rec_n is None else max(0.0, entrega_n - rec_n),
        atende=True,
        motivo_nao_atende=None,
        fonte=formulacao["_fonte"],
    )


def _chave_de_ordem(opcao: OpcaoFormulacao):
    """Menor excesso de P2O5 + K2O; desempate pela menor falta de N; depois pelo rótulo.

    O rótulo entra como último critério só para tornar a ordem determinística quando duas
    formulações empatam em tudo — sem ele, a saída dependeria da ordem do arquivo, e o
    laudo deixaria de ser reprodutível.
    """
    excesso = (opcao.excesso_p2o5 or 0.0) + (opcao.excesso_k2o or 0.0)
    falta_n = opcao.falta_n if opcao.falta_n is not None else 0.0
    return (excesso, falta_n, opcao.rotulo)


def indicar_formulacao(
    adubacao: RecomendacaoAdubacao,
    catalogo: Dict[str, Any],
    trace: Optional[Trace] = None,
) -> IndicacaoFormulacao:
    """Escolhe a formulação NPK que melhor atende a recomendação de adubação.

    Args:
        adubacao: a recomendação já emitida, com as doses de N, P2O5 e K2O em kg/ha
        catalogo: conteúdo de dados/mercado/formulacoes.json
        trace: opcional; recebe o passo R-FOR-01 quando informado

    Returns:
        IndicacaoFormulacao. Quando não há o que indicar — catálogo vazio, nenhuma dose
        numérica de P ou K, ou nenhuma formulação capaz de atender —, `indicada` é None e
        `motivo_sem_indicacao` diz por quê. Nunca levanta exceção por catálogo vazio: um
        laudo sem indicação de formulação continua sendo um laudo completo.

    As doses saem em kg/ha SEM arredondamento. Arredondar aqui repetiria o defeito B-8 do
    CCAE, em que um valor arredondado cedo passou a decidir um corte; a apresentação
    arredonda para exibir, e a comparação entre formulações roda sobre o valor cheio.
    """
    formulacoes: Sequence[Dict[str, Any]] = catalogo.get("formulacoes") or []

    rec_p = _dose_numerica(adubacao.p2o5) or 0.0
    rec_k = _dose_numerica(adubacao.k2o) or 0.0
    rec_n = _dose_numerica(adubacao.n)

    def sem_indicacao(motivo: str) -> IndicacaoFormulacao:
        if trace is not None:
            trace.registrar(
                regra="R-FOR-01: indicação de adubo formulado",
                entradas={"p2o5": adubacao.p2o5, "k2o": adubacao.k2o, "n": adubacao.n,
                          "formulacoes_no_catalogo": len(formulacoes)},
                saida={"indicada": None, "motivo": motivo},
                fonte="dados/mercado/formulacoes.json (catálogo de mercado, não do Manual)",
            )
        return IndicacaoFormulacao(
            indicada=None, ranking=[], motivo_sem_indicacao=motivo, criterio=CRITERIO
        )

    if not formulacoes:
        return sem_indicacao(
            "o catálogo de formulações está vazio — nenhuma formulação foi cadastrada"
        )
    if rec_p <= 0 and rec_k <= 0:
        return sem_indicacao(
            "a recomendação não traz dose numérica de P2O5 nem de K2O, e é por esses dois "
            "que a dose de um adubo formulado se dimensiona"
        )

    avaliadas = [_avaliar(f, rec_p, rec_k, rec_n) for f in formulacoes]
    atendem = sorted((o for o in avaliadas if o.atende), key=_chave_de_ordem)

    if not atendem:
        return sem_indicacao(
            "nenhuma formulação do catálogo contém os nutrientes que esta recomendação exige"
        )

    # As que não atendem seguem no ranking, ao final e com o motivo declarado: saber que
    # uma formulação disponível NÃO serve, e por quê, é informação para quem compra.
    ranking = atendem + [o for o in avaliadas if not o.atende]
    indicada = atendem[0]

    if trace is not None:
        trace.registrar(
            regra="R-FOR-01: indicação de adubo formulado",
            entradas={
                "p2o5": rec_p, "k2o": rec_k, "n": adubacao.n,
                "formulacoes_avaliadas": len(avaliadas),
                "criterio": CRITERIO,
            },
            saida={
                "indicada": indicada.rotulo,
                "dose_kg_ha": indicada.dose_kg_ha,
                "excesso_p2o5": indicada.excesso_p2o5,
                "excesso_k2o": indicada.excesso_k2o,
                "falta_n": indicada.falta_n,
            },
            fonte=(
                f"{indicada.fonte} — catálogo de mercado (dados/mercado/formulacoes.json), "
                f"não é fonte do Manual"
            ),
        )

    return IndicacaoFormulacao(
        indicada=indicada, ranking=ranking, motivo_sem_indicacao=None, criterio=CRITERIO
    )


__all__ = ["CRITERIO", "ErroFormulacao", "indicar_formulacao"]
