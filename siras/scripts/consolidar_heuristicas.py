"""
Consolida as respostas do questionário pós-teste das dez heurísticas de Nielsen.

Lê o CSV exportado pela aba "Respostas" do Google Forms e produz, num comando, o material
que vai à monografia: severidade por heurística, ranking de prioridade e todos os relatos
agrupados, identificados pelo código do participante.

O protocolo está em trabalho_de_conclusao/usabilidade/protocolo.md; o instrumento, em
trabalho_de_conclusao/usabilidade/questionario.md.

Duas escolhas que o relatório declara, e que valem explicar aqui:

- **mediana ao lado da média.** Com cinco a oito respostas, um avaliador severo desloca a
  média inteira. Ver os dois números juntos mostra na hora quando isso aconteceu.
- **sem inferência.** Nada de intervalo de confiança nem teste de hipótese: a amostra é
  pequena e por conveniência, e a estatística é descritiva. Ver USABILIDADE.md §3.

Uso:
    python scripts/consolidar_heuristicas.py respostas.csv
    python scripts/consolidar_heuristicas.py respostas.csv --saida trabalho_de_conclusao/validacao/resultados/

Sem --saida, imprime o relatório em Markdown na tela.
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

#: As dez heurísticas, na ordem canônica. O rótulo curto é o que aparece nas tabelas da
#: monografia; o número é o que ordena.
HEURISTICAS = [
    (1, "Visibilidade do status do sistema"),
    (2, "Correspondência com o mundo real"),
    (3, "Controle e liberdade do usuário"),
    (4, "Consistência e padrões"),
    (5, "Prevenção de erros"),
    (6, "Reconhecimento em vez de memorização"),
    (7, "Flexibilidade e eficiência de uso"),
    (8, "Estética e design minimalista"),
    (9, "Ajuda para reconhecer e corrigir erros"),
    (10, "Ajuda e documentação"),
]

#: Como reconhecer, no cabeçalho do CSV, a coluna de cada tipo de pergunta. O Google Forms
#: exporta o enunciado inteiro como nome da coluna, e o enunciado muda se o autor editar o
#: formulário — por isso a detecção é por padrão, e não por posição fixa.
_PADRAO_SEVERIDADE = re.compile(r"gravidade", re.IGNORECASE)
_PADRAO_FALHA = re.compile(r"deu errado|descreve", re.IGNORECASE)
_PADRAO_SUGESTAO = re.compile(r"diferente", re.IGNORECASE)
_PADRAO_CODIGO = re.compile(r"c[óo]digo", re.IGNORECASE)

#: As perguntas de caracterizacao entraram no formulario em 10/10/2026, quando a ficha
#: de papel foi dissolvida nele. Sao detectadas pelo enunciado para irem ao perfil da
#: amostra, e precisam ficar FORA da varredura das heuristicas: "Como tu fazes a
#: recomendacao hoje?" nao e nota de severidade nem relato de falha.
_PADRAO_PERFIL = re.compile(
    r"forma[çc][ãa]o|h[áa] quanto tempo|recomenda[çc][ãa]o hoje|conforto|como tu usaste",
    re.IGNORECASE,
)


class ErroConsolidacao(Exception):
    """CSV que não tem a forma que o instrumento produz."""


def _colunas_por_heuristica(cabecalho: List[str]) -> Dict[int, Dict[str, str]]:
    """Mapeia cada heurística às suas três colunas, pela ordem em que aparecem.

    O Forms exporta as colunas na ordem das seções, então a n-ésima coluna de severidade é
    a da n-ésima heurística. Casar por número no enunciado seria mais robusto, mas o
    instrumento não numera as perguntas — e pedir que numere para agradar ao script seria
    deixar a ferramenta mandar no método.
    """
    heuristicas = [c for c in cabecalho if not _PADRAO_PERFIL.search(c)]
    severidade = [c for c in heuristicas if _PADRAO_SEVERIDADE.search(c)]
    falha = [c for c in heuristicas if _PADRAO_FALHA.search(c)]
    sugestao = [c for c in heuristicas if _PADRAO_SUGESTAO.search(c)]

    if len(severidade) != len(HEURISTICAS):
        raise ErroConsolidacao(
            f"esperava {len(HEURISTICAS)} colunas de severidade (uma por heurística) e "
            f"encontrei {len(severidade)}. Confira se o formulário exportado é o de "
            f"trabalho_de_conclusao/usabilidade/questionario.md e se todas as seções foram "
            f"respondidas ao menos uma vez"
        )

    mapa: Dict[int, Dict[str, str]] = {}
    for i, (numero, _rotulo) in enumerate(HEURISTICAS):
        mapa[numero] = {
            "severidade": severidade[i],
            "falha": falha[i] if i < len(falha) else "",
            "sugestao": sugestao[i] if i < len(sugestao) else "",
        }
    return mapa


def colunas_de_perfil(cabecalho: List[str]) -> List[str]:
    """As perguntas de caracterizacao do participante (Secao 1 do formulario).

    Entraram no formulario quando a ficha de papel foi dissolvida nele, em 10/10/2026.
    Servem para descrever a amostra na monografia: severidade alta vinda de quem usa
    ferramenta digital todo dia significa coisa diferente da mesma nota vinda de quem
    nunca usou.
    """
    return [c for c in cabecalho if _PADRAO_PERFIL.search(c)]


def _coluna_do_codigo(cabecalho: List[str]) -> Optional[str]:
    for coluna in cabecalho:
        if _PADRAO_CODIGO.search(coluna):
            return coluna
    return None


def _nota(valor: str) -> Optional[int]:
    """A nota quando ela é um inteiro de 0 a 4; None quando a pergunta ficou em branco.

    Em branco não vira zero: zero é "não é um problema", uma afirmação, e resposta ausente
    é ausência de afirmação. Confundir os dois puxaria toda média para baixo.
    """
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        nota = int(float(texto.replace(",", ".")))
    except ValueError:
        return None
    return nota if 0 <= nota <= 4 else None


def carregar(caminho: Path) -> List[Dict[str, str]]:
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    if not linhas:
        raise ErroConsolidacao(f"{caminho}: nenhuma resposta no arquivo")
    return linhas


def consolidar(linhas: List[Dict[str, str]]) -> Dict[str, Any]:
    cabecalho = list(linhas[0].keys())
    colunas = _colunas_por_heuristica(cabecalho)
    coluna_codigo = _coluna_do_codigo(cabecalho)

    resultado = []
    for numero, rotulo in HEURISTICAS:
        col = colunas[numero]
        notas: List[int] = []
        relatos: List[Dict[str, str]] = []

        for i, linha in enumerate(linhas, start=1):
            codigo = (linha.get(coluna_codigo) or "").strip() if coluna_codigo else ""
            codigo = codigo or f"(resposta {i})"

            nota = _nota(linha.get(col["severidade"], ""))
            if nota is not None:
                notas.append(nota)

            falha = (linha.get(col["falha"], "") or "").strip() if col["falha"] else ""
            sugestao = (linha.get(col["sugestao"], "") or "").strip() if col["sugestao"] else ""
            if falha or sugestao:
                relatos.append({
                    "codigo": codigo,
                    "nota": "—" if nota is None else str(nota),
                    "falha": falha,
                    "sugestao": sugestao,
                })

        resultado.append({
            "numero": numero,
            "rotulo": rotulo,
            "n": len(notas),
            "media": statistics.mean(notas) if notas else None,
            "mediana": statistics.median(notas) if notas else None,
            "minimo": min(notas) if notas else None,
            "maximo": max(notas) if notas else None,
            "notas": notas,
            "relatos": relatos,
        })

    return {"heuristicas": resultado, "respondentes": len(linhas)}


def _num(valor: Optional[float], casas: int = 2) -> str:
    """Número no padrão brasileiro, como o resto do sistema."""
    if valor is None:
        return "—"
    return f"{valor:.{casas}f}".replace(".", ",")


def relatorio_markdown(dados: Dict[str, Any]) -> str:
    linhas = [
        "# Consolidação do questionário de usabilidade",
        "",
        f"Respondentes: **{dados['respondentes']}**. Severidade de 0 (não é problema) a "
        "4 (catástrofe).",
        "",
        "> Estatística **descritiva**. A amostra é pequena e por conveniência: não há "
        "inferência, intervalo de confiança nem teste de hipótese. A escala de Nielsen é "
        "atribuída aqui a heurísticas, por usuários, e não a problemas, por especialistas "
        "— o que ela mede é percepção de gravidade. Ver `trabalho_de_conclusao/usabilidade/protocolo.md`, §2 e §3.",
        "",
        "## Severidade por heurística",
        "",
        "| # | Heurística | Média | Mediana | Mín | Máx | n |",
        "|---|---|---|---|---|---|---|",
    ]
    for h in dados["heuristicas"]:
        linhas.append(
            f"| {h['numero']} | {h['rotulo']} | {_num(h['media'])} | "
            f"{_num(h['mediana'], 1)} | {h['minimo'] if h['minimo'] is not None else '—'} | "
            f"{h['maximo'] if h['maximo'] is not None else '—'} | {h['n']} |"
        )

    com_media = [h for h in dados["heuristicas"] if h["media"] is not None]
    ordenadas = sorted(com_media, key=lambda h: (-h["media"], h["numero"]))

    linhas += [
        "",
        "## Prioridade de correção",
        "",
        "Da maior para a menor severidade média. A mediana está ao lado porque, com esta "
        "quantidade de respostas, um avaliador severo desloca a média — quando os dois "
        "números divergem muito, a média está sendo puxada por uma resposta só.",
        "",
        "| Ordem | Heurística | Média | Mediana |",
        "|---|---|---|---|",
    ]
    for posicao, h in enumerate(ordenadas, start=1):
        linhas.append(
            f"| {posicao}º | {h['numero']}. {h['rotulo']} | {_num(h['media'])} | "
            f"{_num(h['mediana'], 1)} |"
        )

    linhas += ["", "## Relatos", ""]
    algum = False
    for h in dados["heuristicas"]:
        if not h["relatos"]:
            continue
        algum = True
        linhas += [f"### {h['numero']}. {h['rotulo']}", ""]
        for r in h["relatos"]:
            linhas.append(f"**{r['codigo']}** (nota {r['nota']})")
            if r["falha"]:
                linhas.append(f"- *Falha:* {r['falha']}")
            if r["sugestao"]:
                linhas.append(f"- *Sugestão:* {r['sugestao']}")
            linhas.append("")
    if not algum:
        linhas.append("Nenhum relato em texto foi registrado.")

    return "\n".join(linhas) + "\n"


def escrever_csv(dados: Dict[str, Any], caminho: Path) -> None:
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["numero", "heuristica", "media", "mediana", "minimo", "maximo", "n"])
        for h in dados["heuristicas"]:
            escritor.writerow([
                h["numero"], h["rotulo"],
                "" if h["media"] is None else f"{h['media']:.4f}",
                "" if h["mediana"] is None else f"{h['mediana']:.4f}",
                h["minimo"] if h["minimo"] is not None else "",
                h["maximo"] if h["maximo"] is not None else "",
                h["n"],
            ])


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Consolida as respostas do questionário das dez heurísticas."
    )
    parser.add_argument("csv", type=Path, help="CSV exportado do Google Forms")
    parser.add_argument(
        "--saida", type=Path, default=None,
        help="diretório onde gravar heuristicas.md e heuristicas.csv "
             "(sem ele, imprime na tela)",
    )
    args = parser.parse_args(argv)

    try:
        dados = consolidar(carregar(args.csv))
    except (ErroConsolidacao, FileNotFoundError) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1

    relatorio = relatorio_markdown(dados)

    if args.saida is None:
        print(relatorio)
        return 0

    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "heuristicas.md").write_text(relatorio, encoding="utf-8")
    escrever_csv(dados, args.saida / "heuristicas.csv")
    print(f"gravado em {args.saida / 'heuristicas.md'} e {args.saida / 'heuristicas.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
