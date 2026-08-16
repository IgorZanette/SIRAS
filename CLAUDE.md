# CLAUDE.md — SIRAS

Instruções permanentes para o Claude Code neste repositório. Leia antes de qualquer tarefa.

## Contexto

SIRAS — sistema especialista baseado em regras para interpretação de análises de solo, recomendação
de calagem e adubação e estimativa de aptidão edáfica. Trabalho de Conclusão de Curso em Ciência da
Computação (UPF, 2026), autor Igor Zanette.

**Fonte técnica única das recomendações:** Manual de Calagem e Adubação para os estados do RS e SC,
CQFS-RS/SC, 11ª edição, 2016. Escopo: 61 culturas e grupos de culturas (ver `docs/ROADMAP.md`).

---

## REGRA ABSOLUTA — dados agronômicos

**Nunca preencha, infira, estime, complete ou "corrija" valores numéricos das tabelas do Manual.**

Isso inclui doses de N, P2O5 e K2O; necessidade de calcário; pH de referência; limites de classes de
interpretação; faixas de expectativa de rendimento; qualquer número agronômico.

Esses valores são transcritos manualmente pelo autor a partir do PDF do Manual. São dados de
pesquisa de um TCC — inventá-los é fabricação de dados.

Se um valor faltar: use `null` ou `"PREENCHER"`, avise explicitamente que o campo depende do Manual,
e **não** proponha um valor "provável" ou "típico", nem em comentário, nem como exemplo.

O mesmo vale para o campo `referencia` dos arquivos em `testes/casos/`: é o oráculo da validação e é
calculado à mão pelo autor. Você pode criar a estrutura do arquivo; nunca o conteúdo desse campo.

**Nunca altere arquivos em `dados/` para fazer validação, schema ou teste passar.** Os dados são
transcrição conferida do Manual e são a fonte da verdade. Quando um schema ou teste conflitar com os
dados, o schema ou o teste é que está errado. Se você acreditar que o dado está incorreto, avise e
pare — não corrija.

| Você (Claude) faz | O autor faz |
|---|---|
| Estrutura de código, arquitetura, refatoração | Transcrever tabelas do Manual para JSON |
| Motor de inferência, rotas Flask, templates | Definir os valores de referência dos testes |
| JSON Schema e validadores | Conferir a base de conhecimento contra o Manual |
| Estrutura dos testes, documentação | Decidir escopo e critérios agronômicos |

---

## Stack e restrições

- **Python 3.12+**, **Flask 3.x**, HTML e CSS. Desenvolvimento em Windows.
- Base de conhecimento em **JSON**, carregada em tempo de execução.
- **Sem** bibliotecas externas de inferência (Experta, PyKE): o motor é Python puro e auditável.
  Decisão metodológica declarada na proposta — ver `docs/decisoes/0001`.
- Dependências permitidas: `flask`, `jsonschema`, `pytest`. Antes de sugerir outra, pergunte.
- **Sem** banco de dados, autenticação ou chamadas de rede. Roda em `localhost`, offline.

## Convenções de código

- Nomes de domínio em português (`analise`, `calagem`, `adubacao`, `aptidao`, `cultura`); termos de
  programação em inglês quando for convenção (`load`, `get`, `test`).
- **Sempre** `open(caminho, encoding="utf-8")` — o padrão do Windows é cp1252 e quebra acentuação.
- **Sempre** `pathlib.Path`; nunca concatenação manual de caminhos.
- `siras/motor/` e `siras/dominio/` **não importam Flask**. O núcleo roda isolado, por linha de
  comando.
- Ponto de entrada único do motor:
  `gerar_laudo(analise: AnaliseSolo, cultura_id: str, contexto: Contexto) -> Laudo` — função pura e
  determinística.
- Toda decisão do motor registra um passo no `Trace` (`siras/motor/trace.py`). Sem exceção.
- Comente regras agronômicas citando a fonte:
  `# R-CAL-03: PD consolidado -> 1/4 SMP para pH 6,0 (Manual 2016, Tab. 5.3, p. 75)`

