"""Gera os fundos de apoio da interface a partir das artes originais.

ENTRADA: `docs/fundos/`, as cinco artes como o autor as entregou — paisagens de
lavoura ao amanhecer, 1672x941 px, PNG de 1,7 a 2,0 MB cada. São a FONTE, e por isso
não ficam em `static/`, que é o que o navegador baixa.

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

AS CINCO SÃO GERADAS, mesmo com duas em uso hoje. Elas são opções do autor: trocar o
fundo da hero é mudar `op-3` para `op-1` numa linha de CSS, e isso só é verdade se as
cinco estiverem lá. A 130 KB cada, as três de reserva custam menos que o PNG de uma.

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

#: Largura servida. O original tem 1672 px e a diferença não aparece: a imagem é
#: `background-size: cover` atrás de conteúdo, nunca examinada de perto.
LARGURA = 1600

#: Qualidade do WebP. Em 70 o céu ainda degrada liso; abaixo disso aparece banding nas
#: faixas de névoa, que é justamente o que uma destas imagens tem de mais frágil.
QUALIDADE = 70


def gerar() -> int:
    if not ORIGEM.is_dir():
        sys.exit(f"Pasta das artes não encontrada: {ORIGEM}")

    DESTINO.mkdir(parents=True, exist_ok=True)
    artes = sorted(ORIGEM.glob("op-*.png"))
    if not artes:
        sys.exit(f"Nenhuma arte op-*.png em {ORIGEM}")

    total_antes = total_depois = 0
    for arte in artes:
        with Image.open(arte) as img:
            img = img.convert("RGB")
            altura = round(img.height * LARGURA / img.width)
            img = img.resize((LARGURA, altura), Image.LANCZOS)
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
