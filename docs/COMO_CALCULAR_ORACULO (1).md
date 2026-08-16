# Como calcular a necessidade de calagem à mão (construção do oráculo)

Este documento descreve o procedimento manual usado para gerar os valores de referência de
`testes/casos/casos_recomendacao.json`. É parte do método de validação: os valores de referência
precisam ser obtidos de forma **independente do sistema**, aplicando diretamente os critérios do
Manual.

Fonte: CQFS-RS/SC, *Manual de Calagem e Adubação para os estados do RS e de SC*, 11. ed., 2016.

---

## 1. O que significa cada índice

| Índice | Unidade | O que é | Para que serve na calagem |
|---|---|---|---|
| **pH em água** | — | **Acidez ativa**: concentração de H⁺ na solução do solo. É a acidez que a planta "sente" no momento. | Decide **SE** aplica calcário (condição de disparo) |
| **Índice SMP** | — | **Acidez potencial**: mede a reserva de H⁺ e Al³⁺ presa aos coloides do solo, obtida pela leitura do pH após adicionar uma solução-tampão à amostra. Quanto **menor** o SMP, **maior** a acidez potencial e maior a dose. | Decide **QUANTO** aplicar (Tabela 5.2) |
| **PRNT** | % | **Poder Relativo de Neutralização Total** do corretivo: combina a pureza química (PN) com a finura das partículas (RE). Um calcário PRNT 70% neutraliza 70% do que neutralizaria o CaCO₃ puro e moído, em 3 meses. | Converte a dose teórica na dose real do produto comprado |
| **CTC pH 7,0** | cmolc/dm³ | **Capacidade de Troca de Cátions**: total de cargas negativas do solo disponíveis para reter cátions. É o "tamanho do depósito" de nutrientes. | Base do cálculo quando o critério é por saturação por bases |
| **V%** | % | **Saturação por bases**: proporção da CTC ocupada por bases trocáveis (Ca + Mg + K). V alto = depósito cheio de nutrientes; V baixo = depósito cheio de H e Al. | Critério de disparo e de dose em culturas sem pH de referência; também entra em exceções |
| **Saturação por Al (m%)** | % | Proporção da CTC ocupada por Al³⁺ trocável, o cátion tóxico às raízes. | Condição adicional de disparo em alguns critérios |
| **Ca, Mg trocáveis** | cmolc/dm³ | Teores de cálcio e magnésio disponíveis. | Exceção: se já houver Ca e Mg suficientes, a calagem por V% é dispensada |
| **MO** | % | Matéria orgânica do solo. | Entra nas equações de solos de baixo poder tampão (SMP > 6,3) |
| **Al trocável** | cmolc/dm³ | Alumínio trocável. | Idem |
| **NC** | t/ha | **Necessidade de Calcário**, sempre expressa na base PRNT 100% até a conversão final. | É a saída do cálculo |

**A distinção que mais confunde:** pH em água e índice SMP medem coisas diferentes. Dois solos podem
ter o mesmo pH 5,1 e precisar de doses muito distintas, porque um tem alta reserva de acidez
(argiloso, SMP baixo) e outro tem baixa (arenoso, SMP alto). Por isso o Manual usa um índice para
decidir *se* e outro para decidir *quanto*.

---

## 2. Procedimento, passo a passo

### Passo 1 — Identificar o critério aplicável

Com a cultura, o sistema de manejo e a condição da área, localize a linha correspondente em:

| Grupo | Tabela | Página |
|---|---|---|
| Grãos (inclui as forrageiras integradas à lavoura) | 5.3 | 75 |
| Hortaliças, tubérculos e raízes | 5.5 | 81 |
| Frutíferas e espécies florestais (inclui erva-mate) | 5.6 | 83 |
| Cana-de-açúcar e tabaco | 5.7 | 86 |

A linha fornece quatro informações: **camada amostrada**, **condição de disparo**, **pH alvo da
dose** e **fator** (1, ½ ou ¼), além do modo de aplicação.

⚠️ O **pH de referência** da Tabela 5.1 não é o pH alvo da dose nem a condição de disparo. Os três
são valores distintos e frequentemente diferentes. Exemplo: grãos têm pH de referência 6,0, disparam
em pH < 5,5 e a dose é calculada para pH 6,0. Macieira tem pH de referência 6,5, dispara em
pH < 6,0 e a dose é para pH 6,5.

### Passo 2 — Testar a condição de disparo

Avalie a condição da coluna "Tomada de decisão", **e também as exceções das notas de rodapé**:

