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


def _gravar(fig, nome: str) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA / f"{nome}.png"
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"  gravada: {caminho.relative_to(Path(__file__).parent.parent)}")


def _caixa(ax, x, y, largura, altura, texto, *, fundo="white", borda=TINTA,
           peso="normal", tamanho=9, traco="-"):
    ax.add_patch(FancyBboxPatch(
        (x, y), largura, altura, boxstyle="round,pad=0.012,rounding_size=0.02",
        facecolor=fundo, edgecolor=borda, linewidth=1.1, linestyle=traco,
    ))
    ax.text(x + largura / 2, y + altura / 2, texto, ha="center", va="center",
            fontsize=tamanho, fontweight=peso, color=TINTA, linespacing=1.35)


def _seta(ax, inicio, fim, *, estilo="-|>", cor=TINTA, traco="-"):
    ax.add_patch(FancyArrowPatch(
        inicio, fim, arrowstyle=estilo, mutation_scale=11,
        color=cor, linewidth=1.1, linestyle=traco, shrinkA=1, shrinkB=1,
    ))


def _tela(largura_pol, altura_pol):
    fig, ax = plt.subplots(figsize=(largura_pol, altura_pol))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


# --- F1: arquitetura em camadas ------------------------------------------------------

def f1_arquitetura() -> None:
    """Por que o núcleo roda sem Flask e é testável isolado."""
    fig, ax = _tela(LARGURA, 3.5)

    camadas = [
        (0.78, "siras/web/", "Flask: rotas, formulário, templates", CLARO),
        (0.60, "siras/relatorio/", "Laudo para a tela e para o papel", CLARO),
        (0.42, "siras/motor/", "Regras SE-ENTÃO: calagem, adubação,\nformulação, aptidão", "white"),
        (0.24, "siras/conhecimento/", "Carregamento e validação da base", "white"),
        (0.06, "siras/dominio/", "Entidades: análise, contexto, laudo", "white"),
    ]
    for y, nome, descricao, fundo in camadas:
        _caixa(ax, 0.04, y, 0.56, 0.13, "", fundo=fundo)
        ax.text(0.07, y + 0.085, nome, fontsize=9.5, fontweight="bold", va="center")
        ax.text(0.07, y + 0.040, descricao, fontsize=8, color=CINZA, va="center",
                linespacing=1.3)

    for y in (0.78, 0.60, 0.42, 0.24):
        _seta(ax, (0.32, y), (0.32, y - 0.05))

    # A fronteira que o trabalho declara.
    ax.plot([0.02, 0.70], [0.565, 0.565], color=VERDE, linewidth=1.6, linestyle=(0, (5, 3)))
    ax.text(0.705, 0.565, "acima: depende de Flask\nabaixo: Python puro,\nroda por linha de comando",
            fontsize=8, va="center", color=TINTA, linespacing=1.4)

    _caixa(ax, 0.66, 0.06, 0.30, 0.31,
           "dados/\n\ncomum/ — Manual\nculturas/ — Manual\nmercado/ — não é Manual",
           fundo="white", traco=(0, (4, 2)), tamanho=8)
    _seta(ax, (0.655, 0.30), (0.605, 0.30), estilo="<|-")

    ax.text(0.02, 0.97,
            "O motor e o domínio não importam Flask. É o que permite rodar as 5.167\n"
            "verificações sem subir servidor, e o que mantém a regra agronômica\n"
            "independente da interface.",
            fontsize=8.5, va="top", color=CINZA, linespacing=1.45)

    _gravar(fig, "f1-arquitetura")


# --- F2: da análise ao laudo ---------------------------------------------------------

