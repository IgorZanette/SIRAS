# Base de conhecimento — formato dos arquivos

Todo arquivo em `dados/` é **dado**, nunca código. A regra é que atualizar o Manual não deve exigir
tocar em nenhum arquivo `.py`.

## Regras gerais

- Codificação UTF-8, indentação de 2 espaços, chaves em `snake_case` sem acento.
- Todo arquivo tem um bloco `fonte` com manual, tabela, página e datas de transcrição e conferência.
- Valor ainda não transcrito: `null` ou `"PREENCHER"`. **Nunca** um valor aproximado.
- Todo arquivo transcrito ganha uma linha em `docs/mapa_manual.md` **no momento da transcrição**.

## Arquivos comuns (`dados/comum/`)

| Arquivo | Origem | Estado |
|---|---|---|
| `calagem_smp.json` | Tabela 5.2, p. 70 + ajustes das p. 71–72, 83 e 298 | transcrito e conferido |
| `ph_referencia.json` | Tabela 5.1, p. 68 | transcrito e conferido |
| `criterios_calagem.json` | Tabelas 5.3 (p. 75), 5.5 (p. 81), 5.6 (p. 83), 5.7 (p. 86) | transcrito e conferido |
| `mapa_culturas.json` | Resolução cultura → critério de calagem (não é tabela do Manual) | 21 culturas de grãos + macieira + erva-mate |
| `interpretacao_p.json` | Tabelas 6.2–6.6, p. 93–94 — classes de P por classe de argila | transcrito e conferido |
| `interpretacao_k.json` | Tabelas 6.7–6.10, p. 95–96 — classes de K por CTC pH 7,0 | transcrito e conferido |
| `interpretacao_geral.json` | Tabelas 6.1, 6.11, 6.12, p. 91/97/98 — MO, CTC, argila, Ca, Mg, S, micronutrientes | transcrito e conferido |
| `corretivos.json` | Cap. 8 — PRNT, tipos de calcário | pendente |

### Arquivos por grupo de cultura (`dados/culturas/<grupo>/`)

Tabelas compartilhadas por todas as culturas de um grupo (não uma por cultura individual):

| Arquivo | Origem | Estado |
|---|---|---|
| `dados/culturas/graos/graos_adubacao_n.json` | Tabelas 6.1.2–6.1.22, p. 116–133 — N por cultura e faixa de MO | transcrito e conferido |
| `dados/culturas/graos/graos_adubacao_pk.json` | Tabelas 6.1.1–6.1.4, p. 105–108 — correção, manutenção e exportação de P/K | transcrito e conferido |
| `dados/culturas/hortalicas/hortalicas_adubacao.json` | Cap. 6.3, p. 161–181 — N/P/K das 18 hortaliças | transcrito e conferido |
| `dados/culturas/tuberculos/tuberculos_adubacao.json` | Cap. 6.4, p. 184–185 — N/P/K de batata e batata-doce | transcrito e conferido |
| `dados/culturas/outras/outras_comerciais_adubacao.json` | Cap. 6.9, p. 280–283 — N/P/K de cana-de-açúcar e tabaco | transcrito e conferido |
| `dados/culturas/frutiferas/frutiferas_adubacao.json` | Cap. 6.5, p. 190–231 — N/P/K das 17 frutíferas, em 3 fases | transcrito e conferido |
| `dados/culturas/erva_mate/erva_mate_adubacao.json` | Seção 6.6.5, p. 239–244 — programas desde o plantio e de recuperação | transcrito e conferido |

Ver `docs/CONFERENCIA_S3.md` e `docs/CONFERENCIA_S4.md` para o roteiro de conferência página a
página desses arquivos, e `docs/NOTA_EXTRACAO_PDF.md` para o problema de extração do símbolo `≤`
que motivou o roteiro. Decisões de modelagem (doses em faixa/teto, variáveis condicionais, classes
de MO por referência) estão em `docs/decisoes/0004-normalizacao-de-doses-e-variaveis-condicionais.md`.

Os 5 arquivos de adubação por grupo (hortaliças, tubérculos, outras comerciais, frutíferas,
erva-mate) têm um bloco `checksum` (`culturas` + `soma_total`, soma de todos os valores
numéricos em `culturas`) conferido pelo autor e verificado a cada carga pelo carregador —
mesmo padrão de `calagem_smp.json` e dos arquivos de grãos. Uma alteração acidental em
qualquer dose, mesmo uma que não quebre a monotonicidade por classe de teor, faz o
carregador falhar.

## Nota de design — não há mais "um arquivo por cultura"

Uma versão anterior deste documento previa um arquivo por cultura
(`dados/culturas/<grupo>/<cultura>.json`, schemas `graos_v1`/`hortalicas_v1`/`frutifera_v1`/
`erva_mate_v1`/`outras_v1`, cada um com seu próprio campo `criterio_calagem`). Esse design
nunca chegou a ser implementado e foi abandonado em favor do padrão que está de fato em
produção — a tabela "Arquivos por grupo de cultura" acima: **um arquivo por grupo inteiro**,
com todas as culturas do grupo em `culturas.<id>` (o mesmo padrão já usado para calagem em
`criterios_calagem.json`, evitando duplicar tabela do Manual 21 ou 61 vezes).

A resolução cultura → critério de calagem vive em `dados/comum/mapa_culturas.json`, não num
campo dentro do arquivo da cultura — ver `siras/motor/calagem.py::resolver_criterio_id()`.

As chaves de classe de teor são sempre: `muito_baixo`, `baixo`, `medio`, `alto`, `muito_alto`
(`dados/culturas/<grupo>/*.json`, nó `classes_teor`).

## Validação

`scripts/valida_base.py` hoje valida apenas `dados/comum/` (via `carregar_dados_comum()`). Os
arquivos de `dados/culturas/<grupo>/` são validados por `Carregador.carregar_dados_graos()` /
`carregar_dados_hortalicas()` / `carregar_dados_tuberculos()` / `carregar_dados_outras()` /
`carregar_dados_frutiferas()` / `carregar_dados_erva_mate()`, exercitados pelos testes em
`testes/unidade/` — ainda não há um único comando que valide `dados/` inteiro de uma vez.