- Se a condição **não** for satisfeita → **NC = 0**, com o motivo registrado. O cálculo termina aqui.
- Se houver exceção aplicável (nota de rodapé) → **NC = 0**, com o motivo da exceção.

Exceções mais comuns:

| Exceção | Onde | Leitura |
|---|---|---|
| V ≥ 65% **e** saturação por Al < 10% | Tab. 5.3, nota (1) — plantio direto consolidado | Ambas as condições precisam ser verdadeiras ao mesmo tempo para dispensar a calagem |
| Ca ≥ 4,0 **e** Mg ≥ 1,0 cmolc/dm³ | Tab. 5.5(3), 5.6(2), 5.7(1) — critérios por V% | Idem: o "e" é conjunção, não alternativa |

### Passo 3 — Ler a Tabela 5.2 (p. 70)

Entre com o **índice SMP** na linha e o **pH alvo do critério** na coluna (5,5 / 6,0 / 6,5). O valor
lido é a NC base, em t/ha de calcário PRNT 100%, para a camada de 0–20 cm.

Casos de contorno: SMP < 4,4 usa a primeira linha (`≤ 4,4`); SMP > 7,1 resulta em 0.

**Critérios por saturação por bases** (erva-mate, florestais, mandioca, arroz pré-germinado) não
usam a Tabela 5.2. Nesses casos:

```
NC = ((V_alvo − V_solo) / 100) × CTC_pH7,0
```

com V_alvo = 40%.

### Passo 4 — Aplicar o fator do critério

Multiplique a NC base pelo fator da linha:

| Fator | Quando |
|---|---|
| 1 | Convencional, implantação do PD, e a maioria dos casos incorporados |
| ½ | Campo natural de baixa acidez potencial (SMP > 5,5) iniciando PD em superfície (p. 73); reaplicação em frutíferas de ciclo longo na fase de produção (Tab. 5.6, nota 3) |
| ¼ | Plantio direto consolidado, aplicação superficial |

### Passo 5 — Ajustes de profundidade e área

- **Incorporação até 30 cm** (macieira, oliveira, demais frutíferas — notas 4 e 5 da Tab. 5.6):
  multiplicar por **1,5**. Não se aplica a amoreira-preta, mirtilo e palmeira-juçara.
- **Aplicação restrita à faixa de plantio**: `DC = NC × (LFA / DLP) × (100 / PRNT)`, onde LFA é a
  largura da faixa e DLP a distância entre linhas, ambas em metros (p. 83).

### Passo 6 — Limite de aplicação superficial

Quando o modo de aplicação for superficial, a quantidade é **limitada a 5 t/ha (PRNT 100%)**
(Tab. 5.3 nota 5; Tab. 5.5 nota 2; Tab. 5.6 nota 3).

📌 **Decisão de interpretação a registrar:** a nota expressa o teto na base PRNT 100%, o que implica
aplicar o corte **antes** da conversão pelo PRNT. Consequência: com um corretivo de PRNT 70%, a
quantidade física do produto pode ultrapassar 5 t/ha. Confirme essa leitura com o orientador e
registre no ADR 0002 — ela muda resultados e é o tipo de detalhe que a banca pode questionar.

### Passo 7 — Converter pelo PRNT do corretivo

```
dose_real = NC × 100 / PRNT
```

Se o PRNT for 100%, a dose não muda. Fonte: Cap. 8, seção 8.1.1, p. 298.

### Passo 8 — Arredondar

Apenas agora: **1 casa decimal**, em t/ha, **meio para cima** (ADR 0002, D1). Os passos 3 a 7 são
feitos em precisão plena — arredondar no meio do caminho acumula erro e gera divergência artificial
contra o sistema.

---

## 3. Exemplo resolvido

**Caso:** soja, sistema convencional, pH em água 5,1, índice SMP 5,4, corretivo com PRNT 100%.

| Passo | Operação | Resultado |
|---|---|---|
| 1 | Critério: Tab. 5.3, linha "Convencional", camada 0–20 cm | disparo pH < 5,5 · pH alvo 6,0 · fator 1 · incorporado |
| 2 | pH 5,1 < 5,5 ? | **sim** → dispara. Sem exceção aplicável a esta linha |
| 3 | Tab. 5.2, linha SMP 5,4, coluna pH 6,0 | 6,8 t/ha |
| 4 | × fator 1 | 6,8 |
| 5 | Sem ajuste de profundidade ou faixa | 6,8 |
| 6 | Aplicação incorporada — teto de 5 t/ha não se aplica | 6,8 |
| 7 | × 100/100 (PRNT 100%) | 6,8 |
| 8 | Arredondar a 1 casa | **6,8 t/ha** |

