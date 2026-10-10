"""Estrutura do laudo: a saída única de gerar_laudo().

Objeto de dados puro, sem regra agronômica. Existe para que a camada web, os testes e
os scripts de validação leiam a mesma coisa, em vez de cada um recompor o resultado a
partir das chamadas soltas de calagem, adubação e aptidão.

Nota de camada: o campo de aptidão guarda um ResultadoAptidao, definido em
siras/motor/aptidao.py. A anotação é importada só sob TYPE_CHECKING de propósito — em
tempo de execução siras/dominio/ não importa siras/motor/, senão a dependência entre as
duas camadas se inverteria (hoje é o motor que importa o domínio) e `import
siras.dominio.laudo` arrastaria o motor inteiro junto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from siras.dominio.analise import AnaliseSolo, Contexto

if TYPE_CHECKING:  # pragma: no cover - só para verificação de tipos
    from siras.motor.aptidao import ResultadoAptidao
    from siras.motor.trace import Trace


@dataclass(frozen=True)
class RecomendacaoCalagem:
    """Necessidade de calcário e o critério de grupo que a produziu."""

    #: t/ha do corretivo real, já convertido pelo PRNT do Contexto
    nc_t_ha: float
    #: preenchido quando nc_t_ha é 0,0: por que a calagem não foi disparada
    motivo: Optional[str]
    #: id do critério em dados/comum/criterios_calagem.json (Tab. 5.3 a 5.7)
    criterio_id: str
    #: o registro inteiro do critério aplicado, como está transcrito na base. O laudo
    #: precisa dele para dizer em que camada amostrar, como aplicar, qual o pH alvo e
    #: quais notas do Manual valem — tudo transcrito, nada redigido pela interface.
    criterio: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecomendacaoAdubacao:
    """Doses de N, P2O5 e K2O (kg/ha) e as classes de teor que as determinaram.

    n/p2o5/k2o são normalmente float. Quando o Manual publica um teto em vez de um valor
    ("<= manutenção", classe Muito alto em 2º cultivo), a dose vem no formato do ADR 0004
    (`{"valor": X, "qualificador": "ate"}`) — daí a anotação Any. Achatar isso para um
    número implicaria uma precisão que o Manual não dá.
    """

    n: Any
    p2o5: Any
    k2o: Any
    classe_p: Optional[str] = None
    classe_k: Optional[str] = None
    #: faixa de MO usada na dose de N (None quando a cultura não recebe N)
    faixa_mo: Optional[str] = None
    #: preenchido quando a cultura não recebe N (leguminosas, fixação biológica)
    motivo_n: Optional[str] = None
    #: as faixas de/até que classificaram P e K nesta análise — vêm da mesma chamada que
    #: produziu classe_p/classe_k. É o que permite à régua dizer quão perto da borda da
    #: classe o teor está, sem reclassificar nada na camada de apresentação.
    faixas_p: List[Dict[str, Any]] = field(default_factory=list)
    faixas_k: List[Dict[str, Any]] = field(default_factory=list)
    #: Orientações práticas que o Manual publica junto da dose: parcelamento de N, P e K,
    #: observações e restrições da cultura. São transcrição, e são o que o técnico procura
    #: depois de saber quanto aplicar — a pergunta seguinte a "quanto" é sempre "como".
    orientacoes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Complemento:
    """Fertilizante simples que cobre o que a fórmula não entregou.

    `momento` é "cobertura" só para o N que sobra do total recomendado; os complementos
    de P e K vão junto da fórmula, no plantio.
    """

    produto: str
    dose_kg_ha: float
    nutriente: str
    momento: str = "plantio"


@dataclass(frozen=True)
class OpcaoFormulacao:
    """Uma formulação NPK do catálogo, avaliada contra a recomendação desta análise.

    Quantidades em kg/ha e SEM arredondamento — quem arredonda é a apresentação.

    A dose é ancorada no nutriente mais deficiente no solo (Manual, §8.3, p. 311), que
    por isso é atendido exatamente. O outro falta ou sobra, e as duas coisas ficam
    declaradas: falta exige uma operação a mais, sobra é adubo pago e não aproveitado.
    """

    id: str
    #: garantias do rótulo, em % de massa
    n: float
    p2o5: float
    k2o: float
    dose_kg_ha: float
    #: kg/ha de cada nutriente que esta dose entrega
    entrega_n: float
    entrega_p2o5: float
    entrega_k2o: float
    #: kg/ha que ainda faltam depois da fórmula (nunca negativos)
    falta_p2o5: float
    falta_k2o: float
    #: kg/ha aplicados além do recomendado (nunca negativos)
    excesso_p2o5: float
    excesso_k2o: float
    excesso_n: float
    #: N do total recomendado que a fórmula não entregou, e vai para cobertura
    n_cobertura: float
    #: métrica de ordenação: (faltas + excessos) / (P2O5 + K2O recomendados). Menor é melhor
    desvio_relativo: float
    #: 'p2o5' ou 'k2o' — o nutriente que definiu a dose
    ancora: str
    #: True quando a âncora foi escolhida pela maior dose por falta de classe de teor
    ancora_por_fallback: bool = False
    complementos: List[Complemento] = field(default_factory=list)
    #: de onde veio a entrada do catálogo. Dado de mercado, não do Manual.
    fontes: List[str] = field(default_factory=list)
    origem: str = ""


@dataclass(frozen=True)
class IndicacaoFormulacao:
    """Qual adubo formulado comprar, e as alternativas em ordem.

    `indicada` é None quando não há o que indicar — catálogo vazio, recomendação sem dose
    numérica de P e K, ou nenhuma formulação capaz de atender. Isso não é erro: o laudo
    segue completo sem a indicação, e `motivo_sem_indicacao` diz o que faltou.
    """

    indicada: Optional[OpcaoFormulacao]
    #: todas as avaliadas, em ordem de preferência
    ranking: List[OpcaoFormulacao] = field(default_factory=list)
    motivo_sem_indicacao: Optional[str] = None
    criterio: str = ""


@dataclass(frozen=True)
class Laudo:
    """Saída única do motor para uma análise, uma cultura e um contexto.

    Os dois cenários de aptidão vêm sempre juntos, não por escolha de apresentação: o
    CCAE §7 define que a diferença entre ATUAL e POTENCIAL é o que quantifica o ganho
    atribuível à recomendação que o próprio SIRAS acabou de emitir. Emitir só um dos dois
    perderia justamente a integração entre os módulos.
    """

    cultura_id: str
    grupo: str
    analise: AnaliseSolo
    contexto: Contexto
    calagem: RecomendacaoCalagem
    adubacao: RecomendacaoAdubacao
    aptidao_atual: "ResultadoAptidao"
    aptidao_potencial: "ResultadoAptidao"
    #: trilha de inferência completa — é o que alimenta a seção "De onde vem cada número"
    trace: "Trace" = field(repr=False)
    #: adubo formulado que atende a recomendação. None quando o catálogo de mercado está
    #: vazio — o laudo continua completo, só sem a ponte para o que se compra na revenda.
    formulacao: Optional[IndicacaoFormulacao] = None


__all__ = [
    "Complemento",
    "IndicacaoFormulacao",
    "Laudo",
    "OpcaoFormulacao",
    "RecomendacaoAdubacao",
    "RecomendacaoCalagem",
]
