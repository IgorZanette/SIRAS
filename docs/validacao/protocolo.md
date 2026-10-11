# Protocolo de validação

Corresponde à Seção 4.4 da proposta. A validação tem três dimensões: correção das saídas,
comparação com ferramenta existente e usabilidade.

## Hipóteses

- **H1.1** — o SIRAS gera recomendações de calagem e adubação com concordância >= 80% em relação a
  valores de referência derivados do Manual.
- **H1.2** — o SIRAS estima a aptidão edáfica com concordância >= 80% em relação a uma classificação
  de referência.

## Definições operacionais

**Concordância de recomendação:** um caso é concordante quando *todas* as saídas — necessidade de
calagem (t/ha) e doses de N, P2O5 e K2O (kg/ha) — coincidem com a referência, admitida apenas
tolerância de arredondamento.

**Política de arredondamento** (declarar também na monografia):

- calcário: 1 casa decimal, em t/ha;
- doses de nutrientes: número inteiro, em kg/ha;
- arredondamento de meio para cima.

**Concordância de aptidão:** a classe atribuída pelo SIRAS coincide com a classe de referência.

## Conjunto de casos

- Mínimo de 40 casos; **alvo de 60 a 80**, estratificados entre os seis grupos de culturas.
- Cobrir todas as classes de interpretação (muito baixo a muito alto), diferentes CTCs e texturas, e
  os casos especiais: plantio direto consolidado, baixo poder tampão (SMP > 6,3), frutíferas por
  fase, erva-mate e tabaco por tipo.
- Formato em `testes/casos/casos_recomendacao.json` e, para a aptidão, `entradas_aptidao.json` + `gabarito_aptidao.csv`.

Cada caso registra `origem_referencia` — quem calculou, quando, e se foi conferido com o orientador.
É esse campo que separa "eu testei" de "eu validei".

## Risco de circularidade — ATENÇÃO

O sistema é construído a partir do Manual; se a referência também for o Manual aplicado pelo próprio
autor, o teste mede apenas se a implementação corresponde à transcrição.

- **H1.1:** mitigado por casos adicionais vindos de laudos reais anonimizados, com recomendação
  elaborada por profissional habilitado.
- **H1.2:** risco maior e ainda **não resolvido**. As faixas de aptidão são definidas pelo autor; se
  o oráculo derivar dessas mesmas faixas, a concordância é 100% por construção e o teste não mede
  nada. Encaminhamento necessário — ver `docs/processo/roadmap.md`, pendência P1:
  1. faixas construídas a partir de fonte **independente** do Manual; e
  2. subconjunto de casos classificado às cegas por um agrônomo.

## Convergência entre transcrições — o que ela prova e o que não prova

Os grupos de exigência de P e K de cada cultura foram transcritos do Manual três vezes, em
momentos distintos e por caminhos distintos: nos arquivos de adubação por grupo (agosto de
2026, campo `grupo_exigencia`), nas listas `culturas` de `interpretacao_p.json` e
`interpretacao_k.json` (setembro de 2026) e no catálogo completo do Anexo 2
(`dados/comum/catalogo_anexo2.json`, 141 culturas, 10/09/2026). As três concordam
integralmente — zero divergências —, e `testes/unidade/test_integridade_catalogo_anexo2.py`
mantém essa concordância travada: qualquer edição futura que desalinhe as três quebra a suíte.

**A distinção precisa ser explícita no texto da monografia:** isso é evidência de *correção da
transcrição*, não de correção agronômica dos critérios. Prova que o dado que está no sistema é
o dado que está no Manual; não prova que o critério do Manual seja o adequado, nem que a
interpretação que o SIRAS faz dele produza a recomendação certa. Escrever sem essa ressalva
transformaria um controle de qualidade de transcrição em alegação de validação agronômica, que
é coisa maior e depende do conjunto de casos com oráculo e da auditoria do agrônomo.

O mesmo vale para a validação cruzada contra os cabeçalhos das Tabelas 6.2 e 6.7, que nomeiam
exaustivamente os Grupos 1 e 4: é uma checagem interna ao Manual, feita sem sair dele.

## Análise dos resultados

O sistema é determinístico: execuções repetidas produzem a mesma saída, logo não há teste de
comparação de médias. Apura-se a proporção de casos concordantes, global e por grupo, com
**intervalo de confiança de 95% pelo método de Wilson** (mais adequado que o intervalo normal para
n pequeno e proporções altas).

Casos discordantes são analisados individualmente, com o `Trace` de cada um, distinguindo erros de
implementação de divergências de interpretação dos critérios.