def f2_fluxo() -> None:
    """O ponto de entrada único, e por que os dois cenários de aptidão saem juntos."""
    fig, ax = _tela(LARGURA, 3.2)

    _caixa(ax, 0.02, 0.76, 0.22, 0.15,
           "Análise de solo\n+ cultura\n+ contexto", fundo=CLARO, tamanho=8.5)
    _caixa(ax, 0.30, 0.76, 0.40, 0.15, "gerar_laudo()\nfunção pura e determinística",
           peso="bold", tamanho=9)
    _seta(ax, (0.245, 0.835), (0.295, 0.835))

    etapas = [
        (0.02, "1. Calagem", "critério do grupo →\níndice SMP → PRNT"),
        (0.26, "2. Adubação", "classe de teor →\ncorreção + manutenção"),
        (0.50, "3. Formulação", "três caminhos\n(ADR 0009)"),
        (0.74, "4. Aptidão", "sete fatores,\nfator mínimo"),
    ]
    for x, titulo, detalhe in etapas:
        _caixa(ax, x, 0.42, 0.22, 0.20, "", fundo="white")
        ax.text(x + 0.11, 0.565, titulo, ha="center", fontsize=9, fontweight="bold")
        ax.text(x + 0.11, 0.487, detalhe, ha="center", fontsize=7.8, color=CINZA,
                linespacing=1.35)

    _seta(ax, (0.50, 0.755), (0.50, 0.63))
    for x in (0.24, 0.48, 0.72):
        _seta(ax, (x, 0.52), (x + 0.02, 0.52))

    _caixa(ax, 0.74, 0.17, 0.11, 0.18, "atual", fundo=CLARO, tamanho=8)
    _caixa(ax, 0.86, 0.17, 0.11, 0.18, "potencial", fundo=MEDIO, tamanho=8)
    _seta(ax, (0.85, 0.42), (0.85, 0.36))
    ax.text(0.855, 0.09, "a diferença entre os dois é o ganho\natribuível à recomendação acima",
            ha="center", fontsize=7.8, color=CINZA, linespacing=1.35)

    _caixa(ax, 0.02, 0.17, 0.66, 0.18,
           "Laudo:  quatro doses  ·  interpretação  ·  qual adubo comprar  ·  como aplicar\n"
           "+ trilha com a regra, a tabela e a página de cada número",
           fundo="white", tamanho=8.3)
    _seta(ax, (0.35, 0.41), (0.35, 0.36))

    ax.text(0.02, 0.985, "Uma passagem só. As mesmas entradas produzem sempre o mesmo laudo "
            "e a mesma trilha.", fontsize=8.5, va="top", color=CINZA)

    _gravar(fig, "f2-fluxo")


# --- F3: como a dose de calcário é decidida -------------------------------------------

def f3_calagem() -> None:
    """O diferencial de rastreabilidade, visualmente: cada caixa cita tabela e página."""
    fig, ax = _tela(LARGURA, 4.0)

    passos = [
        (0.80, "Cultura + sistema de manejo", "Tabela 5.1 e critério do grupo"),
        (0.64, "Qual é o critério deste grupo?", "Tabelas 5.3 a 5.7 — disparo e pH alvo"),
        (0.48, "O pH dispara a calagem?", "o pH de referência NÃO é o gatilho"),
        (0.32, "Quanto de calcário PRNT 100%?", "Tabela 5.2 — índice SMP × pH alvo"),
        (0.16, "Ajuste de manejo e profundidade", "Tab. 5.3 nota (1) · Tab. 5.6 nota (5)"),
        (0.00, "Correção pelo corretivo real", "Cap. 8, p. 298 — dose × 100 / PRNT"),
    ]
    for y, titulo, fonte in passos:
        _caixa(ax, 0.06, y, 0.60, 0.115, "", fundo="white")
        ax.text(0.09, y + 0.072, titulo, fontsize=9, fontweight="bold", va="center")
        ax.text(0.09, y + 0.032, fonte, fontsize=7.6, color=CINZA, va="center",
                style="italic")
        if y > 0:
            _seta(ax, (0.36, y), (0.36, y - 0.045))

    ax.annotate("não dispara →\ncalcário 0,0 t/ha,\ncom o motivo escrito",
                xy=(0.665, 0.538), xytext=(0.70, 0.60),
                fontsize=7.8, color=CINZA, linespacing=1.35,
                arrowprops=dict(arrowstyle="-|>", color=CINZA, linewidth=1))

    ax.text(0.70, 0.33,
            "Casos especiais que\nentram aqui:\n\n"
            "· plantio direto\n  consolidado: ¼ da\n  dose, teto de 5 t/ha\n\n"
            "· SMP > 6,3: equações\n  polinomiais, não a\n  tabela\n\n"
            "· sem pH de referência:\n  decide por V%",
            fontsize=7.6, va="top", color=TINTA, linespacing=1.5)

    ax.text(0.02, 0.985,
            "Cada passo registra regra, entrada, saída e fonte na trilha do laudo. "
            "É o que torna\na recomendação conferível por um terceiro sem acesso ao código.",
            fontsize=8.5, va="top", color=CINZA, linespacing=1.45)

    _gravar(fig, "f3-calagem")


