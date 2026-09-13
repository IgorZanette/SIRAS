"""
Gera os arquivos de marca do SIRAS a partir do lockup oficial.

Entrada: o lockup horizontal em PNG com fundo transparente (ícone à esquerda, palavra
"SIRAS" à direita). Saída: as variantes que a interface usa, em static/img/marca/.

O que este script faz e por quê:

- RECORTA o ícone e a palavra separadamente, achando a lacuna entre os dois pela própria
  imagem. A interface usa os dois juntos na barra e o ícone sozinho no favicon e na tela
  de cálculo, e recortar na mão daria margens diferentes a cada exportação;
- QUADRA o ícone pelo conteúdo. O favicon precisa de proporção 1:1, e reduzir o recorte
  retangular produziria um ícone achatado;
- RECOLORE a palavra para o modo claro. O original é branco e some sobre fundo claro; a
  versão escura troca só os pixels brancos, preservando a folha verde do "A" e a
  suavização das bordas;
- REDUZ para tamanho de tela. O original tem 2172 px de largura, e servi-lo reduzido por
  CSS custaria isso a cada carregamento e ainda renderizaria pior, porque o navegador
  reamostra a cada pintura.

Pillow é dependência DESTE script, não do sistema: o SIRAS continua rodando só com
flask, jsonschema e pytest (CLAUDE.md). Rode uma vez, versione a saída, e o script fica
como registro de como os arquivos foram produzidos.

Uso:
    python scripts/gerar_assets_da_marca.py "C:/caminho/Unica.png"
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

DESTINO = Path(__file__).resolve().parent.parent / "siras" / "web" / "static" / "img" / "marca"

#: Cor do texto no modo claro. É o --n-100 do tema claro.
TINTA_CLARA = (13, 20, 16)

#: Largura da palavra "SIRAS" servida à barra.
#:
#: A barra a exibe com 22 px de altura (.logo__nome), e 300 px de largura dão 67 px —
#: três vezes a altura de exibição, o que cobre telas de densidade 2x e 3x com folga.
#: Não é número escolhido por gosto: o lockup novo é um desenho com gradiente e brilho,
#: e nele cada pixel a mais pesa. A 420 px a palavra sozinha custava 60 KB e estourava o
#: orçamento de marca da barra; a 300 px custa 34 KB e é indistinguível na tela.
LARGURA_DO_TEXTO = 300


def _colunas_com_conteudo(imagem: Image.Image) -> list:
    alfa = imagem.getchannel("A")
    largura, altura = imagem.size
    dados = alfa.load()
    return [
        x for x in range(largura)
        if any(dados[x, y] > 30 for y in range(0, altura, 2))
    ]


def _separar(imagem: Image.Image) -> Tuple[Image.Image, Image.Image]:
    """Divide o lockup na maior lacuna vertical entre o ícone e a palavra."""
    colunas = _colunas_com_conteudo(imagem)
    if not colunas:
        raise SystemExit("imagem sem conteúdo opaco")

    cheias = set(colunas)
    maior, inicio, atual = (0, 0), None, None
    for x in range(colunas[0], colunas[-1] + 1):
        if x not in cheias:
            inicio = x if inicio is None else inicio
            atual = x
        elif inicio is not None:
            if atual - inicio > maior[1] - maior[0]:
                maior = (inicio, atual)
            inicio = None
    if inicio is not None and atual - inicio > maior[1] - maior[0]:
        maior = (inicio, atual)

    corte = (maior[0] + maior[1]) // 2
    altura = imagem.size[1]
    icone = imagem.crop((0, 0, corte, altura))
    texto = imagem.crop((corte, 0, imagem.size[0], altura))
    return _aparar(icone), _aparar(texto)


#: Alfa a partir do qual um pixel conta como conteúdo. O lockup traz uma sombra difusa
#: em volta do ícone, e a caixa de alfa > 0 a inclui: o recorte saía com uma moldura
#: vazia enorme e o ícone encolhia dentro do quadrado do favicon.
_ALFA_DE_CONTEUDO = 60


def _aparar(imagem: Image.Image) -> Image.Image:
    mascara = imagem.getchannel("A").point(
        lambda valor: 255 if valor >= _ALFA_DE_CONTEUDO else 0
    )
    caixa = mascara.getbbox()
    return imagem.crop(caixa) if caixa else imagem


def _quadrar(imagem: Image.Image) -> Image.Image:
    lado = max(imagem.size)
    quadrado = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    quadrado.paste(imagem, ((lado - imagem.width) // 2, (lado - imagem.height) // 2), imagem)
    return quadrado


def _escurecer_texto(imagem: Image.Image) -> Image.Image:
    """Troca o branco por tinta escura e preserva o verde da folha.

    O teste é o próprio matiz: pixel cujo verde domina o vermelho e o azul é folha e
    fica; o resto é letra e escurece. A alfa não é tocada, então a suavização das bordas
    continua valendo e o texto não fica serrilhado.
    """
    convertida = imagem.copy()
    pixels = convertida.load()
    for y in range(convertida.height):
        for x in range(convertida.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            e_folha = g > r + 24 and g > b + 24
            if not e_folha:
                pixels[x, y] = (*TINTA_CLARA, a)
    return convertida


def _salvar(imagem: Image.Image, destino: Path, alvo: int, dimensao: str) -> None:
    largura, altura = imagem.size
    escala = alvo / (largura if dimensao == "largura" else altura)
    novo = (max(1, round(largura * escala)), max(1, round(altura * escala)))
    reduzida = imagem.resize(novo, Image.LANCZOS)
    reduzida.save(destino, "PNG", optimize=True, compress_level=9)
    print(f"  {destino.name:26} {novo[0]}x{novo[1]}  {destino.stat().st_size // 1024} KB")


def main(caminho: Optional[str] = None) -> int:
    if not caminho:
        print(__doc__)
        return 1

    origem = Path(caminho)
    if not origem.is_file():
        print(f"arquivo não encontrado: {origem}")
        return 1

    DESTINO.mkdir(parents=True, exist_ok=True)
    with Image.open(origem) as arquivo:
        lockup = _aparar(arquivo.convert("RGBA"))

    icone, texto = _separar(lockup)
    icone_quadrado = _quadrar(icone)
    texto_escuro = _escurecer_texto(texto)

    print(f"gerando em {DESTINO}:")
    _salvar(lockup, DESTINO / "siras-lockup.png", 640, "largura")
    _salvar(texto, DESTINO / "siras-texto.png", LARGURA_DO_TEXTO, "largura")
    _salvar(texto_escuro, DESTINO / "siras-texto-escuro.png", LARGURA_DO_TEXTO, "largura")
    for tamanho in (256, 180, 64, 32):
        _salvar(icone_quadrado, DESTINO / f"siras-icone-{tamanho}.png", tamanho, "altura")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
