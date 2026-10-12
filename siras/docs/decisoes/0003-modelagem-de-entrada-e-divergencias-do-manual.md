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

**Decisão:** `m` é calculado a partir de `al`, `ca`, `mg` e `k` (já existentes) no momento
do uso, via `AnaliseSolo.obter_saturacao_al()`.

**Extensão (2026-08-22, após os casos de teste validados):** os casos de calagem em PD
consolidado (`testes/casos/casos_recomendacao.json`, CAL-02/CAL-04) trazem `saturacao_al`
como **entrada direta** do laudo, não `ca`/`mg`/`k`/`al` para derivar — cenário real quando
o laudo de solo já traz m% calculado. `AnaliseSolo.saturacao_al` agora é um campo opcional:
quando informado, é usado diretamente; quando ausente, `obter_saturacao_al()` calcula pela
CTC efetiva como a decisão original previa. Implementado em `siras/dominio/analise.py`.

*(Implementado em `siras/motor/calagem.py` para `graos_pd_consolidado` (via
`nao_aplicar_se`), `batata_e_batata_doce` e `frutiferas_ph55` (via
`decisao.tipo="ph_menor_que_e_al"`, mesmo `obter_saturacao_al()`) e, desde 2026-08-23,
também `graos_pd_com_restricoes` — mesmo `obter_saturacao_al()`, agora lido da camada
`subsuperficie` (ver D6).)*

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
(5) da Tabela 5.6 é lida pelo autor. *(Implementado em `siras/motor/calagem.py`, validado
pelo caso CAL-07 — macieira, incorporação a 30 cm.)*

## D6 — SMP e saturação por Al em duas camadas (PD consolidado com restrições)

**Revisão de 2026-08-22 — a decisão original abaixo foi descartada por risco de correção.**

O critério `graos_pd_com_restricoes` exige dado de duas camadas (0–10 e 10–20 cm), mas
`AnaliseSolo` representa uma análise de camada única. A primeira proposta era um punhado de
campos opcionais `_10_20` soltos em `AnaliseSolo` (ph, al, ca, mg, k, indice_smp).

**Por que foi descartada:** `AnaliseSolo` alimenta também o módulo de adubação (P, K, MO,
argila), que interpreta esses valores como a camada de referência (0–20 cm convencional, ou
0–10 cm em PD consolidado — Tab. 6.1 e segs.). Se os campos padrão de `AnaliseSolo`
passassem a significar "camada 10–20 cm" só para satisfazer `graos_pd_com_restricoes`, o
módulo de adubação leria P/K/MO da subsuperfície sem aviso nenhum — erro silencioso que
nenhum teste de calagem pegaria, porque vive inteiramente do lado da adubação.

**Direção corrigida (ainda não implementada):** um objeto `Camada` explícito, e os campos
padrão de `AnaliseSolo` permanecem, por invariante do sistema inteiro, a camada de
referência de fertilidade (nunca a subsuperfície):

```python
@dataclass(frozen=True)
class Camada:
    de_cm: int
    ate_cm: int
    ph_agua: Optional[float] = None
    indice_smp: Optional[float] = None
    ca: Optional[float] = None
    mg: Optional[float] = None
    k: Optional[float] = None
    al: Optional[float] = None

# Em AnaliseSolo:
subsuperficie: Optional[Camada] = None  # exigido só pelos criterios que a declararem
```

E `criterios_calagem.json` passaria a declarar explicitamente de qual camada cada critério
lê, em vez de o código assumir por convenção (`graos_pd_com_restricoes` como exemplo):

```json
"amostragem_cm": [[0, 10], [10, 20]],
"decisao": {"tipo": "ph_menor_que_e_al", "camada": "subsuperficie", "ph": 5.5, "saturacao_al_maior_igual": 30},
"dose": {"tipo": "smp_medio", "camadas": ["superficie", "subsuperficie"], "ph_alvo": 6.0}
```

**Confirmado pelo autor em 2026-08-22, direto na Tabela 5.3 (p. 75):**

1. **Dose — média aritmética confirmada.** Nota (7), literal: usa-se o índice SMP médio das
   duas camadas (0–10 e 10–20 cm) para definir a dose de calcário a incorporar. É a média
   dos dois índices, não uma amostra composta de terceira medição. (SMP ser tamponamento e
   não necessariamente linear continua tecnicamente verdadeiro, mas é irrelevante aqui — o
   Manual prescreve o procedimento, e o SIRAS reproduz o Manual, não a físico-química.)

   **Pendência que isso abriu — resolvida.** A Tabela 5.2 é discreta, em passos de 0,1; uma
   média como 5,45 (de SMP 5,3 e 5,6) não existe na tabela. Decisão do autor em
   `docs/decisoes/0002-calagem-dirigida-por-criterio-de-grupo.md`, D10 (2026-08-23): o índice
   médio é arredondado meio para cima (mesma regra de D1) **antes** de consultar a tabela —
   sem interpolação. 5,45 vira 5,5.

