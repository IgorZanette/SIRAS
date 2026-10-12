# 0010 — Adicional de N por rendimento e reposição na classe Muito alto

- **Status:** aceito
- **Data:** 2026-10-10
- **Contexto:** dez casos de teste novos (ADU-20 a ADU-28 e CAL-12), escritos pelo autor
  para cobrir os grupos que não tinham caso nenhum. Dois deles divergiram do motor, e nos
  dois a divergência era do motor, não do caso
- **Afeta:** `siras/motor/adubacao.py` (`calcular_nitrogenio`, `_dose_pk`,
  `calcular_fosforo_potassio`), `siras/motor/laudo.py`,
  `siras/validacao/concordancia.py`, `dados/culturas/graos/graos_adubacao_pk.json`
  (campo de texto, nenhum número)

## Como os dois erros apareceram

Até 10/10/2026 o conjunto de validação tinha 15 casos, e só **um** deles (ADU-01)
exercitava o algoritmo de adubação de grãos. Nove dos quinze eram de calagem. Os dois
defeitos descritos abaixo estavam no motor desde a implementação do Cap. 6 e atravessaram
toda a suíte — 2.494 na camada rápida, 5.206 na completa — sem que nada falhasse, porque
nenhum teste pedia a combinação de entradas que os revela.

Isso é o argumento central para a Seção de Resultados: a cobertura de 100% de
concordância sobre 15 casos não media o que parecia medir. Os dez casos novos custaram
duas correções no motor, e é esse o valor de um conjunto de validação construído por
lacuna de cobertura, e não por repetição do caminho fácil.

## D10.1 — A dose de N passa a reagir à expectativa de rendimento

**Achado (caso ADU-25).** `graos_adubacao_n.json` traz, em 16 das 21 culturas de grãos,
os campos `rendimento_referencia_t_ha` e `adicional_kg_n_por_t`. Nenhuma linha de código
os lia. Consequência: a dose de N era a mesma para qualquer expectativa de rendimento,
enquanto P e K reagiam normalmente — o milho com 6, 8 ou 12 t/ha recebia os mesmos
70 kg N/ha e 130, 160 e 220 kg P₂O₅/ha.

As cinco culturas que não declaram o adicional são todas leguminosas, de modelo
`nao_aplica`, que não recebem N por fixação biológica. Ou seja: o campo estava transcrito
em **todas** as culturas às quais ele se aplica, e em nenhuma era usado.

**Decisão.** `calcular_nitrogenio` recebe `expectativa_rendimento` e, quando ela supera
`rendimento_referencia_t_ha`, soma `(expectativa − referência) × adicional_kg_n_por_t`.
Expectativa **abaixo** da referência não desconta nada: o Manual publica um adicional,
não uma função linear em torno do rendimento de referência.

O retorno passa a trazer `adicional_kg_n_ha`, para que a trilha e o laudo mostrem a
parcela separada da dose tabelada, em vez de um total sem origem visível.

### D10.2 — Na faixa de MO acima de 5,0%, o teto não recebe adicional

Dezesseis culturas que declaram o adicional declaram também
`acima_de_5_0_e_maximo: true`. Nessa faixa o Manual publica a dose como **teto**, e não
como valor fixo. Somar o adicional passaria do que o teto admite.

**Decisão do autor:** nessa faixa não há adicional. O retorno marca `teto: True`, de modo
que a diferença fique registrada em vez de desaparecer num número.

Esta é a decisão mais frágil das duas, e vale dizer por quê: o Manual não trata
explicitamente da interação entre o teto da faixa de MO alta e o adicional por
rendimento. A escolha é do autor, pela leitura de que um teto é um teto. A alternativa
— somar e deixar o total ultrapassar o teto — foi rejeitada por contradizer o próprio
rótulo do campo.

## D10.3 — Em Muito alto, segundo cultivo, a dose é a reposição e não a manutenção

**Achado (caso ADU-27).** A linha `muito_alto.cultivo_2` de
`algoritmo_dose.regras` estava transcrita como:

> `"<= manutencao (reposicao, a criterio do tecnico)"`

A frase junta duas coisas diferentes numa só: o **teto** (que de fato existe) e a
**base** desse teto. O motor leu "manutenção" e devolvia a manutenção. O caso ADU-27 leu
"reposição" e esperava a exportação nos grãos.

A base do próprio repositório resolve a ambiguidade sem precisar voltar ao PDF:
`exportacao_nos_graos` (Tab. 6.1.3, p. 107) traz a nota transcrita

