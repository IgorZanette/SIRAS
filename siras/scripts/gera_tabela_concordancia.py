"""
Gera a tabela de concordância da validação — a tabela principal de Resultados.

Prometida em `trabalho_de_conclusao/validacao/protocolo.md`: taxa global e por grupo, IC 95% de Wilson, lista de
discordantes com o Trace, e saída em Markdown e CSV.

A apuração vive em `siras/validacao/concordancia.py`, e não aqui, porque o mesmo código
é exercitado por `testes/unidade/test_casos_validados.py`. Se o número publicado viesse
de um script que nenhum teste roda, ele seria a única afirmação do trabalho sem
verificação automática — justamente a que sustenta a H1.1.

Uso:
    python scripts/gera_tabela_concordancia.py
    python scripts/gera_tabela_concordancia.py --saida trabalho_de_conclusao/validacao/resultados/

Sem --saida, imprime o relatório na tela. Código de saída 1 se houver discordante, para
que a geração da tabela possa entrar em verificação automática.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Mesma convenção dos demais scripts: rodar por `python scripts/...` sem instalar o
# pacote. O insert vem antes do import de siras, de propósito.
sys.path.insert(0, str(Path(__file__).parent.parent))

# Windows abre o stdout em cp1252, e o relatório tem acentuação e o símbolo de grau.
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from siras.validacao.concordancia import Apuracao, apurar_aptidao, apurar_recomendacao  # noqa: E402

#: Nome de leitura dos grupos. O id é identificador; a tabela da monografia leva o nome.
_NOME_DO_GRUPO = {
    "graos": "Grãos",
    "hortalicas": "Hortaliças",
    "tuberculos": "Tubérculos",
    "outras": "Cana e tabaco",
    "frutiferas": "Frutíferas",
    "erva_mate": "Erva-mate",
}


def _pct(valor: Optional[float]) -> str:
    if valor is None:
        return "—"
    return f"{valor * 100:.1f}".replace(".", ",") + "%"


def _ic(intervalo: Optional[Tuple[float, float]]) -> str:
    if intervalo is None:
        return "—"
    inferior, superior = intervalo
    return f"[{_pct(inferior)}; {_pct(superior)}]"


def _tabela_por_grupo(apuracao: Apuracao) -> List[str]:
    linhas = [
        "| Grupo | Casos | Concordantes | Taxa | IC 95% (Wilson) |",
        "|---|---|---|---|---|",
    ]
    for grupo, parcial in apuracao.por_grupo().items():
        linhas.append(
            f"| {_NOME_DO_GRUPO.get(grupo, grupo)} | {parcial.total} | "
            f"{parcial.concordantes} | {_pct(parcial.taxa())} | {_ic(parcial.intervalo())} |"
        )
    linhas.append(
        f"| **Global** | **{apuracao.total}** | **{apuracao.concordantes}** | "
        f"**{_pct(apuracao.taxa())}** | **{_ic(apuracao.intervalo())}** |"
    )
    return linhas


def relatorio_markdown(recomendacao: Apuracao, aptidao) -> str:
    linhas = [
        "# Concordância da validação",
        "",
        "Gerado por `scripts/gera_tabela_concordancia.py`. Protocolo em "
        "`trabalho_de_conclusao/validacao/protocolo.md`.",
        "",
        "## Dimensão 1 — recomendação de calagem e adubação (H1.1)",
        "",
        "Um caso é concordante quando **todas** as saídas que a referência declara "
        "coincidem com a saída do motor, admitida apenas tolerância de arredondamento "
        "(calcário com uma casa em t/ha, nutrientes inteiros em kg/ha). Acertar três de "
        "quatro é discordância.",
        "",
    ]
    linhas += _tabela_por_grupo(recomendacao)
    linhas += [
        "",
        f"Casos com oráculo: **{recomendacao.total}**. O protocolo declara alvo de 40 a "
        "80 — a diferença precisa ser declarada na monografia, junto do motivo, e não "
        "compensada no texto.",
        "",
    ]

    if recomendacao.discordantes:
        linhas += ["### Discordantes", ""]
        for r in recomendacao.discordantes:
            linhas.append(f"**{r.id}** — {r.descricao}")
            if r.erro:
                linhas.append(f"- erro de execução: `{r.erro}`")
            for d in r.divergencias:
                linhas.append(
                    f"- `{d.campo}`: esperado `{d.esperado}`, obtido `{d.obtido}`"
                )
            if r.trace:
                linhas.append("- trilha:")
                linhas += [f"  - `{passo}`" for passo in r.trace]
            linhas.append("")
    else:
        linhas += ["Nenhum caso discordante.", ""]

    linhas += [
        "## Dimensão 2 — conformidade da aptidão edáfica (CCAE)",
        "",
        "**Conformidade, não concordância.** Mede se a implementação reproduz o Caderno "
        "de Critérios congelado, não se os critérios estão agronomicamente corretos — a "
        "distinção é do próprio CCAE, §9, e precisa aparecer no texto.",
        "",
        "| Métrica | Casos | Acertos | Taxa | IC 95% (Wilson) |",
        "|---|---|---|---|---|",
        f"| Classe de aptidão | {aptidao.total} | {aptidao.classe_ok} | "
        f"{_pct(aptidao.taxa_classe())} | {_ic(aptidao.intervalo_classe())} |",
        f"| Fator determinante | {aptidao.total} | {aptidao.fator_ok} | "
        f"{_pct(aptidao.taxa_fator())} | — |",
        "",
    ]
    if aptidao.divergentes:
        linhas += ["### Divergentes", ""]
        linhas += [f"- {d}" for d in aptidao.divergentes]
        linhas.append("")
    else:
        linhas += ["Nenhuma divergência.", ""]

    return "\n".join(linhas) + "\n"


def escrever_csv(recomendacao: Apuracao, caminho: Path) -> None:
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["id", "grupo", "cultura", "concordante", "divergencias", "erro"])
        for r in recomendacao.resultados:
            escritor.writerow([
                r.id, r.grupo, r.cultura, int(r.concordante),
                "; ".join(f"{d.campo}: {d.esperado} != {d.obtido}" for d in r.divergencias),
                r.erro or "",
            ])


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera a tabela de concordância da validação."
    )
    parser.add_argument(
        "--saida", type=Path, default=None,
        help="diretório onde gravar concordancia.md e concordancia.csv "
             "(sem ele, imprime na tela)",
    )
    args = parser.parse_args(argv)

    recomendacao = apurar_recomendacao()
    aptidao = apurar_aptidao()
    relatorio = relatorio_markdown(recomendacao, aptidao)

    if args.saida is None:
        print(relatorio)
    else:
        args.saida.mkdir(parents=True, exist_ok=True)
        (args.saida / "concordancia.md").write_text(relatorio, encoding="utf-8")
        escrever_csv(recomendacao, args.saida / "concordancia.csv")
        print(
            f"gravado em {args.saida / 'concordancia.md'} e "
            f"{args.saida / 'concordancia.csv'}"
        )

    houve_falha = bool(recomendacao.discordantes or aptidao.divergentes)
    if houve_falha:
        print("ATENCAO: ha casos discordantes — ver o relatorio", file=sys.stderr)
    return 1 if houve_falha else 0


if __name__ == "__main__":
    raise SystemExit(main())