## Regras agronômicas já fixadas (não contrarie)

Extraídas e conferidas do Manual. Detalhes em `dados/comum/` e `docs/mapa_manual.md`.

- A necessidade de calcário é **preferencialmente** estimada pelo **índice SMP** (Tabela 5.2, p. 70),
  que dá a dose de calcário PRNT 100% para elevar o pH da camada 0–20 cm a 5,5 / 6,0 / 6,5. O método
  da saturação por bases existe como alternativa (p. 71), mas **primeira calagem usa SMP**.
- Faixa da tabela SMP: `<=4,4` a `7,1`, passo 0,1. Fora da faixa: erro de validação, nunca
  extrapolação silenciosa.
- Correção pelo corretivo real: `dose = NC_tabela * 100 / PRNT` (Cap. 8, p. 298).
- **O pH de referência (Tabela 5.1) NÃO dispara a calagem.** O disparo e o pH alvo vêm das Tabelas
  5.3 a 5.7, por grupo de cultura, e frequentemente divergem do pH de referência. Exemplo: grãos têm
  pH de referência 6,0 mas só recebem calcário quando pH < 5,5, com dose para pH 6,0.
  Ver `dados/comum/criterios_calagem.json` — é essa a tabela que dirige o módulo de calagem.
- Plantio direto consolidado: dose = **1/4** do SMP para pH 6,0, superficial, limitada a 5 t/ha.
- Solos de baixo poder tampão (SMP > 6,3): usar as equações polinomiais com MO e Al em vez da tabela
  (ver `calagem_smp.json`, campo `ajustes.baixo_poder_tampao`).
- Erva-mate: sem pH de referência (grupo das espécies florestais, Tabela 5.6). Calagem só se
  V < 40%, pela fórmula `NC = ((40 - V)/100) * CTC_pH7`, exceto se Ca >= 4,0 e Mg >= 1,0.
- Cana-de-açúcar e tabaco: pH de referência 6,0, calagem quando pH < 5,5, dose para pH 6,0.
- Leguminosas (soja, ervilhaca, tremoço) não recebem adubação nitrogenada — fixação biológica.
- Interpretação de **fósforo** depende da classe de **teor de argila**; a de **potássio**, da
  **CTC a pH 7,0**.

## Fluxo de trabalho esperado

1. Antes de escrever código, **apresente o plano** (arquivos a criar ou alterar) e aguarde aprovação.
2. Uma tarefa por vez. Não amplie o escopo do que foi pedido.
3. Ao terminar, rode `pytest` e informe o resultado.
4. Explique decisões de design não óbvias — o autor precisa entender e defender cada linha na banca.
5. Não crie arquivos auxiliares, README ou documentação sem pedido.
6. Ao concluir uma etapa do `docs/ROADMAP.md`, atualize o estado dela no arquivo.

## Convenções de commit

- Formato: `tipo: descrição no imperativo` — tipos `feat`, `fix`, `docs`, `test`, `refactor`,
  `chore`, `dados` (transcrição da base de conhecimento).
- Assunto em português, até 72 caracteres.
- **Não adicione linhas de atribuição nos commits** — nem `Co-Authored-By`, nem
  `Generated with Claude Code`, nem em mensagens de commit, nem em descrições de PR. O uso de IA
  está declarado no `README.md`; a mensagem de commit fica limpa.
- Nunca commite `_local/`, `.venv/` ou `.claude/settings.local.json`.
- Não faça `git push` sem pedido explícito.

## Glossário

- **SMP** — índice tampão de Shoemaker–McLean–Pratt, base do cálculo de calagem no RS/SC
- **PRNT** — poder relativo de neutralização total do corretivo (%)
- **NC** — necessidade de calcário (t/ha)
- **CTC** — capacidade de troca de cátions a pH 7,0 (cmolc/dm³)
- **MO** — matéria orgânica (%)
- **V%** — saturação por bases
- **PD** — plantio direto
- **Aptidão edáfica** — neste trabalho, aptidão restrita a atributos químicos e físicos do solo,
  sem relevo e sem clima