> `"Base da adubacao de reposicao, usada apenas em nivel Muito alto"`

— que diz, no singular, para que serve aquela tabela e em que classe. Não há outra classe
em que a reposição seja usada, e não há outra tabela de reposição.

**Decisão do autor:** vale a reposição. Em classe Muito alto e segundo cultivo,

```
dose = exportacao_nos_graos[nutriente] × expectativa_rendimento
```

mantido o qualificador `ate` do [ADR 0004](0004-normalizacao-de-doses-e-variaveis-condicionais.md)
(D4.1): o Manual autoriza até esse valor, a critério do técnico, e não o impõe. Para o
trigo a 3 t/ha, 30 kg P₂O₅/ha e 18 kg K₂O/ha, contra os 45 e 30 da manutenção que o motor
devolvia antes.

Quando a cultura não declara exportação, o motor levanta `ErroAdubacao` em vez de emitir
um teto vazio.

### A alteração em `dados/`

A frase ambígua foi reescrita para dizer uma coisa só:

```
"cultivo_2": "<= exportacao_nos_graos * rendimento (reposicao, a criterio do tecnico)"
```

É a única alteração em `dados/` desta decisão, é de texto, **nenhum número mudou**, e foi
autorizada explicitamente pelo autor. Fica registrada aqui porque o `CLAUDE.md` trata
`dados/` como fonte da verdade: a regra não foi flexibilizada, foi aplicada — o dado
estava ambíguo, o autor conferiu a p. 107 e decidiu qual das duas leituras vale.

## Consequências para a validação

| | Antes | Depois |
|---|---|---|
| Casos de recomendação | 15 | 25 |
| Grupos sem caso nenhum | hortaliças, tubérculos, outras | nenhum |
| Casos que exercitam a adubação de grãos | 1 | 5 |
| IC 95% de Wilson (limite inferior) | 79,6% | 86,7% |

O limite inferior passa a superar os 80% que a H1.1 declara — a **pendência P9 está
fechada**. `testes/unidade/test_concordancia.py::test_o_conjunto_atual_sustenta_a_H1_1`
guarda esse resultado: se o conjunto encolher abaixo do limiar, a suíte reprova antes de
o texto afirmar a hipótese.

## Procedência dos casos novos

Os dez casos novos **não** têm a mesma força de oráculo que os quinze antigos, e o arquivo
`testes/casos/casos_recomendacao.json` registra a diferença no campo `origem_referencia`:

- **`"Autor - Calculado a mao"`** (CAL-01 a CAL-11, ADU-01, ADU-15 a ADU-17): o autor
  calculou a referência à mão a partir do Manual impresso, sem ver a saída do sistema.
  Prova que a transcrição **e** o algoritmo estão certos.
- **`"Assistente - calculado a partir das transcricoes JSON; conferido pelo autor"`**
  (ADU-20 a ADU-28, CAL-12): a referência foi derivada das tabelas já transcritas em
  `dados/` e depois conferida pelo autor contra o Manual. Prova que o **algoritmo** está
  certo; não prova a transcrição, porque parte dela.

Nos casos novos o campo `verificacao_cruzada` repete `referencia` — os dois vieram do
mesmo cálculo, e não de duas leituras independentes. Ali a comparação entre os dois campos
não acrescenta nada além de uma guarda contra edição parcial, e o arquivo diz isso.

Essa assimetria precisa aparecer na Seção de Resultados. Dois dos dez casos novos
corrigiram o motor justamente porque a transcrição estava certa e o código não a lia —
é o tipo de defeito que um caso derivado da transcrição encontra bem, e é diferente do
defeito que só um cálculo manual independente encontra.

## Guarda estrutural que veio de brinde

O caso ADU-23 escrevia `produtividade_estimada`, que é o nome do campo em **frutíferas**,
enquanto cana e tabaco leem `produtividade_t_ha`. O apurador monta os argumentos por nome
e simplesmente não passava o valor.

No ADU-23 isso derrubou o motor e ficou visível. Nos casos de cebola, tomate e batata o
rendimento caía exatamente no limiar do ajuste, o adicional era zero de qualquer forma, e
o campo errado teria passado em silêncio — um caso que diz exercitar a expectativa de
rendimento sem exercitar nada, somando +1 ao denominador da concordância.

`campos_nao_lidos()` em `siras/validacao/concordancia.py` e o teste
`test_nenhum_caso_carrega_campo_que_o_motor_ignora` fecham essa porta: nenhum caso pode
carregar um campo de entrada que o caminho do seu grupo não consome.
