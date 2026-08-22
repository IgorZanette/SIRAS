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
- Formato em `testes/casos/casos_recomendacao.json` e `casos_aptidao.json`.

Cada caso registra `origem_referencia` — quem calculou, quando, e se foi conferido com o orientador.
É esse campo que separa "eu testei" de "eu validei".

## Risco de circularidade — ATENÇÃO

O sistema é construído a partir do Manual; se a referência também for o Manual aplicado pelo próprio
autor, o teste mede apenas se a implementação corresponde à transcrição.

- **H1.1:** mitigado por casos adicionais vindos de laudos reais anonimizados, com recomendação
  elaborada por profissional habilitado.
- **H1.2:** risco maior e ainda **não resolvido**. As faixas de aptidão são definidas pelo autor; se
  o oráculo derivar dessas mesmas faixas, a concordância é 100% por construção e o teste não mede
  nada. Encaminhamento necessário — ver `docs/ROADMAP.md`, pendência P1:
  1. faixas construídas a partir de fonte **independente** do Manual; e
  2. subconjunto de casos classificado às cegas por um agrônomo.

## Análise dos resultados

O sistema é determinístico: execuções repetidas produzem a mesma saída, logo não há teste de
comparação de médias. Apura-se a proporção de casos concordantes, global e por grupo, com
**intervalo de confiança de 95% pelo método de Wilson** (mais adequado que o intervalo normal para
n pequeno e proporções altas).

Casos discordantes são analisados individualmente, com o `Trace` de cada um, distinguindo erros de
implementação de divergências de interpretação dos critérios.

`scripts/gera_tabela_concordancia.py` produz, em um comando: taxa global e por grupo, IC 95%, lista
de discordantes com o trace, e saída em Markdown e CSV para a monografia.

## Comparação com ferramenta existente

Subconjunto dos casos submetido ao FertFacil (ou AdubaTec), no que houver sobreposição de
funcionalidade. Natureza qualitativa: evidenciar convergências, divergências e as funcionalidades
que o SIRAS oferece e as demais não — em especial a aptidão edáfica integrada.

## Usabilidade

Roteiro de tarefas (selecionar cultura, informar análise, interpretar o laudo) com 5 a 10
participantes do público-alvo, seguido do questionário **SUS**.

- Escala: Brooke (1996).
- Referência de 68 como média: **Bangor, Kortum & Miller (2008)** e **Sauro (2011)** — *não* é de
  Brooke (1996); a proposta precisa dessa correção.
- Confirmado com o orientador (Rafael Rieder) que a avaliação de usabilidade não requer submissão
  ao comitê de ética (CEP). Será aplicado TCLE aos participantes.
