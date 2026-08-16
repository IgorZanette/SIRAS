# ADR 0002 — Calagem dirigida por critério de grupo e políticas do motor

**Status:** aceito · **Data:** 2026-08-16

## Contexto

A leitura inicial da proposta assumia que a calagem seria calculada a partir do pH de referência da
cultura (Tabela 5.1) aplicado à tabela do índice SMP (Tabela 5.2).

A extração do Capítulo 5 do Manual mostrou que isso está incorreto. O pH de referência identifica a
exigência da espécie, mas a **condição de disparo** e o **pH alvo da dose** vêm das Tabelas 5.3 a
5.7, organizadas por grupo de cultura e sistema de manejo, e frequentemente divergem do pH de
referência:

- grãos: pH de referência 6,0, disparo em pH < 5,5, dose para pH 6,0;
- aspargo: pH de referência 6,5, disparo em pH < 6,0, dose para pH 6,5;
- plantio direto consolidado: fator de 1/4 sobre a dose, aplicação superficial limitada a 5 t/ha;
- erva-mate e florestais: sem pH de referência, critério por saturação por bases (V ≤ 40%).

## Decisão principal

`dados/comum/criterios_calagem.json` é a tabela que dirige o módulo de calagem. A cadeia é
`cultura + sistema + condição da área -> critério -> (disparo, pH alvo, fator) -> Tabela 5.2`.

`ph_referencia.json` permanece na base para exibição no laudo e para a regra de rotação de culturas
(usar o pH de referência da cultura mais sensível), mas **não** dispara a calagem.

## Consequências

- O sistema de manejo (convencional / plantio direto e sua condição) passa a ser entrada obrigatória
  do formulário, não opcional.
- A Seção 3.1.2 da proposta precisa ser corrigida: hoje descreve o método da saturação por bases,
  que o Manual traz apenas como alternativa, e não menciona o índice SMP.

---

# Políticas do motor

As três decisões abaixo não estão no Manual — são escolhas de implementação que o Manual não
determina. Precisam estar registradas porque afetam diretamente a comparação com os valores de
referência na validação (Seção 4.4 da proposta) e podem ser questionadas em banca.

## D1 — Política de arredondamento

**Decisão:**

| Saída | Precisão | Regra |
|---|---|---|
| Necessidade de calcário | 1 casa decimal, em t/ha | meio para cima |
| Doses de N, P₂O₅ e K₂O | número inteiro, em kg/ha | meio para cima |

**O arredondamento ocorre apenas na saída final.** Todos os passos intermediários — fator do
critério (1, ½, ¼), ajuste por PRNT, fator de 30 cm, limite de 5 t/ha — são calculados em precisão
plena. Arredondar a cada etapa acumularia erro e produziria divergências artificiais contra o
oráculo.

**Justificativa:** a Tabela 5.2 do Manual publica as doses com uma casa decimal; adotar a mesma
precisão na saída mantém coerência com a fonte. O arredondamento meio para cima é o convencional em
recomendação agronômica e é conservador — na dúvida, aplica-se ligeiramente mais corretivo, o que é
preferível a subcorrigir.

**Armadilha de implementação:** `round()` do Python usa *banker's rounding* — `round(0.25, 1)`
devolve `0.2`, não `0.3`. Isso quebraria casos de teste de forma silenciosa e difícil de rastrear.
Usar explicitamente:

```python
from decimal import Decimal, ROUND_HALF_UP

def arredondar(valor: float, casas: int) -> float:
    """Arredonda meio-para-cima. round() nativo usa banker's rounding e nao serve aqui."""
    exp = Decimal(1).scaleb(-casas)               # 0.1 para casas=1, 1 para casas=0
    return float(Decimal(str(valor)).quantize(exp, rounding=ROUND_HALF_UP))
```

**Reflexo na validação:** a tolerância dos casos de teste é ±0,05 t/ha para calcário e ±1 kg/ha para
nutrientes — margem que absorve apenas o arredondamento, não divergência de critério.

## D2 — Índice SMP fora da faixa da tabela

A Tabela 5.2 cobre de `≤ 4,4` a `7,1`. **Decisão, por faixa:**