# --- F4: os três caminhos da formulação -----------------------------------------------

#: Nome de leitura dos fertilizantes simples. O id é identificador de arquivo; numa
#: figura de artigo vai o nome por extenso, acentuado.
_NOME_DO_SIMPLES = {
    "ureia": "ureia",
    "superfosfato_triplo": "sup. triplo",
    "cloreto_de_potassio": "cloreto de K",
}


def f4_formulacao() -> None:
    """O exemplo do Manual (p. 311) resolvido nos três caminhos, pelo próprio motor."""
    from siras.conhecimento.carregador import carregar_formulas_npk
    from siras.dominio.laudo import RecomendacaoAdubacao
    from siras.motor.formulacao import recomendar_formulacao

    rec = RecomendacaoAdubacao(n=60, p2o5=120, k2o=80,
                               classe_p="muito_baixo", classe_k="medio")
    r = recomendar_formulacao(rec, carregar_formulas_npk(), n_plantio=10)

    fig, ax = _tela(LARGURA, 3.9)

    _caixa(ax, 0.02, 0.86, 0.96, 0.11,
           "Recomendação:  N 60  ·  P₂O₅ 120  ·  K₂O 80  kg/ha      "
           "(N de plantio informado: 10)",
           fundo=CLARO, peso="bold", tamanho=8.6)

    colunas = [
        (0.02, "A. Fórmula ideal", "para encomendar",
         [f"{o.formula_id} — {o.dose_kg_ha:.0f} kg/ha" for o in r.ideais]),
        (0.35, "B. Do catálogo", "para comprar pronto",
         [f"{o.formula_id} — {o.dose_kg_ha:.0f} kg/ha" for o in r.catalogo]),
        (0.68, "C. Simples", "sempre exata",
         [f"{_NOME_DO_SIMPLES.get(c.produto, c.produto)} — {c.dose_kg_ha:.0f} kg/ha"
          for c in (r.mistura.complementos if r.mistura else [])]),
    ]
    for x, titulo, sub, linhas in colunas:
        _caixa(ax, x, 0.30, 0.30, 0.46, "", fundo="white")
        ax.text(x + 0.15, 0.715, titulo, ha="center", fontsize=9, fontweight="bold")
        ax.text(x + 0.15, 0.672, sub, ha="center", fontsize=7.8, color=CINZA,
                style="italic")
        for i, linha in enumerate(linhas[:4]):
            ax.text(x + 0.015, 0.615 - i * 0.055, "· " + linha, fontsize=7.3, va="center")
        _seta(ax, (x + 0.15, 0.855), (x + 0.15, 0.77))

    ax.text(0.02, 0.21,
            "As três fórmulas da coluna A são exatamente as que o Manual publica no exemplo\n"
            "da p. 311, com as doses que ele calcula — oráculo externo, não escrito por nós.",
            fontsize=8.2, va="top", linespacing=1.45)
    ax.text(0.02, 0.085,
            "A coluna B encontra ainda uma fórmula real de mercado, de mesma proporção, que o\n"
            "Manual não cita. O método sozinho não a apontaria; o catálogo sozinho não saberia\n"
            "qual escolher.",
            fontsize=8.2, va="top", color=CINZA, linespacing=1.45)

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
