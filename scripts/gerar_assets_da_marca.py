"""
Gera os arquivos de marca em tamanho de tela a partir dos originais.

Os originais têm entre 400 e 630 KB e até 2172 px de largura: servi-los reduzidos por CSS
custaria mais de 1,5 MB por carregamento e ainda renderizaria pior do que o arquivo
permite, porque o navegador reamostra a cada pintura.

Pillow é dependência DESTE script, não do sistema: o SIRAS continua rodando só com flask,
jsonschema e pytest (CLAUDE.md). Rode uma vez, versione a saída, e o script fica como
registro de como os arquivos de static/img/marca/ foram produzidos.

Uso:
    python scripts/gerar_assets_da_marca.py "C:/caminho/para/os/originais"
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

DESTINO = Path(__file__).resolve().parent.parent / "siras" / "web" / "static" / "img" / "marca"

#: (arquivo de origem, nome de saída, largura ou altura alvo, dimensão que manda, quadrar)
#:
#: `quadrar` recorta a moldura transparente e deixa o símbolo centrado num quadrado. É o
#: que um favicon exige: o original tem 1535x1024, e reduzir sem recortar produziria um
#: ícone achatado, com o desenho ocupando dois terços da área útil.
SAIDAS = (
    ("Logo completa.png", "siras-logo.png", 460, "largura", False),
    ("SIRAS Branco.png", "siras-texto.png", 420, "largura", False),
    ("Icone.png", "siras-icone.png", 256, "altura", True),
    ("Icone.png", "siras-icone-180.png", 180, "altura", True),
    ("Icone.png", "siras-icone-32.png", 32, "altura", True),
)


def _quadrar(imagem: Image.Image) -> Image.Image:
    """Recorta pelo conteúdo (bounding box do canal alfa) e centra num quadrado."""
    caixa = imagem.getchannel("A").getbbox()
    if caixa:
        imagem = imagem.crop(caixa)
    lado = max(imagem.size)
    quadrado = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    quadrado.paste(
        imagem, ((lado - imagem.width) // 2, (lado - imagem.height) // 2), imagem
    )
    return quadrado


def redimensionar(origem: Path, destino: Path, alvo: int, dimensao: str, quadrar: bool) -> None:
    with Image.open(origem) as arquivo:
        imagem = arquivo.convert("RGBA")
        if quadrar:
            imagem = _quadrar(imagem)
        largura, altura = imagem.size
        escala = alvo / (largura if dimensao == "largura" else altura)
        novo = (max(1, round(largura * escala)), max(1, round(altura * escala)))
        # LANCZOS: reamostragem de melhor qualidade do Pillow para reduzir imagem.
        reduzida = imagem.resize(novo, Image.LANCZOS)
        # optimize + compress_level 9: PNG sem perda, só melhor empacotado.
        reduzida.save(destino, "PNG", optimize=True, compress_level=9)
    print(f"  {destino.name:22} {novo[0]}x{novo[1]}  {destino.stat().st_size // 1024} KB")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    origem = Path(sys.argv[1])
    if not origem.is_dir():
        print(f"pasta não encontrada: {origem}")
        return 1

    DESTINO.mkdir(parents=True, exist_ok=True)
    print(f"gerando em {DESTINO}:")
    for arquivo, nome, alvo, dimensao, quadrar in SAIDAS:
        caminho = origem / arquivo
        if not caminho.is_file():
            print(f"  !! ausente: {arquivo}")
            continue
        redimensionar(caminho, DESTINO / nome, alvo, dimensao, quadrar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
