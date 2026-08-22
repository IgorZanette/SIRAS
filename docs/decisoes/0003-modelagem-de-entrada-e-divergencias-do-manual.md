# ADR 0003 — Modelagem de entrada e divergências internas do Manual

**Status:** aceito · **Data:** 2026-08-22

## Contexto

Ao expandir `siras/motor/calagem.py` além do caminho `graos_convencional`/`ph_menor_que`,
surgiram cinco questões que o Manual não resolve de forma direta em código — quatro de
modelagem de entrada e uma de divergência textual interna do próprio Manual. O autor
conferiu cada uma diretamente no Manual (não Claude Code) antes de decidir.

## D4 — Saturação por Al (m%) é campo calculado, não de entrada

O Manual (Cap. 3, p. 53) define:

```
m (%) = (Al³⁺ / CTC_efetiva) × 100,  onde CTC_efetiva = Ca²⁺ + Mg²⁺ + K⁺ + Al³⁺
```

**Ponto de atenção:** a CTC efetiva (denominador de `m`) é diferente da CTC pH 7,0
(denominador de `V%`, já usada em `AnaliseSolo.ctc_ph7`). São duas CTCs distintas — tratar
uma pela outra é erro silencioso e plausível.

K entra em cmolc/dm³, mas o laudo de solo reporta K em mg/dm³. Conversão do Manual:
`K(cmolc/dm³) = K(mg/dm³) / 391`.

**Decisão:** `m` não é campo de `AnaliseSolo` — é calculado a partir de `al`, `ca`, `mg` e
`k` (já existentes) no momento do uso. Se qualquer um desses campos estiver ausente, os
critérios que dependem de `m` (`graos_pd_consolidado`, `graos_pd_com_restricoes`,
`batata_e_batata_doce`, `frutiferas_ph55`) devem falhar com erro explícito citando o campo
faltante — nunca assumir valor.

*(Implementação da função de cálculo de `m` e dos critérios que a usam: pendente — ver
seção "Próximos passos" no README/ROADMAP; depende dos casos de teste calculados pelo
autor.)*

## D5 — `Contexto.profundidade_cm` renomeado para `profundidade_incorporacao_cm`

O campo original colapsava dois conceitos distintos:

- **Camada amostrada** — vem do critério de calagem (`criterios_calagem.json`, campo
  `amostragem_cm`); é dado, não escolha do usuário.
- **Profundidade de incorporação** — decisão operacional do técnico no momento da
  aplicação do calcário; é entrada do `Contexto`.

**Decisão:** `Contexto.profundidade_cm` → `Contexto.profundidade_incorporacao_cm`,
restrito aos valores `20` ou `30` (as duas profundidades que o Manual discute — 0-20 cm
padrão e 30 cm para fruteiras de raiz profunda). Implementado em
`siras/dominio/analise.py`.

O ajuste `dose.fator_30cm` (Tab. 5.6, macieira/oliveira e demais frutíferas) só se aplica
quando `profundidade_incorporacao_cm == 30` **e** o critério declarar `fator_30cm` — por
isso amoreira-preta, mirtilo e palmeira-juçara (critério `frutiferas_ph55`, sem
`fator_30cm`) não recebem o multiplicador mesmo com incorporação a 30 cm, conforme a nota
(5) da Tabela 5.6 é lida pelo autor. *(Lógica de aplicação do fator: pendente.)*

## D6 — SMP e saturação por Al em duas camadas (PD consolidado com restrições)

O critério `graos_pd_com_restricoes` exige SMP médio de duas camadas (0–10 e 10–20 cm),
mas `AnaliseSolo` representa uma análise de camada única. Um modelo de múltiplas camadas
completo seria mais correto, mas é refatoração desproporcional para atender a um único
critério entre dezesseis.

**Decisão (trade-off assumido por escopo):** campos opcionais em `AnaliseSolo`, exclusivos
deste critério:

```python
indice_smp_10_20: float | None = None
al_10_20: float | None = None
ca_10_20: float | None = None
mg_10_20: float | None = None
k_10_20: float | None = None
```

Se o critério exigir esses campos e algum estiver `None`, é erro de validação explícito,
nunca suposição de valor. Extensível a um modelo de múltiplas camadas em trabalho futuro,
se o escopo do TCC permitir. *(Implementação: pendente.)*

## D7 — Divergência interna do Manual: "V > 65%" (texto) vs "V ≥ 65%" (nota da tabela)

O texto corrido da p. 73 diz: *"pode-se considerar não aplicar calcário quando a saturação
por bases for **maior do que** 65% e quando a saturação por Al for **menor do que** 10%"*.
A nota (1) da Tabela 5.3 usa **≥ 65%**. O Manual diverge de si mesmo; só importa no
caso-limite V = 65% exato.

**Decisão:** seguir a tabela (**≥ 65%**), por ser a fonte normativa direta consultada pelo
critério. Divergência registrada aqui para que, se um caso de teste cair exatamente em
V=65%, a escolha não pareça arbitrária.

## D8 — A exceção do PD consolidado é facultativa no Manual; o sistema a aplica deterministicamente

O texto diz *"pode-se considerar não aplicar"* — é uma ponderação oferecida ao técnico, não
uma regra automática. O SIRAS é determinístico e precisa escolher um comportamento.

**Decisão:** quando as duas condições (V ≥ 65% e Al < 10%) forem satisfeitas, o sistema
**aplica** a exceção (`nc_t_ha = 0.0`, motivo `excecao_v_e_al`), e o `Trace`/laudo registra
explicitamente que o Manual apresenta essa dispensa como opção ao técnico, não como
obrigação — para que o usuário saiba que pode optar por calcariar mesmo assim.
*(Implementação: pendente.)*

## D9 — Teto de 5 t/ha em aplicação superficial: antes ou depois da conversão por PRNT

O Manual não resolve isso explicitamente — a nota das tabelas diz apenas "limitada a
5 t/ha (PRNT 100%)"; o texto corrido (p. 72–74) não menciona o teto.

**Argumento a favor de aplicar o corte antes do PRNT:** toda a Tabela 5.2 e os fatores do
critério trabalham na base PRNT 100%; "5 t/ha (PRNT 100%)" está na mesma unidade em que a
dose é lida. A conversão pelo PRNT é etapa posterior (Cap. 8, p. 298), de tradução para o
produto comercial — ler o teto como limite do produto físico exigiria supor que a nota
mudou de unidade sem avisar.

**Argumento a favor de aplicar depois (contraponto agronômico, não descartado):** o limite
existe porque excesso de calcário em superfície não incorporado pode causar desequilíbrio
químico na camada superficial — efeito ligado à quantidade física real aplicada, não à
equivalência teórica em PRNT 100%. Um corretivo de PRNT 60% produziria 8,3 t/ha de produto
físico a partir de uma dose-teto de 5 t/ha (PRNT 100%), acima do que a restrição
pretenderia evitar.

**Decisão:** aplicar o corte de 5 t/ha **antes** da conversão por PRNT (mesma base da
tabela). Na prática, com fator ¼ (único caso de aplicação superficial no escopo atual,
`graos_pd_consolidado`/`olericolas_pd_consolidado`), a dose raramente se aproxima de
5 t/ha — o teto deve disparar raramente. *(Implementação: pendente.)*

## Nota de escopo

Nenhuma das decisões D4–D9 foi implementada em código nesta revisão — a implementação
aguarda os casos de teste calculados à mão pelo autor (ver `docs/COMO_CALCULAR_ORACULO.md`
e `testes/casos/casos_recomendacao.json`), para evitar repetir o padrão que produziu e
descartou a primeira versão de `siras/motor/calagem.py`: código plausível, não verificado.
