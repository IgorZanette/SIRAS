from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class PassoInferencia:
    """Representa uma etapa de inferência com sua regra e a evidência documental."""

    regra: str
    entradas: Dict[str, Any]
    saida: Dict[str, Any]
    fonte: str


class Trace:
    """Acumula os passos do raciocínio do motor de inferência.

    O método registrar() adiciona um passo ao histórico e retorna a saída,
    permitindo uso em linha dentro do motor sem quebrar o fluxo de cálculo.
    """

    def __init__(self) -> None:
        self.passos: List[PassoInferencia] = []

    def registrar(
        self,
        regra: str,
        entradas: Dict[str, Any],
        saida: Dict[str, Any],
        fonte: str,
    ) -> Dict[str, Any]:
        passo = PassoInferencia(
            regra=regra,
            entradas=dict(entradas),
            saida=dict(saida),
            fonte=fonte,
        )
        self.passos.append(passo)
        return passo.saida

    def limpar(self) -> None:
        self.passos.clear()

    def __len__(self) -> int:
        return len(self.passos)

    def __iter__(self):
        return iter(self.passos)

    def __bool__(self) -> bool:
        return bool(self.passos)


__all__ = ["PassoInferencia", "Trace"]
