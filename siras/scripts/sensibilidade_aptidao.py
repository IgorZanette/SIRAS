"""
Análise de sensibilidade da aptidão edáfica (CCAE v1.3, §9.4).

Roda o conjunto de conformidade (casos com gabarito CONFERIDO ou CORRIGIDO_NA_CONFERENCIA,
cada um no cenário que o gabarito declara) em quatro configurações e reporta a distribuição
de classes em cada uma, quantos casos mudam em relação ao baseline e a conformidade com o
gabarito:

    1. baseline: fator mínimo puro, sete fatores (a configuração do sistema)
    2. com REBAIXAMENTO_POR_ACUMULO ativado (decisão A-1)
    3. sem F7, a textura
    4. sem F5 e F7, só fatores de fertilidade em sentido estrito

Nenhum arquivo de dados é alterado. As configurações são aplicadas sobre uma cópia, em
memória, dos dados carregados — o config_aptidao.json em disco continua sendo a fonte do
sistema. "Sem F5" é obtido com F5_GRAU_MAXIMO = NULO: como a classe é dada pelo fator de
maior grau, um fator preso em nulo nunca a determina, o que equivale a retirá-lo.

Uso, de dentro de siras/:
    python scripts/sensibilidade_aptidao.py
    python scripts/sensibilidade_aptidao.py --saida ../trabalho_de_conclusao/validacao/resultados/
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import siras.motor.aptidao as aptidao  # noqa: E402
from siras.conhecimento.carregador import carregar_dados_comum  # noqa: E402

CASOS = Path(__file__).parent.parent / "testes" / "casos"
CLASSES = ["APTA", "APTA_COM_RESTRICOES", "RESTRITA", "INAPTA_SEM_CORRECAO"]
ROTULO = {"APTA": "Apta", "APTA_COM_RESTRICOES": "Apta c/ restrições",
          "RESTRITA": "Restrita", "INAPTA_SEM_CORRECAO": "Inapta s/ correção"}

CONFIGURACOES = [
    ("1", "Baseline: fator mínimo puro, sete fatores", {}),
    ("2", "Com rebaixamento por acúmulo (A-1)", {"REBAIXAMENTO_POR_ACUMULO": True}),
    ("3", "Sem F7 (textura)", {"F7_ATIVO": False}),
    ("4", "Sem F5 e F7 (fertilidade estrita)", {"F7_ATIVO": False, "F5_GRAU_MAXIMO": "NULO"}),
]


def _casos():
    entradas = {c["id_caso"]: c for c in
                json.loads((CASOS / "entradas_aptidao.json").read_text(encoding="utf-8"))["casos"]}
    with open(CASOS / "gabarito_aptidao.csv", encoding="utf-8") as f:
        gabarito = [g for g in csv.DictReader(f)
                    if g["status"] in ("CONFERIDO", "CORRIGIDO_NA_CONFERENCIA")]
    return entradas, gabarito


def rodar(alteracoes, entradas, gabarito, base):
    dados = copy.deepcopy(base)
    dados["config_aptidao"].update(alteracoes)
    original = aptidao.carregar_dados_comum
    aptidao.carregar_dados_comum = lambda: dados
    try:
        saida = {}
        for g in gabarito:
            caso = entradas[g["id_caso"]]
            r = aptidao.avaliar_aptidao_ccae(analise=caso["entrada"], cultura=caso["cultura"],
                                             cenario=g["cenario"])
            saida[(g["id_caso"], g["cenario"])] = r.classe
        return saida
    finally:
        aptidao.carregar_dados_comum = original


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args(argv)

    entradas, gabarito = _casos()
    base = carregar_dados_comum()
    cenarios = Counter(g["cenario"] for g in gabarito)
    resultados = {cid: rodar(alt, entradas, gabarito, base) for cid, _, alt in CONFIGURACOES}
    baseline = resultados["1"]

    linhas = [
        "# Sensibilidade da aptidão edáfica (CCAE §9.4)",
        "",
        f"Gerado por `scripts/sensibilidade_aptidao.py`. Conjunto de conformidade: "
        f"**{len(gabarito)} casos**, cada um no cenário que o gabarito declara "
        f"({cenarios['ATUAL']} no atual, {cenarios['POTENCIAL']} no potencial).",
        "",
        "| # | Configuração | " + " | ".join(ROTULO[c] for c in CLASSES)
        + " | Mudam vs. 1 | Conformidade |",
        "|---|---|" + "---|" * len(CLASSES) + "---|---|",
    ]
    detalhe = []
    for cid, nome, _ in CONFIGURACOES:
        r = resultados[cid]
        dist = Counter(r.values())
        mudam = [k for k in r if r[k] != baseline[k]]
        conf = sum(1 for g in gabarito if r[(g["id_caso"], g["cenario"])] == g["classe_esperada"])
        linhas.append(f"| {cid} | {nome} | " + " | ".join(str(dist.get(c, 0)) for c in CLASSES)
                      + f" | {len(mudam) if cid != '1' else '—'} | {conf}/{len(gabarito)} |")
        if cid != "1" and mudam:
            trans = Counter(f"{ROTULO[baseline[k]]} → {ROTULO[r[k]]}" for k in mudam)
            por_cen = Counter(k[1] for k in mudam)
            detalhe += [f"**Configuração {cid}** — {len(mudam)} casos mudam "
                        f"({por_cen.get('ATUAL', 0)} no atual, {por_cen.get('POTENCIAL', 0)} no potencial): "
                        + "; ".join(f"{t} ({n})" for t, n in trans.most_common()) + ".",
                        "", "Casos: " + ", ".join(f"`{k[0]}` ({k[1].lower()})" for k in sorted(mudam)), ""]
        elif cid != "1":
            detalhe += [f"**Configuração {cid}** — nenhum caso muda.", ""]

    linhas += ["", "## O que muda em cada configuração", ""] + detalhe
    linhas += [
        "## Como ler",
        "",
        "A conformidade só é 100% no baseline porque o gabarito foi produzido à mão com a "
        "configuração do sistema. Nas demais, a queda **não é erro**: mede quanto a classe "
        "depende daquela decisão do autor.",
        "",
    ]
    relatorio = "\n".join(linhas)
    if args.saida:
        args.saida.mkdir(parents=True, exist_ok=True)
        (args.saida / "sensibilidade_aptidao.md").write_text(relatorio, encoding="utf-8")
        print(f"gravado em {args.saida / 'sensibilidade_aptidao.md'}")
    else:
        print(relatorio)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