| Faixa do SMP informado | Comportamento |
|---|---|
| < 4,4 | Usa a linha `≤ 4,4`. A tabela é aberta à esquerda por construção, então isso é leitura correta, não extrapolação. Registra passo no trace informando que o valor foi tratado pelo limite inferior. |
| 4,4 a 7,1 | Consulta direta. |
| > 7,1 | Dose 0, com justificativa no trace. Não é erro: a própria tabela já indica 0 em 7,1 para os três pH alvo. |
| fora do domínio físico plausível (< 3,0 ou > 8,0), ausente ou não numérico | **Erro de validação de entrada**, levantado em `siras/dominio/`, antes do motor. Mensagem indicando o campo e a faixa aceita. |

**Justificativa:** a distinção entre *fora da tabela* e *fora do domínio* separa dois problemas
diferentes. O primeiro é uma condição de contorno legítima e o sistema deve responder; o segundo é
erro de digitação do usuário e deve ser recusado na entrada, nunca processado silenciosamente.
Extrapolar a tabela produziria um número plausível e sem respaldo no Manual — exatamente o que a
ferramenta existe para evitar.

**Caso relacionado — baixo poder tampão:** SMP > 6,3 **não** é fora da faixa. O Manual (p. 71–72)
alerta que nesses solos o índice subestima a acidez potencial e recomenda as equações polinomiais
com MO e Al. Decisão:

- se MO e Al estiverem disponíveis, o valor recomendado é o da **equação polinomial**;
- o valor da tabela é calculado assim mesmo e exibido no trace, para o técnico ver a diferença;
- se MO ou Al faltarem, usa-se a tabela com **alerta explícito no laudo** de que o solo está na
  faixa em que o Manual recomenda o método alternativo.

## D3 — Ausência de necessidade de calagem

**Decisão:** quando o critério não dispara, o motor retorna um resultado estruturado com
`nc_t_ha = 0.0` e um **motivo enumerado** — nunca `None`, nunca resultado vazio, nunca exceção.

Motivos possíveis:

| Código | Situação | Fonte |
|---|---|---|
| `ph_acima_do_disparo` | pH do solo ≥ limite de disparo do critério | Tabelas 5.3 a 5.7 |
| `excecao_v_e_al` | PD consolidado com V ≥ 65% e saturação por Al < 10% | Tab. 5.3, nota (1) |
| `ca_mg_suficientes` | Critério por saturação por bases, mas Ca ≥ 4,0 e Mg ≥ 1,0 | Tab. 5.5(3), 5.6(2), 5.7(1) |
| `v_acima_do_alvo` | Critério por saturação por bases com V > 40% | Tab. 5.6 |
| `smp_acima_da_tabela` | SMP > 7,1 | Tab. 5.2 |

O laudo exibe "Não há necessidade de calagem", seguido da justificativa e da referência à tabela do
Manual.

**Justificativa:** "não precisa calcariar" é uma resposta técnica tão válida quanto uma dose, e é
frequentemente a mais valiosa em termos econômicos — evita gasto desnecessário, que é uma das
motivações declaradas do trabalho (Seção 2.1). Uma saída vazia obrigaria o usuário a inferir se o
sistema decidiu que não precisa ou se falhou. Registrar o motivo enumerado também torna essa
situação testável: os casos de teste podem verificar não só a dose 0, mas **por qual regra** ela foi
zero — o que pega o erro de "acertou pelo motivo errado".

**Comportamento relacionado — limite de 5 t/ha:** quando o critério é de aplicação superficial e a
dose calculada excede 5 t/ha (PRNT 100%), a dose é truncada em 5 t/ha e o trace registra o valor
original e o truncamento. O laudo informa que houve limitação, para o técnico avaliar se cabe
reiniciar o sistema com incorporação.

---

## Nota de organização

Se preferir separar responsabilidades entre ADRs, as três políticas acima podem ser movidas para um
`0003-politicas-do-motor.md`, mantendo em 0002 apenas a decisão sobre o critério de grupo. Estão
juntas aqui por conveniência, já que todas decorrem da mesma leitura do Capítulo 5.