2. **Gatilho — confirmado.** A célula diz `pH < 5,5` **e** `Al ≥ 30%` (o `≥` é um dos
   glifos-imagem do PDF, não um `=` da extração literal). O Al é saturação por Al na CTC,
   coerente com a nota (1) ("saturação por Al na CTC < 10%"). O
   `saturacao_al_maior_igual: 30` já presente em `criterios_calagem.json` está correto.

   **Ponto de atenção para a implementação:** a exceção da nota (1) — V ≥ 65% e Al < 10% —
   está ancorada apenas na linha "sem restrições" e na linha "arroz, semeadura em solo
   seco", **não** na linha "com restrições". `graos_pd_com_restricoes` não deve herdar essa
   exceção. (O dado em `criterios_calagem.json` já está correto — esse critério não tem
   `nao_aplicar_se` — mas fica registrado aqui para não ser "corrigido" por engano numa
   reescrita futura.)

3. **Quem decide "com restrições" — a proposta original deste item estava errada.** A nota
   (3) define "restrições" como produtividade abaixo da média local (sobretudo em anos secos),
   compactação restringindo o crescimento radicular, e P na camada 10–20 cm abaixo do teor
   crítico — fatores de campo e de observação do técnico, não deriváveis de um laudo/
   `AnaliseSolo`. "Com restrições" é diagnóstico feito **antes** de escolher o critério; o
   `pH < 5,5 E Al ≥ 30%` é a regra de decisão **dentro** do critério já escolhido, não o que
   seleciona o critério. **`mapa_culturas.json` e `resolver_criterio_id()` permanecem como
   estão** — a hipótese de o motor inferir a condição a partir do Al da subsuperfície foi
   descartada.

**Status: implementado em 2026-08-23.** As três perguntas originais e a pendência de
arredondamento que a primeira abriu (D10, ADR 0002) foram todas respondidas antes de
codificar — o desenho do `Camada`, o invariante de que os campos padrão de `AnaliseSolo`
são sempre a camada de fertilidade, e a declaração `decisao.camada`/`dose.
usar_smp_medio_das_camadas` no JSON (resto deste ADR) valem exatamente como descrito
acima. Oráculo: CAL-10 (SMP médio exato na grade) e CAL-11 (SMP médio 5,45, fora da
grade, exercita o arredondamento de D10), calculados à mão pelo autor em 2026-08-23
(`testes/casos/casos_recomendacao.json`).

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
*(Implementado em `siras/motor/calagem.py` via avaliador genérico de `nao_aplicar_se`
(campo/operador/valor de `criterios_calagem.json`), validado pelos casos CAL-02 (exceção
não se aplica) e CAL-04 (exceção se aplica).)*

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
5 t/ha — o teto deve disparar raramente. *(Implementado em `siras/motor/calagem.py`;
`testes/unidade/test_calagem.py::TestTetoAplicacaoSuperficial` cobre o caso em que o teto
dispara de fato, já que nenhum dos 10 casos validados em 2026-08-22 chega a 5 t/ha.)*

## Nota de escopo (atualizada em 2026-08-22)

D4, D5, D7, D8 e D9 foram implementadas em `siras/motor/calagem.py` e `siras/motor/adubacao.py`
(novo), depois que o autor calculou e conferiu 10 casos de teste à mão
(`testes/casos/casos_recomendacao.json`) e confirmou que batem com `verificacao_cruzada`.
`testes/unidade/test_casos_validados.py` liga esses 10 casos diretamente ao motor real.

**Atualização de 2026-08-22:** `decisao.tipo="ph_menor_que_e_al"` foi implementado (cobre
`batata_e_batata_doce` e `frutiferas_ph55`), junto com a expansão de `mapa_culturas.json`
para as 21 culturas de grãos. `motor/calagem.py` cobria então 14 dos 15 critérios de
`criterios_calagem.json` — só `graos_pd_com_restricoes` seguia pendente.

**Atualização de 2026-08-23:** D6 foi respondido pelo autor (ver seção D6 acima), D10
(ADR 0002) fixou a política de arredondamento do SMP médio, e `graos_pd_com_restricoes`
foi implementado com CAL-10/CAL-11 como oráculo. `motor/calagem.py` cobre agora os 15
critérios de `criterios_calagem.json` — nenhum permanece pendente por falta de decisão.
