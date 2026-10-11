"""
Gera os arquivos de marca do SIRAS a partir das artes originais.

ENTRADA: `docs/marca/`, a pasta das artes como o autor as exportou — horizontal e
vertical, com e sem o descritivo, em versão de letras claras e de letras escuras, mais
o ícone quadrado. São arquivos de 0,5 a 1,5 MB cada: eles são a FONTE, e não ficam em
`static/`, que é o que o navegador baixa.

SAÍDA: `siras/web/static/img/marca/`, só o que a interface serve, reduzido para
tamanho de tela.

O QUE ESTE SCRIPT FAZ, E POR QUÊ

- SEPARA o ícone da palavra no lockup horizontal, achando a lacuna entre os dois pela
  própria imagem. A barra usa os dois juntos, mas como duas imagens: assim a palavra
  troca de cor com o tema e o ícone, que é o mesmo nos dois, é baixado uma vez só.
  Recortar à mão daria margens diferentes a cada exportação da arte.
- NÃO RECOLORE nada. A versão anterior deste script tingia os pixels brancos para
  produzir a palavra escura, porque só havia a arte clara. A identidade de 11/10/2026
  traz as duas versões desenhadas, e uma arte autoral é melhor que um tingimento
  automático — sobretudo num logotipo com gradiente.
- REDUZ para tamanho de tela. O horizontal original tem 2172 px de largura; servi-lo
  reduzido por CSS custaria o arquivo inteiro a cada carregamento e renderizaria pior,
  porque o navegador reamostra a cada pintura.

Pillow é dependência DESTE script, não do sistema: o SIRAS continua rodando só com
flask, jsonschema e pytest (CLAUDE.md). Rode uma vez, versione a saída, e o script
fica como registro de como os arquivos servidos foram produzidos.

Uso:
    python scripts/gerar_assets_da_marca.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "docs" / "marca"
DESTINO = RAIZ / "siras" / "web" / "static" / "img" / "marca"

#: As artes originais, pelo nome com que o autor as exportou.
ARTE_ICONE = "Icon e favicon.png"
ARTE_HORIZONTAL_CLARA = "Logo Horizontal minimalista.png"
ARTE_HORIZONTAL_ESCURA = "Logo Horizontal escura minimalista.png"
ARTE_HORIZONTAL_DESCRITIVO = "Logo Horizontal.png"
ARTE_VERTICAL_CLARA = "Logo Vertical minimalista.png"

#: Largura da palavra "SIRAS" servida à barra.
#:
#: A barra a exibe com 22 px de altura (.logo__nome). 300 px de largura dão cerca de
#: 67 px de altura — três vezes a de exibição, o que cobre telas de densidade 2x e 3x
#: com folga e ainda cabe no orçamento de peso que o teste da barra impõe.
LARGURA_DA_PALAVRA = 300

#: Tamanhos de ícone que o HTML declara: favicon em dois tamanhos e o da tela inicial
#: de iOS. O navegador escolhe o mais próximo do que precisa, em vez de reamostrar o
#: maior a cada pintura.
TAMANHOS_DE_ICONE = (32, 64, 180, 256)

#: Alfa a partir do qual um pixel conta como conteúdo. As artes trazem sombra difusa
#: em volta do desenho; aparar pelo alfa > 0 incluiria essa sombra e deixaria margem
#: inútil em volta de tudo.
LIMIAR_DE_CONTEUDO = 26


def _colunas_com_conteudo(imagem: Image.Image) -> list:
    """Quais colunas de pixels têm algo além de transparência."""
    alfa = imagem.getchannel("A")
    largura, altura = imagem.size
    dados = alfa.load()
    return [
        x for x in range(largura)
        if any(dados[x, y] > LIMIAR_DE_CONTEUDO for y in range(0, altura, 3))
    ]


def _aparar(imagem: Image.Image) -> Image.Image:
    """Corta a moldura transparente, pelo limiar de conteúdo."""
    alfa = imagem.getchannel("A")
    mascara = alfa.point(lambda v: 255 if v > LIMIAR_DE_CONTEUDO else 0)
    caixa = mascara.getbbox()
    return imagem.crop(caixa) if caixa else imagem


def _separar(lockup: Image.Image) -> Tuple[Image.Image, Image.Image]:
    """Divide o lockup horizontal na maior lacuna vertical entre ícone e palavra."""
    colunas = _colunas_com_conteudo(lockup)
    if not colunas:
        raise SystemExit("a arte está vazia: confira o arquivo de origem")

    maior, corte = 0, None
    for anterior, seguinte in zip(colunas, colunas[1:]):
        if seguinte - anterior > maior:
            maior, corte = seguinte - anterior, (anterior + seguinte) // 2
    if corte is None or maior < 20:
        raise SystemExit(
            "não achei a lacuna entre o ícone e a palavra. Se a arte mudou de "
            "composição, ajuste a separação em vez de recortar à mão."
        )

    altura = lockup.size[1]
    return _aparar(lockup.crop((0, 0, corte, altura))), _aparar(
        lockup.crop((corte, 0, lockup.size[0], altura))
    )


def _quadrar(imagem: Image.Image) -> Image.Image:
    """Centra o conteúdo numa tela quadrada. O favicon precisa de 1:1, e reduzir um
    recorte retangular produziria um ícone achatado."""
    lado = max(imagem.size)
    tela = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    tela.paste(imagem, ((lado - imagem.size[0]) // 2, (lado - imagem.size[1]) // 2))
    return tela


def _salvar(imagem: Image.Image, destino: Path, alvo: int, dimensao: str) -> None:
    largura, altura = imagem.size
    escala = alvo / (largura if dimensao == "largura" else altura)
    novo = (max(1, round(largura * escala)), max(1, round(altura * escala)))
    reduzida = imagem.resize(novo, Image.LANCZOS)
    destino.parent.mkdir(parents=True, exist_ok=True)
    reduzida.save(destino, "PNG", optimize=True)
    print(f"  {destino.name:34} {novo[0]:4}x{novo[1]:<4} "
          f"{destino.stat().st_size // 1024:4} KiB")


def _abrir(nome: str) -> Image.Image:
    caminho = ORIGEM / nome
    if not caminho.is_file():
        raise SystemExit(
            f"não achei '{nome}' em {ORIGEM}.\n"
            f"As artes originais moram em docs/marca/; static/ recebe só o que este "
            f"script gera."
        )
    return _aparar(Image.open(caminho).convert("RGBA"))


def main() -> int:
    print(f"origem:  {ORIGEM}")
    print(f"destino: {DESTINO}\n")

    # --- ícone, em quatro tamanhos ---
    icone = _quadrar(_abrir(ARTE_ICONE))
    for lado in TAMANHOS_DE_ICONE:
        _salvar(icone, DESTINO / f"siras-icone-{lado}.png", lado, "largura")

    # --- a palavra, nas duas versões que o tema alterna ---
    _, palavra_clara = _separar(_abrir(ARTE_HORIZONTAL_CLARA))
    _salvar(palavra_clara, DESTINO / "siras-texto.png", LARGURA_DA_PALAVRA, "largura")

    _, palavra_escura = _separar(_abrir(ARTE_HORIZONTAL_ESCURA))
    _salvar(palavra_escura, DESTINO / "siras-texto-escuro.png",
            LARGURA_DA_PALAVRA, "largura")

    # --- lockups inteiros, para onde a marca aparece grande ---
    _salvar(_abrir(ARTE_HORIZONTAL_DESCRITIVO),
            DESTINO / "siras-lockup.png", 640, "largura")
    _salvar(_abrir(ARTE_VERTICAL_CLARA),
            DESTINO / "siras-vertical.png", 360, "altura")

    print("\nPronto. Versione a saída; as artes originais ficam em docs/marca/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