`scripts/gera_tabela_concordancia.py` produz, em um comando: taxa global e por grupo, IC 95%, lista
de discordantes com o trace, e saída em Markdown e CSV para a monografia. A apuração vive em
`siras/validacao/concordancia.py` e é exercitada por `testes/unidade/test_concordancia.py` — o
número publicado sai do mesmo código que a suíte roda.

**Medido em 10/10/2026, de manhã — um problema de tamanho de amostra, não de acerto:** 15/15 casos
concordantes, 100%, com IC 95% de Wilson **[79,6%; 100,0%]**. O limite inferior ficava **abaixo dos
80%** que a H1.1 declara. Não era o motor que falhava — era o n.

**Reaberto no mesmo dia, com dez casos novos (ADU-20 a ADU-28 e CAL-12):** 25/25 concordantes,
100%, IC 95% **[86,7%; 100,0%]**. O limite inferior passa o limiar e a hipótese se sustenta pelo
critério declarado. Dos dez casos, **dois corrigiram o motor** — ver
[ADR 0010](../decisoes/0010-adicional-de-n-por-rendimento-e-reposicao-em-muito-alto.md).

Duas coisas precisam ir ao texto junto com esse número, e não depois dele:

1. **O ganho não foi só de n.** Antes dos casos novos, três dos seis grupos de cultura
   (hortaliças, tubérculos, cana e tabaco) não tinham caso nenhum, e um único caso exercitava o
   algoritmo de adubação de grãos. O 100% sobre 15 casos media menos do que parecia.
2. **Os dez casos novos são um oráculo mais fraco.** A referência deles foi derivada das tabelas
   já transcritas em `dados/` e depois conferida pelo autor, enquanto a dos quinze antigos foi
   calculada à mão a partir do Manual impresso. Os novos provam o algoritmo; não provam a
   transcrição, porque partem dela. O campo `origem_referencia` de cada caso registra qual é
   qual, e [`como-calcular-oraculo.md`](como-calcular-oraculo.md) descreve o procedimento manual.

A conformidade da aptidão nunca teve esse problema: 88 casos, 100%, IC [95,8%; 100,0%].

## Comparação com ferramenta existente

Subconjunto dos casos submetido ao FertFacil (ou AdubaTec), no que houver sobreposição de
funcionalidade. Natureza qualitativa: evidenciar convergências, divergências e as funcionalidades
que o SIRAS oferece e as demais não — em especial a aptidão edáfica integrada.

## Usabilidade

**Protocolo completo em [`protocolo de usabilidade`](../usabilidade/protocolo.md).** Resumo do que mudou e por quê:

Decidido com o orientador em **24/09/2026**: sai o **SUS**, entram **três roteiros de teste com
usuários do público-alvo** e um **questionário pós-teste estruturado pelas dez heurísticas de
Nielsen**, com quatro perguntas abertas ao final. O SUS entrega um número; esta etapa precisa
entregar uma lista priorizada de correções, e é isso que as heurísticas dão.

- 5 a 8 participantes (mais 1 no piloto), em duas partes: sessão de roteiros (~35 min) e
  questionário respondido depois, no Google Forms.
- **Nomenclatura obrigatória no texto:** *teste de usabilidade com usuários, seguido de
  questionário pós-teste estruturado pelas dez heurísticas de Nielsen* — **nunca** "avaliação
  heurística", que no método de Nielsen e Molich (1990) é inspeção por especialistas em
  usabilidade, sem usuários e sem tarefas. Ver o protocolo, §2.
- A escala 0–4 é adaptação declarada: no método original a severidade é atribuída a **problemas**,
  por avaliadores; aqui é atribuída a **heurísticas**, por usuários, e mede percepção de gravidade.
- Estatística **descritiva**, sem inferência: amostra pequena e por conveniência.
- Confirmado com o orientador (Rafael Rieder) que a avaliação **não requer submissão ao CEP** e,
  em 10/10/2026, que **não exige termo assinado**: o participante usa o sistema e responde ao
  formulário. Um instrumento só, com a caracterização do participante na Seção 1 dele.
- A interface é congelada na tag `congelamento-v1` antes da primeira sessão e não muda até a última.

Consolidação por `scripts/consolidar_heuristicas.py`, análogo ao
`gera_tabela_concordancia.py` da dimensão de correção.

**A proposta foi corrigida em 24/09/2026** (§4.4.3, etapa (i) do método e linha (i) do
cronograma). Com o SUS fora do texto, deixou de existir também a atribuição errada do limiar de 68 —
que é de **Bangor, Kortum & Miller (2008)** e **Sauro (2011)**, e não de Brooke (1996). Seguem
pendentes na P3 o método de calagem (SMP) e a referência Ramalho Filho & Beek.
