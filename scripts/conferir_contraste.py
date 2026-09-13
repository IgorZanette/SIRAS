"""
Confere o contraste WCAG 2.2 dos pares texto/fundo das duas paletas do SIRAS.

O par. 2.3 do plano de front-end fixa o piso: 4,5:1 para texto normal e 3:1 para texto
grande e componentes. Este script mede, em vez de afirmar — e já apanhou o verde vivo
sendo usado como texto sobre claro, onde ele fica em 2,2:1.

A fórmula é a da própria recomendação: luminância relativa com a correção de gama por
canal, e razão (L_claro + 0,05) / (L_escuro + 0,05).

Uso:
    python scripts/conferir_contraste.py
"""

from __future__ import annotations

import sys
from typing import Dict, List, Tuple

# --- paleta ------------------------------------------------------------------
VERDES = {
    "--v-200": "#D9FBAE", "--v-300": "#B6F56A", "--v-400": "#8CE23F",
    "--v-500": "#6CC72A", "--v-600": "#4E9A2A", "--v-700": "#34701F",
    "--v-800": "#27561A",
}
#: Os sinais têm um valor por tema. Sobre preto eles precisam brilhar; sobre claro, os
#: mesmos valores ficam entre 1,4:1 e 2,6:1 e viram pastel. As variantes do modo claro
#: mantêm matiz e saturação e baixam só a luminosidade.
SINAIS_ESCURO = {
    "--sig-coral": "#FF6B4A", "--sig-laranja": "#FF9F3D",
    "--sig-ambar": "#FFC93D", "--sig-aqua": "#2BE0C8",
}
SINAIS_CLARO = {
    "--sig-coral": "#FF451C", "--sig-laranja": "#D96D00",
    "--sig-ambar": "#B28100", "--sig-aqua": "#179B8A",
}
ESCURO = {
    "fundo": "#0A0F0C", "painel": "#121B16", "campo": "#18231D",
    "texto": "#E9F0EB", "texto-2": "#A9BCB1", "texto-3": "#82998C",
}
CLARO = {
    "fundo": "#F6F8F5", "painel": "#FFFFFF", "campo": "#FFFFFF",
    "texto": "#0D1410", "texto-2": "#3B4A41", "texto-3": "#5C6F64",
}


def _luminancia(cor: str) -> float:
    cor = cor.lstrip("#")
    canais = [int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ajustados = [
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canais
    ]
    return 0.2126 * ajustados[0] + 0.7152 * ajustados[1] + 0.0722 * ajustados[2]


def contraste(frente: str, fundo: str) -> float:
    a, b = _luminancia(frente), _luminancia(fundo)
    claro, escuro = max(a, b), min(a, b)
    return (claro + 0.05) / (escuro + 0.05)


def _situacao(razao: float, grande: bool = False) -> str:
    piso = 3.0 if grande else 4.5
    return "ok " if razao >= piso else "FALHA"


def _tabela(titulo: str, pares: List[Tuple[str, str, str, bool]]) -> int:
    print(f"\n{titulo}")
    print(f"  {'par':46} {'razão':>7}  {'':5}")
    falhas = 0
    for nome, frente, fundo, grande in pares:
        razao = contraste(frente, fundo)
        situacao = _situacao(razao, grande)
        if situacao.strip() == "FALHA":
            falhas += 1
        print(f"  {nome:46} {razao:6.2f}:1  {situacao}")
    return falhas


def main() -> int:
    falhas = 0

    for tema, paleta in (("ESCURO", ESCURO), ("CLARO", CLARO)):
        pares: List[Tuple[str, str, str, bool]] = []
        for papel in ("texto", "texto-2", "texto-3"):
            for superficie in ("fundo", "painel"):
                pares.append((
                    f"{papel} sobre {superficie}", paleta[papel], paleta[superficie], False
                ))
        falhas += _tabela(f"Texto — tema {tema}", pares)

    for tema, paleta in (("ESCURO", ESCURO), ("CLARO", CLARO)):
        pares = [
            (f"{nome} como texto sobre {superficie}", valor, paleta[superficie], False)
            for nome, valor in VERDES.items()
            for superficie in ("fundo", "painel")
        ]
        falhas += _tabela(f"Verde como texto — tema {tema} (informativo)", pares)

    for tema, paleta, sinais in (
        ("ESCURO", ESCURO, SINAIS_ESCURO), ("CLARO", CLARO, SINAIS_CLARO)
    ):
        pares = [
            (f"{nome} sobre o fundo", valor, paleta["fundo"], True)
            for nome, valor in sinais.items()
        ]
        falhas += _tabela(f"Sinais como componente (piso 3:1) — tema {tema}", pares)

    pares = [
        (f"{nome} como componente sobre o fundo claro", valor, CLARO["fundo"], True)
        for nome, valor in VERDES.items()
    ]
    falhas += _tabela("Verde como componente (piso 3:1) — tema CLARO", pares)

    print(f"\n{falhas} par(es) abaixo do piso nesta varredura.")
    print("Verde e sinais como TEXTO sobre claro são informativos: o sistema os usa como")
    print("preenchimento e borda, e o rótulo textual vai sempre junto (WCAG 1.4.1).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
