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
from typing import TYPE_CHECKING, Any, Optional

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


__all__ = ["Laudo", "RecomendacaoAdubacao", "RecomendacaoCalagem"]
