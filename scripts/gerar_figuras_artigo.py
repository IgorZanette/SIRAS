"""
Gera as figuras do artigo final, em PNG, para docs/artigo_final/fig/.

REGRA QUE VALE PARA TODAS: nenhuma figura com número inventado. As que mostram
resultado leem o valor do próprio sistema, no momento da geração — a tabela de
concordância sai de siras/validacao/concordancia.py, o exemplo da formulação sai de
siras/motor/formulacao.py. Se o dado mudar, a figura muda junto. Figura cujo dado ainda
não existe NÃO é gerada: o script avisa e segue, e o \\pendente{} correspondente continua
visível no texto.

As figuras são pensadas para IMPRESSÃO EM PRETO E BRANCO, que é como a maior parte das
cópias de um TCC circula: nada depende de cor para ser lido. A cor existe como reforço,
nunca como o único portador de significado.

Uso:
    python scripts/gerar_figuras_artigo.py
    python scripts/gerar_figuras_artigo.py --figura f7
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

SAIDA = Path(__file__).parent.parent / "docs" / "artigo_final" / "fig"

#: Largura útil de uma página do template, em polegadas. A classe é A4 com margens de
#: 3 cm à esquerda e 2 cm à direita, o que deixa 16 cm de texto.
LARGURA = 6.3
DPI = 200

#: Paleta. Cinzas fazem o trabalho; o verde é reforço, e some sem prejuízo numa laser
#: monocromática. Os dois tons de preenchimento foram escolhidos com diferença de
#: luminosidade suficiente para se distinguirem em escala de cinza.
TINTA = "#1A1A1A"
CINZA = "#6E6E6E"
CLARO = "#E8E8E8"
MEDIO = "#B8B8B8"
VERDE = "#4E9A2A"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": TINTA,
    "axes.labelcolor": TINTA,
    "text.color": TINTA,
    "xtick.color": TINTA,
    "ytick.color": TINTA,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


# --- utilitários de layout -----------------------------------------------------------
#
# A primeira versão destas figuras posicionava tudo por coordenadas escolhidas no olho, e
# o resultado foi texto sobre texto em três das quatro. O que segue é o conserto: uma
# grade com margem declarada, posições calculadas, e nenhuma prosa dentro do PNG — a
# explicação vai na legenda do LaTeX, que é onde o leitor a procura.

#: Margem interna de toda figura, em fração da área. Nada é desenhado fora dela.
MARGEM = 0.03


def _gravar(fig, nome: str) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA / f"{nome}.png"
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"  gravada: {caminho.relative_to(Path(__file__).parent.parent)}")


def _tela(largura_pol, altura_pol):
    """Eixo em coordenadas 0-1, com a margem já reservada."""
    fig, ax = plt.subplots(figsize=(largura_pol, altura_pol))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _linhas_em_faixas(fracoes, topo=1.0, base=0.0, respiro=0.035):
    """Divide a altura disponível em faixas proporcionais, com respiro entre elas.

    Devolve uma lista de (y_base, altura). É o que substitui as coordenadas digitadas:
    acrescentar uma faixa reacomoda todas as outras sozinho.
    """
    total = sum(fracoes)
    vaos = respiro * (len(fracoes) - 1)
    util = (topo - base) - vaos
    faixas, y = [], topo
    for fracao in fracoes:
        altura = util * fracao / total
        y -= altura
        faixas.append((y, altura))
        y -= respiro
    return faixas


def _caixa(ax, x, y, largura, altura, *, fundo="white", borda=TINTA, traco="-",
           espessura=1.1):
    ax.add_patch(FancyBboxPatch(
        (x, y), largura, altura, boxstyle="round,pad=0.008,rounding_size=0.015",
        facecolor=fundo, edgecolor=borda, linewidth=espessura, linestyle=traco,
        zorder=2,
    ))


def _titulo_e_apoio(ax, x, y, altura, titulo, apoio=None, *, tamanho=9.2):
    """Título em negrito e, abaixo, a linha de apoio em cinza. Centrados na faixa."""
    if apoio:
        ax.text(x, y + altura * 0.62, titulo, fontsize=tamanho, fontweight="bold",
                va="center", zorder=3)
        ax.text(x, y + altura * 0.28, apoio, fontsize=tamanho - 1.4, color=CINZA,
                va="center", zorder=3, linespacing=1.3)
    else:
        ax.text(x, y + altura / 2, titulo, fontsize=tamanho, fontweight="bold",
                va="center", zorder=3)


def _seta(ax, inicio, fim, *, estilo="-|>", cor=TINTA, traco="-"):
    ax.add_patch(FancyArrowPatch(
        inicio, fim, arrowstyle=estilo, mutation_scale=10,
        color=cor, linewidth=1.0, linestyle=traco, shrinkA=0, shrinkB=0, zorder=4,
    ))


# --- F1: arquitetura em camadas ------------------------------------------------------

def f1_arquitetura() -> None:
    """Camadas e a fronteira do Flask. A explicação vai na legenda, não na figura."""
    fig, ax = _tela(LARGURA, 3.2)

    camadas = [
        ("siras/web/", "rotas, formulário e templates", CLARO),
        ("siras/relatorio/", "laudo para a tela e para o papel", CLARO),
        ("siras/motor/", "as regras SE-ENTÃO dos quatro módulos", "white"),
        ("siras/conhecimento/", "carregamento e validação da base", "white"),
        ("siras/dominio/", "entidades: análise, contexto, laudo", "white"),
    ]
    coluna_x, coluna_largura = MARGEM, 0.58
    faixas = _linhas_em_faixas([1] * 5, topo=1 - MARGEM, base=MARGEM, respiro=0.045)

    for (y, altura), (nome, apoio, fundo) in zip(faixas, camadas):
        _caixa(ax, coluna_x, y, coluna_largura, altura, fundo=fundo)
        _titulo_e_apoio(ax, coluna_x + 0.025, y, altura, nome, apoio)

    # A seta que cruza a fronteira sai do centro para que a linha tracejada passe
    # limpa por ela; as demais ficam centradas.
    for i, ((y, _altura), _) in enumerate(zip(faixas[:-1], camadas[:-1])):
        x = coluna_x + coluna_largura * (0.25 if i == 1 else 0.5)
        _seta(ax, (x, y), (x, y - 0.045))

    # A fronteira: entre relatorio (índice 1) e motor (índice 2).
    corte = (faixas[1][0] + faixas[2][0] + faixas[2][1]) / 2
    ax.plot([MARGEM - 0.015, coluna_x + coluna_largura + 0.015], [corte, corte],
            color=VERDE, linewidth=1.8, linestyle=(0, (6, 3)), zorder=5)
    ax.text(coluna_x + coluna_largura + 0.03, corte,
            "acima, depende de Flask\nabaixo, Python puro",
            fontsize=8.2, va="center", linespacing=1.45, zorder=3)

    # A base de conhecimento, à direita, alinhada às duas camadas que a consomem.
    base_y = faixas[4][0]
    base_altura = faixas[3][0] + faixas[3][1] - base_y
    dados_x = coluna_x + coluna_largura + 0.045
    _caixa(ax, dados_x, base_y, 1 - MARGEM - dados_x, base_altura, traco=(0, (4, 2)))
    ax.text(dados_x + 0.02, base_y + base_altura * 0.78, "dados/",
            fontsize=9, fontweight="bold", va="center", zorder=3)
    for i, linha in enumerate(("comum/ — Manual", "culturas/ — Manual",
                               "mercado/ — não é Manual")):
        ax.text(dados_x + 0.02, base_y + base_altura * (0.52 - i * 0.2), linha,
                fontsize=7.8, color=CINZA, va="center", zorder=3)
    _seta(ax, (dados_x, base_y + base_altura * 0.78),
          (coluna_x + coluna_largura, faixas[3][0] + faixas[3][1] / 2), estilo="<|-")

    _gravar(fig, "f1-arquitetura")


# --- F2: da análise ao laudo ---------------------------------------------------------

def f2_fluxo() -> None:
    """O ponto de entrada único e os quatro módulos, em quatro faixas."""
    fig, ax = _tela(LARGURA, 3.4)

    faixas = _linhas_em_faixas([0.85, 1.25, 1.15], topo=1 - MARGEM, base=MARGEM,
                               respiro=0.075)
    (y_topo, h_topo), (y_meio, h_meio), (y_base, h_base) = faixas
    direita = 1 - MARGEM

    # Entrada e ponto de entrada.
    _caixa(ax, MARGEM, y_topo, 0.26, h_topo, fundo=CLARO)
    ax.text(MARGEM + 0.13, y_topo + h_topo / 2,
            "análise de solo\n+ cultura\n+ contexto",
            ha="center", va="center", fontsize=8.3, linespacing=1.4, zorder=3)

    entrada_fim = MARGEM + 0.26
    _caixa(ax, entrada_fim + 0.055, y_topo, direita - entrada_fim - 0.055, h_topo,
           espessura=1.6)
    centro_x = (entrada_fim + 0.055 + direita) / 2
    ax.text(centro_x, y_topo + h_topo * 0.62, "gerar_laudo()", ha="center",
            va="center", fontsize=10, fontweight="bold", family="DejaVu Sans Mono",
            zorder=3)
    ax.text(centro_x, y_topo + h_topo * 0.26, "ponto de entrada único · determinística",
            ha="center", va="center", fontsize=8, color=CINZA, zorder=3)
    _seta(ax, (entrada_fim, y_topo + h_topo / 2), (entrada_fim + 0.055, y_topo + h_topo / 2))

    # Os quatro módulos. Subtítulos curtos, em até três linhas: na largura de um quarto
    # da figura, frase de uma linha só invadia a caixa vizinha.
    etapas = [
        ("1. Calagem", "critério\ndo grupo\nSMP e PRNT"),
        ("2. Adubação", "classe\nde teor\ncorreção e\nmanutenção"),
        ("3. Formulação", "três\ncaminhos\n(ADR 0009)"),
        ("4. Aptidão", "sete\nfatores\nfator mínimo"),
    ]
    vao = 0.022
    largura_etapa = (direita - MARGEM - vao * 3) / 4
    for i, (titulo, apoio) in enumerate(etapas):
        x = MARGEM + i * (largura_etapa + vao)
        _caixa(ax, x, y_meio, largura_etapa, h_meio)
        ax.text(x + largura_etapa / 2, y_meio + h_meio * 0.72, titulo, ha="center",
                va="center", fontsize=8.8, fontweight="bold", zorder=3)
        ax.text(x + largura_etapa / 2, y_meio + h_meio * 0.34, apoio, ha="center",
                va="center", fontsize=7.2, color=CINZA, linespacing=1.5, zorder=3)
        if i:
            _seta(ax, (x - vao, y_meio + h_meio / 2), (x, y_meio + h_meio / 2))
    _seta(ax, (centro_x, y_topo), (centro_x, y_meio + h_meio))

    # Saída: laudo à esquerda, dois cenários à direita.
    largura_laudo = 0.56
    _caixa(ax, MARGEM, y_base, largura_laudo, h_base)
    ax.text(MARGEM + 0.02, y_base + h_base * 0.78, "Laudo", fontsize=9,
            fontweight="bold", va="center", zorder=3)
    ax.text(MARGEM + 0.02, y_base + h_base * 0.34,
            "quatro doses · interpretação\nqual adubo comprar · como aplicar\n"
            "trilha com tabela e página",
            fontsize=7.4, color=CINZA, va="center", linespacing=1.5, zorder=3)
    _seta(ax, (MARGEM + largura_laudo / 2, y_meio), (MARGEM + largura_laudo / 2,
                                                     y_base + h_base))

    cenarios_x = MARGEM + largura_laudo + 0.045
    largura_cenario = (direita - cenarios_x - 0.018) / 2
    for i, (nome, fundo) in enumerate((("atual", CLARO), ("potencial", MEDIO))):
        x = cenarios_x + i * (largura_cenario + 0.018)
        _caixa(ax, x, y_base + h_base * 0.42, largura_cenario, h_base * 0.58, fundo=fundo)
        ax.text(x + largura_cenario / 2, y_base + h_base * 0.71, nome, ha="center",
                va="center", fontsize=8.2, zorder=3)
    ax.text(cenarios_x + (direita - cenarios_x) / 2, y_base + h_base * 0.18,
            "a diferença é o ganho\natribuível à recomendação", ha="center", va="center",
            fontsize=7.4, color=CINZA, linespacing=1.45, zorder=3)
    _seta(ax, (cenarios_x + (direita - cenarios_x) / 2, y_meio),
          (cenarios_x + (direita - cenarios_x) / 2, y_base + h_base))

    _gravar(fig, "f2-fluxo")


# --- F3: como a dose de calcário é decidida -------------------------------------------

def f3_calagem() -> None:
    """Seis passos, cada um com a tabela e a página que o sustentam."""
    fig, ax = _tela(LARGURA, 3.9)

    passos = [
        ("Cultura + sistema de manejo", "Tabela 5.1 e critério do grupo"),
        ("Qual o critério deste grupo?", "Tabelas 5.3 a 5.7 — disparo e pH alvo"),
        ("O pH dispara a calagem?", "o pH de referência NÃO é o gatilho"),
        ("Quanto de calcário PRNT 100%?", "Tabela 5.2 — índice SMP × pH alvo"),
        ("Ajuste de manejo e profundidade", "Tab. 5.3 nota (1) · Tab. 5.6 nota (5)"),
        ("Correção pelo corretivo real", "Cap. 8, p. 298 — dose × 100 / PRNT"),
    ]
    coluna_largura = 0.56
    faixas = _linhas_em_faixas([1] * 6, topo=1 - MARGEM, base=MARGEM, respiro=0.032)

    for i, ((y, altura), (titulo, fonte)) in enumerate(zip(faixas, passos)):
        _caixa(ax, MARGEM, y, coluna_largura, altura)
        ax.text(MARGEM + 0.022, y + altura * 0.66, titulo, fontsize=8.8,
                fontweight="bold", va="center", zorder=3)
        ax.text(MARGEM + 0.022, y + altura * 0.28, fonte, fontsize=7.3, color=CINZA,
                va="center", style="italic", zorder=3)
        if i < len(passos) - 1:
            meio = MARGEM + coluna_largura / 2
            _seta(ax, (meio, y), (meio, y - 0.032))

    # Saída lateral do passo 3.
    y3, h3 = faixas[2]
    ax.annotate("não dispara:\ncalcário 0,0 t/ha,\ncom o motivo escrito",
                xy=(MARGEM + coluna_largura, y3 + h3 / 2),
                xytext=(MARGEM + coluna_largura + 0.06, y3 + h3 / 2),
                fontsize=7.6, va="center", color=TINTA, linespacing=1.4,
                arrowprops=dict(arrowstyle="-|>", color=CINZA, linewidth=1))

    # Casos especiais, alinhados ao bloco de baixo.
    painel_x = MARGEM + coluna_largura + 0.05
    painel_y = faixas[5][0]
    painel_altura = faixas[3][0] - painel_y
    ax.text(painel_x, painel_y + painel_altura, "Casos especiais", fontsize=8.4,
            fontweight="bold", va="top", zorder=3)
    especiais = [
        "plantio direto consolidado:\num quarto da dose, teto\nde 5 t/ha",
        "SMP acima de 6,3: equações\npolinomiais, não a tabela",
        "sem pH de referência:\ndecide pela saturação\npor bases",
    ]
    y = painel_y + painel_altura - 0.055
    for texto in especiais:
        ax.text(painel_x, y, "· " + texto, fontsize=7.4, va="top", color=TINTA,
                linespacing=1.45, zorder=3)
        y -= 0.055 * (texto.count("\n") + 1) + 0.028

    _gravar(fig, "f3-calagem")


# --- F4: os três caminhos da formulação -----------------------------------------------

#: Nome de leitura dos fertilizantes simples, para caber na coluna.
_NOME_DO_SIMPLES = {
    "ureia": "ureia",
    "superfosfato_triplo": "superfosfato triplo",
    "cloreto_de_potassio": "cloreto de potássio",
}


def f4_formulacao() -> None:
    """O exemplo do Manual (p. 311) resolvido nos três caminhos, pelo próprio motor."""
    from siras.conhecimento.carregador import carregar_formulas_npk
    from siras.dominio.laudo import RecomendacaoAdubacao
    from siras.motor.formulacao import recomendar_formulacao

    rec = RecomendacaoAdubacao(n=60, p2o5=120, k2o=80,
                               classe_p="muito_baixo", classe_k="medio")
    r = recomendar_formulacao(rec, carregar_formulas_npk(), n_plantio=10)

    fig, ax = _tela(LARGURA, 3.15)
    direita = 1 - MARGEM

    (y_cab, h_cab), (y_col, h_col) = _linhas_em_faixas(
        [0.34, 1.0], topo=1 - MARGEM, base=MARGEM, respiro=0.07
    )

    _caixa(ax, MARGEM, y_cab, direita - MARGEM, h_cab, fundo=CLARO)
    ax.text((MARGEM + direita) / 2, y_cab + h_cab * 0.64,
            "Recomendação:  N 60   ·   P₂O₅ 120   ·   K₂O 80   kg/ha",
            ha="center", va="center", fontsize=9.4, fontweight="bold", zorder=3)
    ax.text((MARGEM + direita) / 2, y_cab + h_cab * 0.24,
            "com 10 kg/ha de N informados para a semeadura",
            ha="center", va="center", fontsize=7.8, color=CINZA, zorder=3)

    colunas = [
        ("A. Fórmula ideal", "para encomendar",
         [f"{o.formula_id}  —  {o.dose_kg_ha:.0f} kg/ha" for o in r.ideais]),
        ("B. Do catálogo", "para comprar pronto",
         [f"{o.formula_id}  —  {o.dose_kg_ha:.0f} kg/ha" for o in r.catalogo]),
        ("C. Adubos simples", "sempre exata",
         [f"{_NOME_DO_SIMPLES.get(c.produto, c.produto)}\n      {c.dose_kg_ha:.0f} kg/ha"
          for c in (r.mistura.complementos if r.mistura else [])]),
    ]
    vao = 0.025
    largura = (direita - MARGEM - vao * 2) / 3
    for i, (titulo, sub, linhas) in enumerate(colunas):
        x = MARGEM + i * (largura + vao)
        _caixa(ax, x, y_col, largura, h_col)
        ax.text(x + largura / 2, y_col + h_col * 0.86, titulo, ha="center",
                va="center", fontsize=8.8, fontweight="bold", zorder=3)
        ax.text(x + largura / 2, y_col + h_col * 0.72, sub, ha="center", va="center",
                fontsize=7.4, color=CINZA, style="italic", zorder=3)
        for j, linha in enumerate(linhas[:3]):
            ax.text(x + 0.018, y_col + h_col * (0.52 - j * 0.19), linha, fontsize=7.6,
                    va="center", linespacing=1.6, zorder=3)
        _seta(ax, (x + largura / 2, y_cab), (x + largura / 2, y_col + h_col))

    _gravar(fig, "f4-formulacao")


# --- F5: custo × dose, com os pontos de quebra ----------------------------------------

def f5_pontos_de_quebra() -> None:
    """Por que basta avaliar dois pontos: a função é convexa e linear por partes."""
    from siras.motor.formulacao import W_EXC, W_FALTA, W_OP

    teores = {"n": 5.0, "p2o5": 25.0, "k2o": 25.0}
    rec = {"n": 120.0, "p2o5": 60.0, "k2o": 120.0}

    def custo(d: float) -> float:
        fornecido = {i: d * teores[i] / 100.0 for i in ("n", "p2o5", "k2o")}
        excesso = sum(max(0.0, fornecido[i] - rec[i]) for i in ("n", "p2o5", "k2o"))
        faltas = {i: max(0.0, rec[i] - fornecido[i]) for i in ("p2o5", "k2o")}
        operacoes = sum(1 for v in faltas.values() if v > 0.5)
        return W_EXC * excesso + W_FALTA * sum(faltas.values()) + W_OP * operacoes

    doses = [d * 2.0 for d in range(0, 351)]
    custos = [custo(d) for d in doses]

    quebra_p = rec["p2o5"] * 100 / teores["p2o5"]
    quebra_k = rec["k2o"] * 100 / teores["k2o"]

    fig, ax = plt.subplots(figsize=(LARGURA, 3.1))
    ax.plot(doses, custos, color=TINTA, linewidth=1.8, zorder=3)

    for x, rotulo in ((quebra_p, "cobre o P₂O₅"), (quebra_k, "cobre o K₂O")):
        ax.axvline(x, color=CINZA, linewidth=0.9, linestyle=(0, (4, 3)), zorder=1)
        ax.plot([x], [custo(x)], "o", color=VERDE, markersize=7,
                markeredgecolor=TINTA, markeredgewidth=1.1, zorder=4)
        ax.annotate(f"{rotulo}\n{x:.0f} kg/ha · custo {custo(x):.0f}",
                    xy=(x, custo(x)), xytext=(x + 28, custo(x) + 26),
                    fontsize=8, linespacing=1.35,
                    arrowprops=dict(arrowstyle="-", color=CINZA, linewidth=0.8))

    ax.set_xlabel("Dose da fórmula 05-25-25 (kg/ha)")
    ax.set_ylabel("Custo da função objetivo")
    ax.set_xlim(0, 700)
    ax.set_ylim(0, max(custos) * 1.05)
    ax.grid(axis="y", color=CLARO, linewidth=0.8)
    ax.set_axisbelow(True)
    # O título precisa ser exato: excesso e falta são convexos e lineares por partes,
    # mas o termo da operação de complemento é CONSTANTE POR TRECHOS, e é ele que produz
    # os saltos visíveis. Chamar o conjunto de "convexo" seria impreciso, e o gráfico
    # mostra a imprecisão.
    ax.set_title(
        "Excesso e falta são convexos e lineares por partes; o custo da operação é\n"
        "constante por trechos. Nos dois casos o mínimo está num ponto de quebra.",
        fontsize=8.6, color=CINZA, pad=10, loc="left", linespacing=1.4,
    )

    _gravar(fig, "f5-pontos-de-quebra")


# --- F6: aptidão nos dois cenários -----------------------------------------------------

def f6_aptidao() -> None:
    """O diferencial integrador: o mesmo solo, antes e depois da correção recomendada."""
    from siras.conhecimento.carregador import carregar_dados_comum
    from siras.dominio.analise import AnaliseSolo, Contexto
    from siras.motor.laudo import gerar_laudo

    analise = AnaliseSolo(
        ph_agua=5.0, indice_smp=5.3, argila=24.0, mo=2.1,
        p=4.0, k=42.0, ctc_ph7=7.2, al=1.6, ca=1.9, mg=0.7, v_percent=38.0,
    )
    contexto = Contexto(
        cultura_id="milho", sistema_manejo="convencional",
        condicao_area="todos os casos", prnt=85.0,
        profundidade_incorporacao_cm=20.0, cultivo=1, expectativa_rendimento=8.0,
        antecedente="graminea",
    )
    laudo = gerar_laudo(analise, "milho", contexto, carregar_dados_comum())

    ordem = ["F1_acidez", "F2_fosforo", "F3_potassio", "F4_ca_mg",
             "F5_ctc", "F6_mo", "F7_textura"]
    nomes = ["Acidez", "Fósforo", "Potássio", "Ca e Mg", "CTC", "Mat. orgânica", "Textura"]

    def graus(resultado) -> List[int]:
        # `grau` já é o inteiro de 0 a 4 do CCAE; `rotulo` é o nome dele. Mapear o
        # inteiro por uma tabela de rótulos devolvia zero em tudo, e o primeiro desenho
        # saiu com o gráfico vazio.
        por_fator = {f.id: f.grau for f in resultado.fatores}
        return [por_fator.get(f, 0) for f in ordem]

    atual, potencial = graus(laudo.aptidao_atual), graus(laudo.aptidao_potencial)

    fig, ax = plt.subplots(figsize=(LARGURA, 3.0))
    posicoes = range(len(ordem))
    largura = 0.38
    ax.bar([p - largura / 2 for p in posicoes], atual, largura,
           color=MEDIO, edgecolor=TINTA, linewidth=1.0, label="Solo como está")
    ax.bar([p + largura / 2 for p in posicoes], potencial, largura,
           color="white", edgecolor=TINTA, linewidth=1.0, hatch="///",
           label="Após as correções recomendadas")

    ax.set_xticks(list(posicoes))
    ax.set_xticklabels(nomes, fontsize=8.2)
    ax.set_yticks(range(5))
    ax.set_yticklabels(["Nula", "Ligeira", "Moderada", "Forte", "Muito forte"], fontsize=8)
    ax.set_ylabel("Grau de limitação")
    ax.set_ylim(0, 5.4)
    ax.grid(axis="y", color=CLARO, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False, loc="upper right", ncol=1,
              bbox_to_anchor=(1.0, 0.98))

    determinante = laudo.aptidao_atual.fator_determinante
    if determinante in ordem:
        i = ordem.index(determinante)
        ax.annotate("fator mínimo:\ndetermina a classe",
                    xy=(i - largura / 2, atual[i]), xytext=(i - 0.4, atual[i] + 1.1),
                    fontsize=7.8, linespacing=1.3, color=TINTA,
                    arrowprops=dict(arrowstyle="-|>", color=TINTA, linewidth=1))

    ax.set_title(
        "A regra do fator mínimo: a classe é a do fator mais limitante, não a média",
        fontsize=8.8, color=CINZA, pad=10, loc="left",
    )

    _gravar(fig, "f6-aptidao")


# --- F7: concordância com intervalo de Wilson ------------------------------------------

def f7_concordancia() -> None:
    """Torna visível o problema do tamanho da amostra, em vez de escondê-lo na tabela."""
    from siras.validacao.concordancia import apurar_aptidao, apurar_recomendacao

    recomendacao = apurar_recomendacao()
    aptidao = apurar_aptidao()

    nomes_de_grupo = {
        "graos": "Grãos", "hortalicas": "Hortaliças", "tuberculos": "Tubérculos",
        "outras": "Cana e tabaco", "frutiferas": "Frutíferas", "erva_mate": "Erva-mate",
    }

    linhas = []
    for grupo, parcial in recomendacao.por_grupo().items():
        linhas.append((nomes_de_grupo.get(grupo, grupo), parcial.taxa(),
                       parcial.intervalo(), parcial.total, False))
    linhas.append(("Recomendação (global)", recomendacao.taxa(),
                   recomendacao.intervalo(), recomendacao.total, True))
    linhas.append(("Aptidão — classe", aptidao.taxa_classe(),
                   aptidao.intervalo_classe(), aptidao.total, True))

    fig, ax = plt.subplots(figsize=(LARGURA, 0.46 * len(linhas) + 1.25))
    posicoes = list(range(len(linhas)))[::-1]

    for y, (nome, taxa, intervalo, n, destaque) in zip(posicoes, linhas):
        inferior, superior = intervalo
        ax.plot([inferior * 100, superior * 100], [y, y],
                color=TINTA, linewidth=2.2 if destaque else 1.4, solid_capstyle="butt")
        for limite in (inferior, superior):
            ax.plot([limite * 100, limite * 100], [y - 0.16, y + 0.16],
                    color=TINTA, linewidth=1.4 if destaque else 1.0)
        ax.plot([taxa * 100], [y], "o", markersize=8 if destaque else 6,
                color=VERDE if destaque else "white",
                markeredgecolor=TINTA, markeredgewidth=1.3, zorder=4)
        ax.text(101.5, y, f"n = {n}", fontsize=8, va="center", color=CINZA)

    ax.axvline(80, color=TINTA, linewidth=1.3, linestyle=(0, (5, 3)))
    # Abaixo do eixo, e não no topo: lá em cima ela cobria o título.
    ax.annotate("limiar da hipótese: 80%", xy=(80, -0.72), xytext=(80, -0.72),
                fontsize=8, ha="center", va="center", color=TINTA,
                annotation_clip=False,
                bbox=dict(facecolor="white", edgecolor="none", pad=2.5))

    ax.set_yticks(posicoes)
    ax.set_yticklabels([nome for nome, *_ in linhas], fontsize=8.5)
    ax.set_ylim(-1.1, len(linhas) - 0.4)
    ax.set_xlim(28, 108)
    ax.set_xticks([40, 50, 60, 70, 80, 90, 100])
    ax.set_xlabel("Concordância com o oráculo (%), com intervalo de confiança de 95% de Wilson")
    ax.grid(axis="x", color=CLARO, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    inferior_global = recomendacao.intervalo()[0] * 100
    ax.set_title(
        f"Todas as taxas pontuais são de 100%. O limite inferior do intervalo global da\n"
        f"recomendação fica em {inferior_global:.1f}% — abaixo do limiar, por tamanho de amostra.",
        fontsize=8.6, color=CINZA, pad=12, loc="left", linespacing=1.4,
    )

    _gravar(fig, "f7-concordancia")


# --- F8: severidade por heurística (depende da coleta) ----------------------------------

def f8_usabilidade() -> None:
    """Severidade por heurística. NÃO é gerada antes de a coleta existir."""
    entrada = (
        Path(__file__).parent.parent
        / "docs" / "usabilidade" / "resultados" / "heuristicas.csv"
    )
    if not entrada.exists():
        print(
            "  F8 NAO gerada: falta "
            f"{entrada.relative_to(Path(__file__).parent.parent)}.\n"
            "     Rode scripts/consolidar_heuristicas.py sobre o CSV do Forms depois da\n"
            "     coleta. Ate la, o \\pendente{} do artigo continua no lugar."
        )
        return

    import csv

    with open(entrada, encoding="utf-8") as arquivo:
        dados = [linha for linha in csv.DictReader(arquivo) if linha["media"]]
    if not dados:
        print("  F8 NAO gerada: o arquivo existe mas nao tem media por heuristica.")
        return

    dados.sort(key=lambda linha: float(linha["media"]))
    nomes = [f"{linha['numero']}. {linha['heuristica']}" for linha in dados]
    medias = [float(linha["media"]) for linha in dados]
    medianas = [float(linha["mediana"]) for linha in dados]

    fig, ax = plt.subplots(figsize=(LARGURA, 0.34 * len(dados) + 1.3))
    posicoes = list(range(len(dados)))
    ax.barh(posicoes, medias, 0.62, color=MEDIO, edgecolor=TINTA, linewidth=1.0,
            label="Média")
    ax.plot(medianas, posicoes, "D", color="white", markersize=6,
            markeredgecolor=TINTA, markeredgewidth=1.2, label="Mediana", zorder=4)

    ax.set_yticks(posicoes)
    ax.set_yticklabels(nomes, fontsize=8.2)
    ax.set_xlim(0, 4.3)
    ax.set_xticks(range(5))
    ax.set_xlabel("Severidade percebida (0 = não é problema · 4 = catástrofe)")
    ax.grid(axis="x", color=CLARO, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_title(
        "Mediana ao lado da média: com poucas respostas, um avaliador severo desloca a média",
        fontsize=8.6, color=CINZA, pad=10, loc="left",
    )

    _gravar(fig, "f8-usabilidade")


FIGURAS: Dict[str, Callable[[], None]] = {
    "f1": f1_arquitetura,
    "f2": f2_fluxo,
    "f3": f3_calagem,
    "f4": f4_formulacao,
    "f5": f5_pontos_de_quebra,
    "f6": f6_aptidao,
    "f7": f7_concordancia,
    "f8": f8_usabilidade,
}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Gera as figuras do artigo final.")
    parser.add_argument("--figura", choices=sorted(FIGURAS), default=None,
                        help="gera só uma; sem isso, gera todas")
    args = parser.parse_args(argv)

    escolhidas = [args.figura] if args.figura else sorted(FIGURAS)
    print(f"Gerando {len(escolhidas)} figura(s) em {SAIDA}:")
    for nome in escolhidas:
        FIGURAS[nome]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
