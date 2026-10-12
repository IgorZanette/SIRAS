"""Gera os fundos de apoio da interface a partir das artes originais.

ENTRADA: `docs/fundos/`, as artes como o autor as entregou, 1672x941 px e PNG de 1,4 a
2,0 MB cada. São a FONTE, e por isso não ficam em `static/`, que é o que o navegador
baixa. São DUAS FAMÍLIAS, e a distinção importa:

- `op-1` a `op-5`: paisagens de lavoura ao amanhecer, escuras (luminância média ~43).
  Para o tema escuro, onde entram por `screen`, que só clareia.
- `claro-1` e `claro-2`: as mesmas colinas sob névoa de manhã, claras (luminância média
  ~226). Para o tema claro, nas calhas e na chamada final.
- `claro-vitrine`: a contraparte clara da `op-3`, e a única quadrada (1254x1254) —
  é a que fica atrás do monólito, numa caixa de proporção quase quadrada.

A segunda família chegou depois, e resolveu um problema que nenhuma dosagem resolvia:
sobre fundo quase branco, `screen` com arte escura move 0,3 de 255 — não faz nada — e
`multiply` dá uma sombra cinza, não uma paisagem. Arte clara sobre fundo claro aparece
por composição normal, sem truque de mesclagem. Uma arte certa vale mais que um filtro
bem ajustado.

SAÍDA: `siras/web/static/img/background/op-N.webp`, de 100 a 200 KB cada.

POR QUE CONVERTER, E NÃO SERVIR O PNG

As cinco artes entraram em `static/` no commit da identidade e estavam sendo servidas
inteiras: 8,5 MB de PNG para pintar uma textura a 10% de opacidade atrás de texto. O
PNG é formato sem perda — ele preserva com precisão um degradê de céu que, no uso
final, está encoberto por uma camada de 90% de fundo sólido. É pagar pelo que não se
vê, e numa tela de campo, por 4G, é o que o produtor espera carregando.

WebP com perda a 70 resolve: a mesma imagem sai com cerca de um décimo do tamanho, e a
diferença visível a 10% de opacidade é zero. A largura cai de 1672 para 1600 px, que é
o que uma faixa full-bleed usa num monitor comum.

TODAS SÃO GERADAS, e as que o CSS não cita são APAGADAS DE `static/` na revisão de
pré-congelamento. Não é contradição: gerar é barato e o script é o registro de como cada
arquivo servido foi produzido, mas um `static/` com arquivos que ninguém baixa é ruído
num repositório que vai ser congelado e lido por outras pessoas.

Para experimentar outra arte: rode o script, aponte o CSS para ela, e deixe em `static/`
só a que ficou.

Pillow é dependência DESTE script, não do sistema: o SIRAS continua rodando só com
flask, jsonschema e pytest (CLAUDE.md). Rode uma vez, versione a saída, e o script
fica como registro de como os arquivos servidos foram produzidos.

Uso:
    python scripts/gerar_fundos.py
"""

from __future__ import annotations

import pathlib
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - mensagem para quem roda sem o Pillow
    sys.exit("Este script precisa do Pillow: pip install Pillow")

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "docs" / "fundos"
DESTINO = RAIZ / "siras" / "web" / "static" / "img" / "background"

#: Largura MÁXIMA servida. A diferença para o original não aparece: a imagem é
#: `background-size: cover` atrás de conteúdo, nunca examinada de perto.
#:
#: É teto, e não alvo: `claro-vitrine` é quadrada e tem 1254 px, e ampliá-la para 1600
#: custaria bytes para inventar detalhe que a arte não tem.
LARGURA_MAXIMA = 1600

#: Qualidade do WebP. Em 70 o céu ainda degrada liso; abaixo disso aparece banding nas
#: faixas de névoa, que é justamente o que uma destas imagens tem de mais frágil.
QUALIDADE = 70


def gerar() -> int:
    if not ORIGEM.is_dir():
        sys.exit(f"Pasta das artes não encontrada: {ORIGEM}")

    DESTINO.mkdir(parents=True, exist_ok=True)
    artes = sorted(ORIGEM.glob("*.png"))
    if not artes:
        sys.exit(f"Nenhuma arte .png em {ORIGEM}")

    total_antes = total_depois = 0
    for arte in artes:
        with Image.open(arte) as img:
            img = img.convert("RGB")
            if img.width > LARGURA_MAXIMA:
                altura = round(img.height * LARGURA_MAXIMA / img.width)
                img = img.resize((LARGURA_MAXIMA, altura), Image.LANCZOS)
            saida = DESTINO / f"{arte.stem}.webp"
            img.save(saida, "WEBP", quality=QUALIDADE, method=6)

        antes, depois = arte.stat().st_size, saida.stat().st_size
        total_antes += antes
        total_depois += depois
        print(f"{arte.name:>10} -> {saida.name:<12} "
              f"{antes / 1024:7.0f} KB -> {depois / 1024:6.0f} KB "
              f"({depois / antes:.0%})")

    print(f"\n{len(artes)} fundos: {total_antes / 1024 / 1024:.1f} MB -> "
          f"{total_depois / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(gerar())