No arquivo de casos:

```jsonc
{
  "id": "G-SOJA-01",
  "descricao": "Soja, convencional, pH 5,1, SMP 5,4, PRNT 100 - caso base de calagem",
  "entrada": {
    "cultura": "soja", "ph_agua": 5.1, "indice_smp": 5.4,
    "sistema_manejo": "convencional", "prnt": 100
  },
  "referencia": { "nc_t_ha": 6.8 },
  "memoria_calculo": "Tab. 5.3 (p.75): disparo pH<5,5, alvo 6,0, fator 1. Tab. 5.2 (p.70): SMP 5,4 x pH 6,0 = 6,8. PRNT 100 -> 6,8 t/ha.",
  "origem_referencia": "calculo manual do autor em __/__/2026; conferido com orientador em __/__/2026"
}
```

O campo `memoria_calculo` não é exigido pelo teste, mas documenta o caminho percorrido. Vale ouro
quando um caso discordar três meses depois e você precisar decidir se o erro está no sistema ou na
referência — e serve de material direto para o capítulo de resultados.

---

## 4. Roteiro dos demais casos

Os valores de referência **devem ser calculados por você**, lendo as tabelas. Abaixo está apenas o
caminho a percorrer.

### Caso 2 — Grãos, plantio direto consolidado

Entrada: soja · pH 5,1 · SMP 5,4 · V 50% · saturação por Al 15% · PRNT 75 · sem restrição em 10–20 cm

1. Tab. 5.3, linha "Sistema consolidado, sem restrições" — atenção: camada amostrada é **0–10 cm**
2. Disparo pH < 5,5 e, pela nota (1), verificar se V ≥ 65% **e** Al < 10% dispensam a calagem —
   avalie as duas condições em conjunto
3. Tab. 5.2 com SMP 5,4 e o pH alvo do critério
4. Fator ¼
5. Sem ajuste de profundidade
6. Aplicação **superficial** → verificar o teto de 5 t/ha
7. PRNT 75 → × 100/75
8. Arredondar

### Caso 3 — Grãos, PD consolidado, sem disparo

Entrada: soja · pH 5,8 · SMP 5,4

O pH está **abaixo** do pH de referência (6,0) mas **acima** da condição de disparo (5,5).
Resultado: `nc_t_ha = 0.0`, motivo `ph_acima_do_disparo`. Nenhuma consulta à Tabela 5.2.

Este é o caso mais importante do conjunto inicial: é ele que distingue um sistema que implementou a
cadeia de critérios de um que apenas consultou o pH de referência.

### Caso 4 — Macieira

Entrada: macieira · pH 5,7 · SMP 5,0 · incorporação até 30 cm · PRNT a definir por você

1. Tab. 5.6, linha "Macieira e oliveira" — a condição de disparo **não** é pH < 5,5
2. O pH alvo da dose também **não** é 6,0
3. Tab. 5.2 com SMP 5,0 e o pH alvo correto
4. Fator 1
5. Incorporação a 30 cm → × 1,5 (nota 5)
6. Incorporado, sem teto
7. PRNT
8. Arredondar

Defina o PRNT explicitamente. Todo caso precisa desse campo — sem ele o resultado é ambíguo.

### Caso 5 — Erva-mate

Entrada: erva-mate · V 32% · CTC pH 7,0 = 8,0 cmolc/dm³ · Ca 2,0 · Mg 0,8 cmolc/dm³

1. Tab. 5.6, seção "Espécies florestais" (a erva-mate está nesse grupo pela Tab. 5.1)
2. Disparo V ≤ 40%; exceção se Ca ≥ 4,0 **e** Mg ≥ 1,0 — verifique as duas
3. Não usa a Tabela 5.2. Aplique `NC = ((40 − V) / 100) × CTC`
4. Sem fator
5. Sem ajuste
6. Incorporado, sem teto
7. PRNT
8. Arredondar

---

## 5. Por que você calcula e não a ferramenta

Se os valores de referência forem produzidos pelo mesmo mecanismo (ou pela mesma IA) que gerou o
sistema, a validação deixa de medir correção e passa a medir consistência interna. O oráculo precisa
ser independente da implementação — é o que sustenta a H1.1 na Seção 4.4 da proposta.

Na prática: se o seu número divergir de qualquer outra fonte, **o Manual decide**. E se um caso
discordar na execução, a primeira hipótese a testar não é "o sistema errou", e sim "qual dos dois
está errado" — por isso a `memoria_calculo` existe.
