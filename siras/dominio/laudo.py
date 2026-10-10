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
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

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
class OpcaoAdubacao:
    """Uma forma de atender a recomendação, avaliada e custeada.

    Cobre os quatro tipos da ADR 0009: uma fórmula do catálogo, uma fórmula que o usuário
    informou, uma fórmula ideal calculada para esta recomendação, ou a mistura de
    fertilizantes simples. São todas comparáveis porque todas respondem à mesma pergunta
    — o que aplicar e quanto —, e por isso compartilham a estrutura.

    Quantidades em kg/ha e SEM arredondamento: quem arredonda é a apresentação, e a
    escolha entre opções roda sobre o valor cheio.
    """

    #: "catalogo" | "usuario" | "ideal" | "mistura_simples"
    tipo: str
    #: None na mistura de simples, que não tem fórmula
    formula_id: Optional[str]
    dose_kg_ha: float
    #: "p2o5" ou "k2o" — o ponto de quebra escolhido. None na mistura de simples
    ancora: Optional[str]
    #: kg/ha de n, p2o5 e k2o que a fórmula entrega
    fornecido: Dict[str, float] = field(default_factory=dict)
    #: kg/ha aplicados além do recomendado, por nutriente (nunca negativos)
    excesso: Dict[str, float] = field(default_factory=dict)
    #: kg/ha que a fórmula não cobriu, por nutriente (nunca negativos)
    falta: Dict[str, float] = field(default_factory=dict)
    complementos: Tuple[Complemento, ...] = ()
    #: valor da função de custo da ADR 0009. Menor é melhor
    custo: float = 0.0
    #: fórmula + complementos + ureia de cobertura. É o desempate de D9
    massa_total_kg_ha: float = 0.0
    #: garantias do rótulo, em % de massa. Vazio na mistura de simples
    teores: Dict[str, float] = field(default_factory=dict)
    #: de onde veio a entrada do catálogo. Vazio nos demais tipos
    fontes: List[str] = field(default_factory=list)
    #: quão forte é a prova de que a fórmula é vendida: forte, media, fraca ou nenhuma
    evidencia: str = ""
    #: ponto de quebra -> (dose, custo). É o que a trilha mostra para justificar a
    #: escolha: as duas doses possíveis e o que cada uma custaria.
    candidatos: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResultadoFormulacao:
    """Os três caminhos da ADR 0009, sempre os três.

    Nenhum deles é obrigatório existir: sem catálogo cadastrado, `catalogo` vem vazia e os
    outros dois seguem; sem dose numérica de P e K, os três vêm vazios e
    `motivo_sem_indicacao` diz por quê. Em nenhum caso isso é erro — o laudo segue
    completo.
    """

    #: caminho A: uma opção por alvo de concentração (ADR 0009, D10)
    ideais: List[OpcaoAdubacao] = field(default_factory=list)
    #: caminho B: as melhores do catálogo, já incluídas as que o usuário informou
    catalogo: List[OpcaoAdubacao] = field(default_factory=list)
    #: caminho C: ureia, superfosfato triplo e cloreto de potássio
    mistura: Optional[OpcaoAdubacao] = None
    #: avisos fixos do laudo (ADR 0009, D12)
    avisos: List[str] = field(default_factory=list)
    #: True quando o N de plantio não foi informado e a fórmula ideal saiu binária
    sem_n_de_plantio: bool = False
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
    #: como atender a recomendação com produto: fórmula ideal, melhores do catálogo e
    #: mistura de simples (ADR 0009). Nunca None — sem catálogo, os outros dois caminhos
    #: seguem, e o laudo continua completo.
    formulacao: Optional["ResultadoFormulacao"] = None


__all__ = [
    "Complemento",
    "Laudo",
    "OpcaoAdubacao",
    "ResultadoFormulacao",
    "RecomendacaoAdubacao",
    "RecomendacaoCalagem",
]
