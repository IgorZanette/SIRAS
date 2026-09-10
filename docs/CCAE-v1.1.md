# Caderno de Critérios de Aptidão Edáfica (CCAE)

**Versão:** 1.1
**Status:** aprovado pelo orientador — e-mail do Prof. Dr. Rafael Rieder em 10/09/2026, 14:04 (transcrito no Apêndice D)
**Data de congelamento:** 2026-09-10
**Tag Git prevista:** `criterios-v1.1`
**Sistema:** SIRAS — Sistema de Recomendação e Aptidão do Solo

---

> **AVISO DE PROCEDIMENTO**
>
> Este documento é a **especificação** do módulo de aptidão edáfica do SIRAS. Ele deve ser aprovado por escrito pelo orientador e receber uma tag no repositório **antes** do início da implementação.
>
> O gabarito dos casos de teste é gerado aplicando este documento **manualmente**, sem consultar o código-fonte. Se o gabarito for derivado do código, a verificação de conformidade perde validade metodológica e o resultado não pode ser reportado na monografia.
>
> Alterações posteriores geram nova versão (`v1.1`, `v1.2`...) com registro de motivo no Apêndice C. Alterações feitas **após** a execução do conjunto de validação invalidam aquele conjunto.

---

## 1. Escopo e natureza do artefato

### 1.1 O que este módulo é

Um classificador determinístico baseado em regras que, a partir dos atributos químicos e físicos de uma análise de solo e de uma cultura alvo, atribui uma **classe de aptidão edáfica** em dois cenários: o estado atual do solo e o estado projetado após a aplicação das correções recomendadas pelo próprio SIRAS.

### 1.2 O que este módulo NÃO é

Não é uma avaliação de aptidão agrícola das terras no sentido de Ramalho Filho e Beek (1995) nem do Mapa de Aptidão Agrícola das Terras do Brasil (Embrapa/IBGE, 2025). Não considera relevo, declividade, clima, deficiência hídrica, deficiência de oxigênio, suscetibilidade à erosão, pedregosidade, profundidade efetiva do perfil, drenagem, impedimentos à mecanização ou legislação ambiental.

O Manual RS/SC 2016 (Cap. 2, p. 23) é explícito ao afirmar que os fatores que determinam a aptidão agrícola das terras incluem características do solo (profundidade efetiva, textura, drenagem) e do ambiente (declividade, pedregosidade, degradação, risco de enchentes) que **devem ser considerados** para a utilização do sistema de recomendação. Este módulo cobre apenas o subconjunto químico e textural desses fatores. Essa limitação deve constar de toda saída ao usuário e da Seção 4.7 da monografia.

**Nomenclatura obrigatória:** usar sempre o termo *aptidão edáfica*, nunca *aptidão agrícola*, na interface, no laudo e no texto. As classes definidas aqui não devem usar a notação de grupos e subgrupos de Ramalho Filho e Beek (`1(a)`, `3(ab)`, `4p`), sob pena de sugerir equivalência inexistente.

### 1.3 Culturas cobertas

As culturas com pH de referência e tabelas completas no Manual RS/SC 2016, conforme a Seção 4.7 da proposta. Ficam **fora do escopo** o arroz irrigado por alagamento e a mandioca — as ramificações correspondentes existem na especificação (marcadas `FORA_DE_ESCOPO`) mas não devem ser implementadas nem testadas na v1.0.

---

## 2. Princípios de construção

| # | Princípio | Consequência prática |
|---|---|---|
| P1 | Nenhum limiar numérico é criado pelo autor | Todo valor rastreia a uma tabela do Manual RS/SC 2016 ou de Sobral et al. (2015), com tabela e página registradas |
| P2 | A arquitetura vem do sistema oficial | Graus de limitação e regra do fator mínimo seguem Ramalho Filho e Beek (1995), conforme descrito por Höfig et al. (2015) |
| P3 | Toda decisão do autor é isolada e declarada | As decisões de julgamento estão listadas exaustivamente no Apêndice A e implementadas como parâmetros configuráveis, nunca embutidas em código |
| P4 | Separação entre limitação corrigível e permanente | Duas saídas: aptidão atual e aptidão potencial pós-correção |
| P5 | Falha explícita | Dado ausente nunca é imputado por valor médio; gera classe `INDETERMINADA` com justificativa |

---

## 3. Escala de classes de aptidão edáfica

Escala **ordinal de quatro níveis**. A ordem é significativa e é usada pelas métricas de conformidade.

| Código | Rótulo | Significado |
|---|---|---|
| `APTA` | Apta | Nenhum atributo edáfico avaliado impõe limitação superior a ligeira. Expectativa de rendimento próxima ao máximo com adubação de manutenção |
| `APTA_COM_RESTRICOES` | Apta com restrições | Pelo menos um atributo em grau moderado. Limitações corrigíveis dentro de uma safra com as práticas indicadas no laudo |
| `RESTRITA` | Restrita | Pelo menos um atributo em grau forte. Exige correção plurianual ou investimento elevado antes de se atingir o potencial produtivo |
| `INAPTA_SEM_CORRECAO` | Inapta sem correção prévia | Pelo menos um atributo em grau muito forte. O cultivo não é indicado antes da correção |
| `INDETERMINADA` | Indeterminada | Atributos obrigatórios ausentes ou inválidos. **Não é classe de aptidão** — é estado de erro e fica fora do cálculo de conformidade |

**Justificativa do rótulo `INAPTA_SEM_CORRECAO`:** o sufixo é obrigatório. Solo ácido ou pobre em fósforo não é inapto em caráter permanente; é inapto no estado em que se encontra. Rotular como "inapta" simples seria agronomicamente falso e é o tipo de imprecisão que um auditor da área rejeita de imediato.

---

## 4. Graus de limitação

Cinco graus, conforme Ramalho Filho e Beek (1995), citados por Höfig et al. (2015, p. 357): *nulo, ligeiro, moderado, forte e muito forte*.

Codificação interna ordinal:

```
NULO = 0 | LIGEIRO = 1 | MODERADO = 2 | FORTE = 3 | MUITO_FORTE = 4
```

### 4.1 Ancoragem do mapeamento (fundamento central do CCAE)

O Manual RS/SC 2016 (Cap. 6, p. 89–90) estabelece que as classes de disponibilidade de P e K correspondem a faixas de **rendimento relativo** das culturas: a classe Muito baixo corresponde a aproximadamente 40% do rendimento máximo; Baixo, de 40 a 75%; Médio, de 75 a 90%; e o teor crítico é o limite superior da faixa Médio, onde normalmente se obtêm rendimentos próximos à máxima eficiência econômica, situados em torno de 90% do rendimento relativo máximo. A faixa Alto vai do teor crítico até o dobro dele, e Muito alto acima disso.

Esse é o vínculo que torna o mapeamento **não arbitrário**: um grau de limitação é, por definição, uma restrição ao rendimento sustentado, e o Manual já quantifica a restrição associada a cada classe.

| Classe de disponibilidade (Manual) | Rendimento relativo esperado | Grau de limitação |
|---|---|---|
| Muito baixo | ~40% | `MUITO_FORTE` |
| Baixo | 40 – 75% | `FORTE` |
| Médio | 75 – 90% | `MODERADO` |
| Alto | ≥ 90% (acima do teor crítico) | `NULO` |
| Muito alto | ≥ 90% (≥ 2× teor crítico) | `NULO` + alerta ambiental |

**Alerta ambiental na classe Muito alto:** o Manual (Cap. 10, p. 332–333) observa que a classe Muito alto não tem limite superior e que, a partir de determinado teor, o risco de dano ambiental aumenta sensivelmente, associado ao Limite Crítico Ambiental (LCA). O alerta é emitido no laudo mas **não altera a classe de aptidão**, porque é risco ambiental e não limitação produtiva. Decisão registrada em A-6.

---

## 5. Variáveis de entrada

### 5.1 Obrigatórias

| Campo | Unidade | Faixa válida | Uso |
|---|---|---|---|
| `ph_agua` | — | 3,0 – 9,0 | F1 |
| `indice_smp` | — | 4,0 – 7,5 | Dose de calcário (cenário corrigido) |
| `argila` | % | 0 – 100 | Classe de argila; F2; F7 |
| `mo` | % (dag/kg) | 0 – 20 | F6 |
| `p_mehlich1` | mg/dm³ | 0 – 500 | F2 |
| `k_mehlich1` | mg/dm³ | 0 – 2000 | F3 |
| `ca` | cmolc/dm³ | 0 – 40 | F4; m%; V% |
| `mg` | cmolc/dm³ | 0 – 20 | F4; m%; V% |
| `al` | cmolc/dm³ | 0 – 20 | F1 (m%) |
| `ctc_ph7` | cmolc/dm³ | 0 – 60 | F3; F5; V% |
| `cultura` | enum | catálogo | Seleciona pH ref. e grupos de exigência |

### 5.2 Opcionais com regra de derivação

| Campo | Se ausente |
|---|---|
| `v_percent` | Calcular: `V% = 100 × S / CTC_pH7`, com `S = Ca + Mg + K_cmolc` |
| `m_percent` | Calcular: `m% = 100 × Al / (Al + S)` |
| `k_cmolc` | Converter: `K_cmolc = K_mg_dm3 / 391,0` |
| `na` | Assumir 0,0 e registrar a assunção no laudo |
| `s_enxofre` | Fator F8 não avaliado; registrar |

### 5.3 Conversões Mehlich-3 → Mehlich-1

Aplicar **antes** de qualquer interpretação, quando o laudo indicar Mehlich-3 (Manual, notas das Tabelas 6.3–6.6 e 6.8–6.10):

```
P_M1 = P_M3 / (2 − (0,02 × argila))
K_M1 = K_M3 × 0,83
```

Onde `argila` está em %. Guardar valor original e convertido no laudo, para rastreabilidade.

### 5.4 Validação

Valor fora da faixa válida → **rejeitar a entrada**, não truncar. Campo obrigatório ausente → classe `INDETERMINADA` com a lista dos campos faltantes. Nenhuma imputação por média, mediana ou valor típico é permitida (P5).

---

## 6. Fatores de limitação

Sete fatores. Cada um recebe um grau de 0 a 4.

---

### F1 — Acidez e toxidez por alumínio

**Fonte:** Manual RS/SC 2016, Tabela 5.1 (p. 68), texto p. 69, Tabelas 5.3 a 5.7; Sobral et al. (2015), Tabela 4.

O Manual estabelece que a toxidez por Al é uma das maiores limitações de solos ácidos e que o Al em forma trocável só ocorre quando o pH em água é menor que 5,5. Para culturas com pH de referência 6,0, a acidez limita pouco a produtividade enquanto o pH cai de 6,0 até 5,5, pois somente abaixo desse valor reaparece o Al trocável.

**Ramo (a) — culturas COM pH de referência** (5,5 / 6,0 / 6,5, conforme Tabela 5.1):

| Condição | Grau | Origem do limiar |
|---|---|---|
| `pH ≥ pH_ref` | `NULO` | Tabela 5.1 |
| `5,5 ≤ pH < pH_ref` | `LIGEIRO` | Texto p. 69: a acidez limita pouco a produtividade nessa faixa |
| `pH < 5,5` e `m% < 30` | `MODERADO` | Sobral et al. (2015), Tab. 4: saturação por Al < 30% = baixa |
| `pH < 5,5` e `30 ≤ m% ≤ 50` | `FORTE` | Sobral et al. (2015), Tab. 4: 30–50% = média |
| `pH < 5,5` e `m% > 50` | `MUITO_FORTE` | Sobral et al. (2015), Tab. 4: > 50% = alta |

**Ramo (b) — culturas SEM pH de referência** (araucária, acácia-negra, bracatinga, cedro-australiano, erva-mate, eucalipto, pinus, pastagem natural — Tabela 5.1):

O Manual estabelece que estas espécies são tolerantes ao Al trocável e não respondem à correção da acidez; a resposta à calagem é atribuída principalmente ao suprimento de Ca e Mg, com critério baseado em `V% < 40%`, exceto se `Ca ≥ 4,0` e `Mg ≥ 1,0 cmolc/dm³` (Tabelas 5.6 e 5.7).

| Condição | Grau |
|---|---|
| `V% ≥ 40` ou (`Ca ≥ 4,0` e `Mg ≥ 1,0`) | `NULO` |
| `V% < 40` e não satisfaz a exceção Ca/Mg | `MODERADO` |

Neste ramo o pH **não** é avaliado. F1 nunca ultrapassa `MODERADO`, o que é coerente com a tolerância documentada dessas espécies.

**Nota de escopo:** o arroz irrigado nos sistemas pré-germinado e com transplante de mudas também aparece sem pH de referência (aumento natural de pH pelo alagamento), mas está `FORA_DE_ESCOPO` na v1.0.

---

### F2 — Disponibilidade de fósforo

**Fonte:** Manual RS/SC 2016, Tabelas 6.2 a 6.6 (p. 93–94).

Passo 1 — enquadrar a cultura no grupo de exigência (Tabela 6.2):

| Grupo | Teor crítico | Culturas | Tabela |
|---|---|---|---|
| 1 | 1,7× o de grãos | alho, beterraba, cenoura, batata, roseira de corte | 6.3 |
| 2 | igual ao de grãos | culturas de grãos (exceto arroz irrigado); hortaliças exceto Grupo 1; pastagens exceto pastagem natural; frutíferas; gengibre | 6.4 |
| 3 | 0,5× o de grãos | demais culturas: florestais, medicinais, aromáticas, condimentares, raízes, cana-de-açúcar, tabaco | 6.5 |
| 4 | — | arroz irrigado por alagamento | 6.6 — `FORA_DE_ESCOPO` |

Passo 2 — determinar a classe de argila (nota das Tabelas 6.3–6.5):

| Classe | Faixa de argila |
|---|---|
| 1 | > 60% |
| 2 | 41 – 60% |
| 3 | 21 – 40% |
| 4 | ≤ 20% |

Passo 3 — enquadrar `p_mehlich1` (mg P/dm³):

**Tabela 6.3 — Grupo 1**

| Classe | Argila 1 | Argila 2 | Argila 3 | Argila 4 |
|---|---|---|---|---|
| Muito baixo | ≤ 5,0 | ≤ 7,0 | ≤ 10,0 | ≤ 17,0 |
| Baixo | 5,1 – 10,0 | 7,1 – 14,0 | 10,1 – 20,0 | 17,1 – 34,0 |
| Médio | 10,1 – 15,0 | 14,1 – 21,0 | 20,1 – 30,0 | 34,1 – 51,0 |
| Alto | 15,1 – 30,0 | 21,1 – 42,0 | 30,1 – 60,0 | 51,1 – 102,0 |
| Muito alto | > 30,0 | > 42,0 | > 60,0 | > 102,0 |

**Tabela 6.4 — Grupo 2**

| Classe | Argila 1 | Argila 2 | Argila 3 | Argila 4 |
|---|---|---|---|---|
| Muito baixo | ≤ 3,0 | ≤ 4,0 | ≤ 6,0 | ≤ 10,0 |
| Baixo | 3,1 – 6,0 | 4,1 – 8,0 | 6,1 – 12,0 | 10,1 – 20,0 |
| Médio | 6,1 – 9,0 | 8,1 – 12,0 | 12,1 – 18,0 | 20,1 – 30,0 |
| Alto | 9,1 – 18,0 | 12,1 – 24,0 | 18,1 – 36,0 | 30,1 – 60,0 |
| Muito alto | > 18,0 | > 24,0 | > 36,0 | > 60,0 |

**Tabela 6.5 — Grupo 3**

| Classe | Argila 1 | Argila 2 | Argila 3 | Argila 4 |
|---|---|---|---|---|
| Muito baixo | ≤ 1,5 | ≤ 2,0 | ≤ 3,0 | ≤ 5,0 |
| Baixo | 1,5 – 3,0 | 2,1 – 4,0 | 3,1 – 6,0 | 5,1 – 10,0 |
| Médio | 3,1 – 4,5 | 4,1 – 6,0 | 6,1 – 9,0 | 10,1 – 15,0 |
| Alto | 4,6 – 9,0 | 6,1 – 12,0 | 9,1 – 18,0 | 15,1 – 30,0 |
| Muito alto | > 9,0 | > 12,0 | > 18,0 | > 30,0 |

> ⚠ **PENDÊNCIA A-10 RESOLVIDA (ver Apêndice A).** O texto extraído do PDF apresenta a faixa Baixo da coluna Argila 1 como "1,5 – 3,0", aparentemente sobrepondo o limite superior de Muito baixo (≤ 1,5). Isso é artefato do arredondamento a uma casa decimal do Manual, não erro de transcrição nem lacuna real (mesmo raciocínio da Seção 2 do CCAE-implementacao.md). `dados/comum/interpretacao_p.json` (Tabela 6.5, p. 94) já traz esta mesma tabela, transcrita e conferida pelo autor em 2026-08-22, representando cada classe **apenas pelo limite superior**, com comparação `de < valor ≤ ate` em ordem crescente. Sob essa convenção, o valor 1,5 classifica-se em Muito baixo (`1,5 ≤ 1,5`) e Baixo passa a valer, na prática, de 1,5 (exclusive) a 3,0 (inclusive) — sem sobreposição e sem necessidade de mover o limite para 1,6. O motor de aptidão (F2_fosforo) referencia `interpretacao_p.json` diretamente em vez de duplicar esta tabela, eliminando o risco de as duas fontes divergirem.

Passo 4 — aplicar o mapeamento da Seção 4.1.

---

### F3 — Disponibilidade de potássio

**Fonte:** Manual RS/SC 2016, Tabelas 6.7 a 6.10 (p. 95–96).

Passo 1 — grupo de exigência (Tabela 6.7):

| Grupo | Teor crítico | Culturas | Tabela |
|---|---|---|---|
| 1 | 1,5× o de grãos | alho, beterraba, cenoura, mandioquinha-salsa, tomateiro, batata, batata-doce, roseira de corte | 6.8 |
| 2 | igual ao de grãos | culturas de grãos; pastagens exceto pastagem natural; frutíferas; mandioca; hortaliças exceto Grupo 1 | 6.9 |
| 3 | 0,7× o de grãos | demais culturas não inclusas nos Grupos 1 e 2 | 6.10 |

> **Atenção:** os grupos de P e de K **não coincidem**. A mandioquinha-salsa e o tomateiro estão no Grupo 1 de K mas não no Grupo 1 de P; a mandioca está no Grupo 2 de K e no Grupo 3 de P. O catálogo de culturas deve manter os dois campos independentes (`grupo_p`, `grupo_k`). Erro clássico — cobrir com caso de teste dedicado.

Passo 2 — classe de CTC pH 7,0: `≤ 7,5` | `7,6 – 15,0` | `15,1 – 30,0` | `> 30,0`

Passo 3 — enquadrar `k_mehlich1` (mg K/dm³):

**Tabela 6.8 — Grupo 1**

| Classe | CTC ≤ 7,5 | 7,6 – 15,0 | 15,1 – 30,0 | > 30,0 |
|---|---|---|---|---|
| Muito baixo | ≤ 30 | ≤ 45 | ≤ 60 | ≤ 70 |
| Baixo | 31 – 60 | 46 – 90 | 61 – 120 | 71 – 140 |
| Médio | 61 – 90 | 91 – 135 | 121 – 180 | 141 – 210 |
| Alto | 91 – 180 | 136 – 270 | 181 – 360 | 211 – 420 |
| Muito alto | > 180 | > 270 | > 360 | > 420 |

**Tabela 6.9 — Grupo 2**

| Classe | CTC ≤ 7,5 | 7,6 – 15,0 | 15,1 – 30,0 | > 30,0 |
|---|---|---|---|---|
| Muito baixo | ≤ 20 | ≤ 30 | ≤ 40 | ≤ 45 |
| Baixo | 21 – 40 | 31 – 60 | 41 – 80 | 46 – 90 |
| Médio | 41 – 60 | 61 – 90 | 81 – 120 | 91 – 135 |
| Alto | 61 – 120 | 91 – 180 | 121 – 240 | 136 – 270 |
| Muito alto | > 120 | > 180 | > 240 | > 270 |

**Tabela 6.10 — Grupo 3**

| Classe | CTC ≤ 7,5 | 7,6 – 15,0 | 15,1 – 30,0 | > 30,0 |
|---|---|---|---|---|
| Muito baixo | ≤ 15 | ≤ 20 | ≤ 30 | ≤ 35 |
| Baixo | 16 – 30 | 21 – 40 | 31 – 60 | 36 – 70 |
| Médio | 31 – 45 | 41 – 60 | 61 – 90 | 71 – 105 |
| Alto | 46 – 90 | 61 – 120 | 91 – 180 | 106 – 210 |
| Muito alto | > 90 | > 120 | > 180 | > 210 |

Passo 4 — mapeamento da Seção 4.1.

---

### F4 — Cálcio e magnésio trocáveis

**Fonte:** Manual RS/SC 2016, Tabela 6.11 (p. 97).

O Manual usa **três** classes para Ca, Mg e S, e considera satisfatórios os teores na classe Alto, ressalvando que para algumas culturas teores Médio de Ca e Mg já são suficientes para bom desempenho agronômico.

| Nutriente | Baixo | Médio | Alto |
|---|---|---|---|
| Ca (cmolc/dm³) | < 2,0 | 2,0 – 4,0 | > 4,0 |
| Mg (cmolc/dm³) | < 0,5 | 0,5 – 1,0 | > 1,0 |

Mapeamento (três classes → três graus, preservando a ordem):

| Classe | Grau | Justificativa |
|---|---|---|
| Alto | `NULO` | Manual: teores satisfatórios |
| Médio | `LIGEIRO` | Manual: já suficientes para bom desempenho em algumas culturas |
| Baixo | `MODERADO` | Corrigível com calcário dolomítico na mesma operação da calagem |

`F4 = max(grau_Ca, grau_Mg)`.

> **Decisão do autor (A-2):** F4 é limitado a `MODERADO` porque a deficiência de Ca e Mg é corrigível com o mesmo insumo e na mesma operação já prevista pelo módulo de calagem, não constituindo restrição forte independente. O Manual não atribui graus de limitação a Ca e Mg; a compressão de três classes em três graus preserva a ordem sem criar limiares.

---

### F5 — Capacidade de troca de cátions (CTC pH 7,0)

**Fonte:** Manual RS/SC 2016, Tabela 6.1 (p. 91) e texto p. 71–72; Sobral et al. (2015).

| Faixa (cmolc/dm³) | Classe (Manual) | Grau |
|---|---|---|
| ≤ 7,5 | Baixa | `MODERADO` |
| 7,6 – 15,0 | Média | `LIGEIRO` |
| 15,1 – 30,0 | Alta | `NULO` |
| > 30,0 | Muito alta | `NULO` |

Fundamentação: o Manual registra que solos com baixo poder tampão — arenosos e/ou pobres em matéria orgânica, geralmente com índice SMP maior que 6,3 — podem ter a acidez potencial subestimada pelo índice SMP, exigindo equações alternativas, e que a correspondência entre pH de referência e V% desloca-se cerca de cinco pontos percentuais em solos com CTC pH7 abaixo de 7,5 cmolc/dm³. Sobral et al. (2015) acrescentam que em solos de baixa CTC o parcelamento de N e K é necessário para evitar perdas por lixiviação.

> **Decisão do autor (A-3):** F5 é limitado a `MODERADO`. É um fator **modulador** de risco de manejo, não uma restrição direta ao rendimento, e nenhuma das fontes lhe atribui grau forte. Marcado como `PERMANENTE` na Seção 7.

---

### F6 — Matéria orgânica (indicador de suprimento de N)

**Fonte:** Manual RS/SC 2016, Tabela 6.1 (p. 91).

O Manual classifica a MO em três classes utilizadas como indicador da disponibilidade de nitrogênio do solo.

| Faixa (%) | Classe | Grau |
|---|---|---|
| ≤ 2,5 | Baixo | `MODERADO` |
| 2,6 – 5,0 | Médio | `LIGEIRO` |
| > 5,0 | Alto | `NULO` |

> **Decisão do autor (A-4):** limitado a `MODERADO` porque a deficiência de N é suprível integralmente por adubação dentro da própria safra, ao contrário de P e K, cuja correção pode exigir adubação corretiva plurianual. Marcado como `CORRIGIVEL` quanto ao suprimento de N e `PERMANENTE` quanto ao nível de MO em si (ver Seção 7).
>
> **Exceção não implementada na v1.0:** o Manual registra faixas adicionais de interpretação de MO para forrageiras e tabaco (Cap. 6.2 e 6.9), em função da resposta diferenciada ao N. Registrar como pendência para versão futura e como limitação na monografia.

---

### F7 — Textura (teor de argila)

**Fonte:** Manual RS/SC 2016, Tabela 6.1 (p. 91) e texto p. 72; Sobral et al. (2015).

| Classe de argila | Faixa | Grau |
|---|---|---|
| 4 | ≤ 20% | `MODERADO` |
| 3 | 21 – 40% | `LIGEIRO` |
| 2 | 41 – 60% | `NULO` |
| 1 | > 60% | `NULO` |

Fundamentação: solos arenosos apresentam menor poder tampão, menor retenção de nutrientes e maior risco de lixiviação, condições que o Manual trata explicitamente ao indicar equações alternativas ao índice SMP e que Sobral et al. (2015) associam à necessidade de parcelamento.

> **Decisão do autor (A-5):** este é o fator **mais fracamente fundamentado** do conjunto. Nenhuma das fontes atribui grau de limitação diretamente à textura de forma isolada; a inferência parte do tratamento diferenciado que ambas dão a solos arenosos. Deve ser o primeiro item submetido à auditoria agronômica (Seção 10) e o primeiro candidato a remoção. Marcado como `PERMANENTE`.
>
> **Nota:** a interação entre textura e disponibilidade de P já está contemplada em F2 pelas classes de argila. F7 captura a limitação residual de retenção hídrica e de nutrientes, não a de fósforo. Há risco de dupla contagem — a análise de sensibilidade (Seção 9.4) deve reportar o efeito de desativar F7.

---

## 7. Cenários: aptidão atual e aptidão potencial

Ramalho Filho e Beek estabelecem que o enquadramento da classe é feito pela comparação dos graus de limitação existentes **ou remanescentes após a aplicação de práticas de melhoria** nas condições da terra (Höfig et al., 2015, p. 357). O CCAE adota essa mesma lógica em dois cenários.

| Cenário | Definição | Análogo em R.F. e Beek |
|---|---|---|
| `ATUAL` | Graus calculados sobre os valores do laudo, sem intervenção | Nível de manejo A |
| `POTENCIAL` | Graus remanescentes após aplicação integral das recomendações de calagem e adubação emitidas pelo próprio SIRAS | Níveis B/C (uso de insumos) |

**Nota de honestidade:** os níveis A, B e C de Ramalho Filho e Beek distinguem-se também por tração animal e motomecanização, dimensões que este módulo não avalia. O paralelo é **parcial** e deve ser descrito como tal na monografia — nunca apresentado como equivalência.

### 7.1 Classificação de corrigibilidade

| Fator | Corrigibilidade | Estado no cenário `POTENCIAL` |
|---|---|---|
| F1 acidez | `CORRIGIVEL` | `NULO`, se a dose de calcário recomendada for exequível (ver 7.2) |
| F2 fósforo | `CORRIGIVEL` | `NULO` — a adubação corretiva visa elevar o teor à classe Alto |
| F3 potássio | `CORRIGIVEL` | `NULO` — idem |
| F4 Ca/Mg | `CORRIGIVEL` | `NULO` via calcário dolomítico |
| F5 CTC | `PERMANENTE` | inalterado |
| F6 MO | `CORRIGIVEL` (N) | `NULO` — o N é suprível por adubação na safra |
| F7 textura | `PERMANENTE` | inalterado |

A fundamentação de F2 e F3 é o próprio objetivo declarado do sistema de recomendação: o Manual afirma que o objetivo é atingir e permanecer na faixa Alto, considerada a faixa de disponibilidade mais adequada para as plantas.

### 7.2 Critério de exequibilidade da calagem

A correção da acidez só é considerada realizável se a dose recomendada não exceder o limite operacional:

- Aplicação **incorporada**: sem limite explícito no Manual. Adotar teto de `NC ≤ 20 t/ha` (PRNT 100%) — a Tabela 5.2 tabula até 29,0 t/ha para índice SMP ≤ 4,4 no pH 6,5, mas doses dessa magnitude não são operacionalmente plausíveis em uma safra.
- Aplicação **superficial** (plantio direto consolidado, campo natural): `NC ≤ 5 t/ha`, limite explícito nas notas das Tabelas 5.4, 5.5 e 5.6.

Se a dose exceder o teto, F1 no cenário `POTENCIAL` permanece um grau acima de `NULO` e o laudo registra `correcao_parcelada = true`, indicando necessidade de correção plurianual. Se F1 já era `NULO` ou `LIGEIRO` no cenário `ATUAL` (isto é, a calagem não chega a ser disparada pelo critério da cultura, porque o pH já está acima de 5,5), não há dose a aplicar e F1 permanece inalterado no cenário `POTENCIAL` — não há correção a projetar quando o próprio Manual não recomenda calcário.

> **Decisão do autor (A-7):** o teto de 20 t/ha para aplicação incorporada é escolha do autor. O limite de 5 t/ha para superfície é literal do Manual. Ambos são parâmetros de configuração.

**Consequência de projeto:** no cenário `POTENCIAL`, a classe é determinada exclusivamente por F5, F6 (nível estrutural) e F7. A diferença entre `ATUAL` e `POTENCIAL` **quantifica o ganho atribuível à recomendação que o SIRAS acabou de emitir** — o que integra os dois módulos do sistema e rende discussão substantiva na monografia.

---

## 8. Regra de composição

### 8.1 Fator mínimo

Höfig et al. (2015, p. 357) registram que, no sistema oficial, o fator de limitação que impõe o maior grau de limitação é o que determina a classe. O CCAE adota literalmente esse critério.

```
grau_final = max(F1, F2, F3, F4, F5, F6, F7)
```

Mapeamento para classe:

| `grau_final` | Classe |
|---|---|
| `NULO` (0) **ou** `LIGEIRO` (1) | `APTA` |
| `MODERADO` (2) | `APTA_COM_RESTRICOES` |
| `FORTE` (3) | `RESTRITA` |
| `MUITO_FORTE` (4) | `INAPTA_SEM_CORRECAO` |

Em caso de empate no grau máximo entre fatores, o fator determinante reportado é o de menor índice na ordem F1 < F2 < ... < F7 — escolha arbitrária mas determinística, só relevante para o campo informativo `fator_determinante`, nunca para a classe.

### 8.2 Regra de rebaixamento por acúmulo

```
se (contagem de fatores com grau ≥ MODERADO) ≥ 3
   e classe ≠ INAPTA_SEM_CORRECAO:
       rebaixar uma classe
```

> **Decisão do autor (A-1) — a mais frágil do documento.** O sistema de Ramalho Filho e Beek **não prevê** rebaixamento por acúmulo; usa fator mínimo puro. A regra existe para capturar a situação, comum em solos do RS, em que múltiplas limitações moderadas simultâneas produzem desempenho pior do que qualquer uma delas isoladamente sugeriria. Não há fonte que a sustente.
>
> **Implementar como flag `REBAIXAMENTO_POR_ACUMULO`, default `False`.** O resultado principal da conformidade e da auditoria deve ser reportado **com a regra desativada**, isto é, em conformidade estrita com o sistema oficial. O efeito de ativá-la é reportado apenas como análise de sensibilidade (Seção 9.4). Se o auditor agronômico não a endossar, remover na v1.1.

### 8.3 Saída completa

O motor retorna, para cada cenário:

```json
{
  "cenario": "ATUAL",
  "classe": "RESTRITA",
  "grau_final": 3,
  "fator_determinante": "F2_fosforo",
  "fatores": [
    {"id": "F1_acidez", "grau": 1, "rotulo": "LIGEIRO",
     "evidencia": "pH 5,7 entre 5,5 e pH de referência 6,0",
     "fonte": "Manual RS/SC 2016, Tab. 5.1 e texto p. 69"},
    {"id": "F2_fosforo", "grau": 3, "rotulo": "FORTE",
     "evidencia": "P 7,2 mg/dm3, argila classe 3, grupo de exigencia 2 -> classe Baixo",
     "fonte": "Manual RS/SC 2016, Tab. 6.2 e 6.4"}
  ],
  "alertas": [],
  "rebaixamento_aplicado": false,
  "versao_criterios": "1.1"
}
```

O campo `fonte` é obrigatório em todos os fatores. É ele que dá **rastreabilidade** à saída — objetivo já declarado na proposta — e é o que permite ao auditor agronômico contestar um critério específico em vez do sistema inteiro.

---

### 8.3.1 IDs canônicos dos fatores

Para eliminar divergências de nomenclatura entre documentação, dados, gabarito e implementação,
a v1.1 fixa os seguintes identificadores canônicos. Estes identificadores devem ser usados
literalmente no campo `id` de cada fator e em `fator_determinante`.

| Fator | ID canônico | Não usar |
|---|---|---|
| F1 — Acidez/Al | `F1_acidez` | — |
| F2 — Fósforo | `F2_fosforo` | — |
| F3 — Potássio | `F3_potassio` | — |
| F4 — Cálcio e magnésio | `F4_ca_mg` | `F4_calcio_magnesio` |
| F5 — CTC | `F5_ctc` | — |
| F6 — Matéria orgânica | `F6_mo` | `F6_materia_organica` |
| F7 — Textura | `F7_textura` | — |

A tabela é normativa para a v1.1. Nomes antigos permanecem apenas em registros históricos.

---

## 9. Protocolo de verificação de conformidade

Isto é **verificação**, não validação. Mede se a implementação reproduz esta especificação. Não mede se a especificação está agronomicamente correta.

### 9.1 Geração do gabarito

1. Congelar o CCAE (tag Git + e-mail datado de aprovação do orientador).
2. Construir os casos.
3. Aplicar o CCAE **manualmente**, em planilha, sem abrir o código.
4. Implementar.
5. Comparar.

Se você mesmo gerar o gabarito, faça-o **antes** de implementar ou com intervalo mínimo de sete dias e sem consultar o código. Registre a data de cada gabarito na planilha — é a evidência de independência.

### 9.2 Conjunto de casos

Divisão obrigatória:

| Conjunto | N | Uso |
|---|---|---|
| Calibração | 14 | Casos `CAL-01` a `CAL-14`; ajustes no CCAE são permitidos e geram nova versão |
| Conformidade | 62 | Casos restantes válidos; executados ao final. Qualquer ajuste posterior invalida o conjunto |

Estratificação do conjunto de conformidade:

- **Por grupo de cultura:** os seis grupos do escopo, com pelo menos um caso de cada ramo especial (frutíferas em três fases, erva-mate, tabaco Virgínia e Burley).
- **Por ramo de F1:** casos com pH de referência 5,5 / 6,0 / 6,5 e casos sem pH de referência (ramo b).
- **Por fator determinante:** ao menos 4 casos para cada um dos sete fatores como fator determinante isolado.
- **Casos de fronteira — mínimo 12:** valores exatamente nos limites publicados e a ±0,1 deles. Exemplos: `pH = 5,5` exato; `argila = 20,0` e `20,1`; `P = 6,0` e `6,1` na classe de argila 3, grupo 2; `CTC = 7,5` e `7,6`; `m% = 30,0` e `50,0`; `Ca = 2,0` e `4,0`.
- **Casos de erro — mínimo 3:** campo obrigatório ausente, valor fora de faixa, cultura desconhecida. Devem retornar `INDETERMINADA` ou rejeição, e ficam fora do cálculo das métricas.

### 9.3 Métricas

Meta declarada: **100% de conformidade**. Qualquer divergência é defeito, é investigada, corrigida e registrada no Apêndice B. Não use limiar de 80% aqui — não é hipótese estatística.

Reportar adicionalmente:

- **Cobertura de regras:** percentual dos ramos de decisão do CCAE exercitados pelo conjunto. Meta: 100% dos ramos das Seções 6, 7 e 8. Instrumentar com `coverage.py` sobre o módulo de aptidão.
- **Matriz de confusão** entre classe esperada e obtida, mesmo que idealmente diagonal — expõe assimetria de erro se houver defeito.

### 9.4 Análise de sensibilidade

Executar o conjunto de conformidade em quatro configurações e reportar a distribuição de classes em cada uma:

| # | Configuração |
|---|---|
| 1 | Baseline: fator mínimo puro, sete fatores |
| 2 | Com `REBAIXAMENTO_POR_ACUMULO` ativado |
| 3 | Sem F7 (textura) |
| 4 | Sem F5 e F7 (apenas fatores de fertilidade em sentido estrito) |

Isso transforma as decisões frágeis do Apêndice A em **resultado mensurado** em vez de premissa oculta. É a resposta pronta quando a banca perguntar o quanto os julgamentos do autor afetam a saída.

---

## 10. Auditoria agronômica posterior

Você não tem agrônomo disponível durante o desenvolvimento. O CCAE é projetado para que a auditoria possa acontecer **depois**, sem retrabalho.

### 10.1 O que preparar desde já

- **Apêndice A** (decisões do autor) como documento autônomo, legível por quem não conhece o sistema.
- **Formulário de auditoria por critério**, com uma linha por decisão: `[ ] endosso  [ ] endosso com ressalva  [ ] rejeito`, mais campo de justificativa.
- **10 laudos completos** gerados pelo SIRAS, com os campos `evidencia` e `fonte` visíveis, cobrindo classes distintas.

### 10.2 O que pedir ao auditor

Não peça classificação cega dos casos — isso exigiria protocolo de painel que você não tem condições de montar. Peça **parecer sobre os critérios**: se as faixas foram corretamente extraídas do Manual, se o mapeamento classe→grau é razoável, e quais das decisões do Apêndice A ele endossa.

### 10.3 Como reportar

Subseção própria, qualitativa, **sem percentual**. Formulação sugerida:

> Os critérios foram submetidos a parecer técnico de [nome, formação, vínculo], que endossou N das M decisões registradas, apresentou ressalva quanto a [...] e não endossou [...]. As ressalvas foram incorporadas na versão 1.1 do Caderno de Critérios / registradas como limitação.

Se a auditoria não acontecer até a entrega, isso vira uma linha na Seção 4.7, e não um problema — desde que o Apêndice A esteja escrito e o formulário pronto. É a diferença entre "não validei" e "não validei, mas deixei tudo preparado e identificado para validação".

---

## 11. Ajustes na monografia

| Seção | Ação |
|---|---|
| 2.3 | O objetivo de validar passa a referir-se apenas às recomendações de calagem e adubação. A aptidão migra integralmente para o objetivo de projetar e implementar |
| 2.4 | Remover H0.2 e H1.2. Manter apenas o par sobre calagem e adubação |
| 3.1.3 | Acrescentar que o CCAE deriva a arquitetura de Ramalho Filho e Beek mas não reproduz o sistema, e explicitar a diferença de escala e de fatores |
| 4.3 | Inserir passo entre (c) e (d): **congelamento e aprovação do Caderno de Critérios, com data anterior à implementação**. Ajustar (h) para separar validação das recomendações de verificação de conformidade da aptidão |
| 4.4 | Nova subseção: verificação de conformidade (casos, estratificação, cobertura, geração independente do gabarito, análise de sensibilidade). Nova subseção: auditoria agronômica qualitativa |
| 4.7 | Acrescentar o parágrafo de limitação abaixo |
| Apêndices | CCAE integral; Apêndice A de decisões; planilha de gabarito; formulário de auditoria |

Parágrafo para a Seção 4.7:

> Os critérios de aptidão edáfica implementados foram derivados pelo autor a partir das faixas de interpretação do Manual de Calagem e Adubação para os estados do RS e SC (2016) e da arquitetura de graus de limitação do Sistema de Avaliação da Aptidão Agrícola das Terras (Ramalho Filho; Beek, 1995), e foram verificados quanto à conformidade da implementação frente à especificação congelada previamente ao desenvolvimento. Não foram submetidos a validação por painel independente de especialistas nem a experimentação agronômica de campo. Portanto, os resultados atestam a correção e a rastreabilidade da implementação, e não a adequação agronômica dos critérios em si, o que se registra como trabalho futuro.

---

## Apêndice A — Registro exaustivo de decisões do autor

Toda escolha não determinada pelas fontes. É a lista que vai ao auditor e à banca.

| ID | Decisão | Fundamentação | Fragilidade | Parâmetro |
|---|---|---|---|---|
| A-1 | Rebaixamento por acúmulo de 3+ fatores moderados | Nenhuma. Heurística do autor | **Alta** | `REBAIXAMENTO_POR_ACUMULO` (default `False`) |
| A-2 | F4 limitado a `MODERADO` | Corrigível na mesma operação de calagem | Média | `F4_GRAU_MAXIMO` |
| A-3 | F5 limitado a `MODERADO` | Fator modulador de manejo, não restrição direta de rendimento | Média | `F5_GRAU_MAXIMO` |
| A-4 | F6 limitado a `MODERADO` | N é suprível integralmente na safra | Baixa | `F6_GRAU_MAXIMO` |
| A-5 | Existência de F7 como fator autônomo | Inferido do tratamento diferenciado de solos arenosos | **Alta** | `F7_ATIVO` |
| A-6 | Classe Muito alto não rebaixa a aptidão | Risco ambiental, não limitação produtiva | Baixa | `MUITO_ALTO_REBAIXA` |
| A-7 | Teto de 20 t/ha para calagem incorporada | Plausibilidade operacional | Média | `NC_MAX_INCORPORADO` |
| A-8 | Uso dos limiares de m% de Sobral et al. (2015) | Manual não gradua m%; fonte é do próprio projeto | Média | tabela `F1_M_PERCENT` |
| A-9 | Escala de quatro classes | Adaptação da escala Boa/Regular/Restrita/Inapta | Baixa | — |
| A-10 | Resolvido: sem correção de valor. A aparente sobreposição da Tab. 6.5, coluna argila classe 1 (Muito baixo ≤ 1,5; Baixo "1,5 – 3,0") é artefato de arredondamento do PDF, não erro de transcrição. Sob a convenção de classificação por limite superior (`de < valor ≤ ate`, já em uso em `dados/comum/interpretacao_p.json`, conferido pelo autor em 2026-08-22), 1,5 cai em Muito baixo e Baixo passa a valer, na prática, de 1,5 (exclusive) a 3,0 (inclusive) — sem sobreposição. Não foi necessário adotar 1,6 nem alterar nenhum valor transcrito | Convenção de classificação por limite superior (Seção 2 do CCAE-implementacao.md), já aplicada a todas as tabelas de interpretação do SIRAS | Baixa — resolvido sem alteração de dado | — |

## Apêndice B — Registro de divergências de conformidade

| # | Caso | Esperado | Obtido | Causa | Correção | Data |
|---|---|---|---|---|---|---|
| B-1 | `CONF-FR-06` | coluna `F2` = `FORTE` | `F2` = `NULO` | Célula `F2` do gabarito não foi atualizada quando o caso foi corrigido na conferência. A própria observação da linha diz que, com argila classe 3, P = 20,0 cai em Alto e "F2 vai a NULO", e as colunas `classe_esperada` (`APTA_COM_RESTRICOES`) e `fator_determinante_esperado` (`F3_potassio`) só fazem sentido com F2 = NULO — se F2 fosse FORTE a classe seria RESTRITA. Divergência do gabarito, não da implementação | **Resolvido em 2026-09-10:** célula `F2` da linha `CONF-FR-06` corrigida para `NULO`, conforme instrução do autor. Causa confirmada por ele: ao aplicar a correção de argila 20,1 → classe 3, as colunas `classe_argila`, `classe_esperada` e `fator_determinante_esperado` foram atualizadas, mas `F2` continuou vindo da planilha provisória. Erro de geração do CSV. Nenhuma alteração de código nem de critério | 2026-09-09 → 2026-09-10 |
| B-2 | `CAL-12` (alfafa) | `APTA` / `F1_acidez` | `INDETERMINADA` | `alfafa` tem pH de referência na Tab. 5.1 mas não tem grupo de exigência resolvível: `interpretacao_p.json` cita "pastagens exceto pastagem natural" só em `culturas_texto`, que é descrição, não lista. Lacuna de transcrição do Anexo 2, não defeito do motor | **Resolvido em 2026-09-10:** autor transcreveu do Anexo 2, seção FORRAGEIRAS (*Medicago sativa*): `grupo_p = 2`, `grupo_k = 2`. `alfafa` acrescentada à lista `culturas` do `grupo_2` em `interpretacao_p.json` e `interpretacao_k.json`. Nenhuma alteração de código nem de critério | 2026-09-09 → 2026-09-10 |
| B-3 | `CONF-F3-03` (gengibre) | `APTA_COM_RESTRICOES` / `F2_fosforo` | `INDETERMINADA` | Mesma causa de B-2. A Tab. 6.2 nomeia o gengibre explicitamente no Grupo 2 de P, mas só no texto do grupo; a lista `culturas` não o inclui | **Resolvido em 2026-09-10:** autor transcreveu do Anexo 2, seção MEDICINAIS (*Zingiber officinale*): `grupo_p = 2`, `grupo_k = 3` — uma das cinco divergências P≠K do catálogo. `gengibre` acrescentado ao `grupo_2` de `interpretacao_p.json` e ao `grupo_3` de `interpretacao_k.json`. Nenhuma alteração de código nem de critério | 2026-09-09 → 2026-09-10 |
| B-4 | `CONF-PT-05` (eucalipto, POTENCIAL) | `APTA` / `F5_ctc` (F1 = `NULO`) | `APTA_COM_RESTRICOES` / `F1_acidez` (F1 = `MODERADO`) | O critério de calagem `erva_mate_e_florestais` existe em `criterios_calagem.json`, mas `mapa_culturas.json` mapeia só as 21 culturas de grãos mais erva-mate e macieira. Sem o eucalipto mapeado, a dose não é calculável, o motor não consegue verificar a exequibilidade (§7.2) e mantém F1 — comportamento correto e explícito, sobre base incompleta | **Resolvido em 2026-09-10:** as seis espécies florestais restantes do Anexo 2, seção FLORESTAIS, p. 364 (acácia-negra, araucária, bracatinga, cedro-australiano, eucalipto, pinus) mapeadas em `mapa_culturas.json` para o critério `erva_mate_e_florestais`, que já existia. Todas declaram `grupo: "erva_mate"` porque essa é a chave do grupo desse critério em `criterios_calagem.json` — invariante do carregador, não afirmação agronômica sobre a espécie. Nenhuma alteração de código nem de critério | 2026-09-09 → 2026-09-10 |

| B-5 | `CONF-RB-04` (pastagem natural) | — | — | **Não é divergência de resultado: é atribuição de fonte não verificada, e o teste passa.** A Seção 7.1, ramo (b), inclui a pastagem natural entre as culturas sem pH de referência e atribui o critério `V% < 40` com exceção `Ca ≥ 4,0` e `Mg ≥ 1,0` às **Tabelas 5.6 e 5.7**. A Tab. 5.6 (p. 83) cobre frutíferas e florestais — é a fonte do critério `erva_mate_e_florestais` em `criterios_calagem.json`, e a exceção Ca/Mg é a nota (2) dela. A Tab. 5.7 cobre medicinais e ornamentais. **Pastagem natural não está em nenhuma das duas:** campo natural é da Tabela 5.4 (p. 78), que `criterios_calagem.json`, campo `escopo`, declara fora do escopo do SIRAS. A pertinência ao ramo (b) está correta — `ph_referencia.json` põe `pastagem-natural` no grupo sem pH de referência da Tab. 5.1 —; o que não está sustentado é o critério de grau usado para ela. O caso passa hoje porque V% = 40,0 exatos cai em `NULO` pela regra como escrita, o que torna o defeito invisível para a suíte | **Pendente do autor:** conferir a Tabela 5.4 (p. 78) no impresso — a extração de PDF dessa tabela veio embaralhada e está no bloco de conferência pendente. Se o critério para campo natural divergir, isto é defeito de **especificação**: gera CCAE v1.2, exclui a pastagem natural do ramo (b) ou cria ramo próprio, e obriga a regabaritar o `CONF-RB-04`. Ver também a tensão de escopo: `CAL-12` (alfafa) e `CONF-RB-04` são as duas culturas da Tab. 5.4 presentes no conjunto de conformidade da aptidão, embora a calagem de pastagem esteja declarada fora de escopo | 2026-09-10 |

**Fechamento do Apêndice B (2026-09-10).** Com B-1 a B-4 resolvidos, a conformidade passou de 77/80 para **80/80 = 100%**, tanto em classe quanto em fator determinante. Suíte completa: 1291 testes passando, 1 pulado. **B-5 permanece aberto** e não é medido por esse número: é uma atribuição de fonte da própria especificação, e o caso afetado passa. Não corrigir isso antes da banca significa apresentar 100% de conformidade sobre um critério cuja procedência, para uma das culturas, não foi verificada — o percentual continua verdadeiro, mas a leitura de que "tudo está conferido" não.

Registro para a monografia, porque a distinção importa: **nenhum critério do CCAE foi alterado** para chegar a esse resultado. As quatro correções foram uma célula de gabarito gerada errada (B-1) e três lacunas de transcrição da base de conhecimento (B-2 a B-4) — todas preenchidas pelo autor a partir do Anexo 2 do Manual. O motor não recebeu uma linha de código nova em nenhum dos quatro casos, e a especificação verificada é a mesma que já estava congelada. O conjunto de conformidade permanece, portanto, válido pela regra do aviso de procedimento: o que invalidaria o conjunto seria mudar a especificação depois de executá-lo.

## Apêndice C — Histórico de versões

| Versão | Data | Alteração | Motivo | Conjunto invalidado? |
|---|---|---|---|---|
| 1.0 | | Versão inicial | — | — |
| 1.1 | 2026-09-09 | Correção do mapeamento de §8.1 já previsto no texto; IDs canônicos de F1–F7; fechamento de A-10 pela convenção de limite superior; ajuste do protocolo §9 para 14 calibração + 62 conformidade; correção dos casos CONF-PT-03 e CONF-PT-04. | Auditoria de consistência do gabarito v1.0 e correção de casos malformados. | Sim — qualquer gabarito anterior à v1.1 é inválido como evidência de conformidade. |

## Apêndice D — Registro da aprovação do orientador

Evidência exigida pela §9.1 (congelamento do Caderno) e pela etapa 2 da ordem de trabalho de `docs/CCAE-implementacao.md`.

| Campo | Valor |
|---|---|
| Orientador | Prof. Dr. Rafael Rieder (UPF — LABRV, PPGCA, PPGAGRO) |
| Meio | E-mail, confirmando aval verbal dado anteriormente em orientação |
| Data e hora do recebimento | 10/09/2026, 14:04 |
| Objeto | Caderno de Critérios de Aptidão Edáfica, v1.1 — em especial as decisões de julgamento do Apêndice A relativas à calagem |
| Resultado | Aprovado. Autorização explícita para seguir na linha proposta |

### D.1 Transcrição integral do e-mail

> Olá Igor, boa tarde!
>
> Creio que sua decisão está embasada no conhecimento empírico seu em relação a calagem (experiência prática, observação do cotidiano e eventual tentativa e erro). Pode seguir nessa linha. Podemos usar isso no artigo na hora de justificar eventuais escolhas.
>
> De todo modo, se conseguir encontrar na literatura algum outro autor que já fez algo similar, ou adotou determinado parâmetro que você escolheu, podemos usá-lo para fortalecer a justificativa, citando-o. Isso dará mais robustez, mostrando que não tomou por base somente o manual da Embrapa.
>
> Conversamos a noite. Abraço!
>
> --
> []s
> Prof. Dr. Rafael Rieder
> University of Passo Fundo (UPF)
> Head of Virtual Reality and Computer Vision Research Lab (LABRV)
> Graduate Program in Applied Computing (PPGCA)
> Graduate Program in Agronomy (PPGAGRO)
> Lattes: http://lattes.cnpq.br/3010497094377497
> ORCID: https://orcid.org/0000-0002-7435-9054
> Scopus Author ID: 24597781600
> Web of Science ResearcherID: G-5808-2011

*Nota de precisão terminológica:* a fonte normativa do SIRAS é o Manual de Calagem e Adubação para os Estados do RS e SC (CQFS-RS/SC, 11. ed., 2016, publicado pela SBCS — Núcleo Regional Sul), não uma publicação da Embrapa. A menção do e-mail é transcrita como recebida; a citação correta consta das Referências deste Caderno.

### D.2 Consequências normativas

1. **As decisões de julgamento do Apêndice A ficam aprovadas como estão.** A base declarada da aprovação é o conhecimento empírico do autor sobre calagem — experiência prática, observação de campo e tentativa e erro. Isso não altera o princípio P1: os limiares continuam rastreados ao Manual; o que a aprovação cobre é o conjunto de escolhas do autor listadas em A-1 a A-9, que por definição não têm limiar publicado.
2. **A justificativa dessas escolhas passa a ter status de argumento defensável na monografia e no artigo**, com a origem empírica declarada abertamente em vez de omitida.
3. **Encaminhamento aberto (do autor):** buscar na literatura autores que tenham adotado parâmetro ou procedimento equivalente, para citar em reforço à justificativa. Não é condição da aprovação — é robustez adicional pedida pelo orientador. Registrado como pendência P4 no `docs/ROADMAP.md`.

### D.3 Cronologia da aprovação

A aprovação dos critérios foi **dada verbalmente pelo orientador em orientação anterior**, antes da implementação do motor de aptidão; o e-mail de 10/09/2026 é a **confirmação por escrito** desse aval, obtida para servir de evidência documental exigida pela §9.1. A ordem efetiva foi, portanto:

| # | Evento | Data |
|---|---|---|
| 1 | Redação do Caderno como especificação, sem código de aptidão existente | anterior a 07/09/2026 |
| 2 | Aval verbal do orientador aos critérios, em orientação | anterior à implementação |
| 3 | Implementação do motor de aptidão (commits `492c563` a `cd1c0df`) | 07/09 a 09/09/2026 |
| 4 | Fechamento da v1.1 e verificação de conformidade (77/80) | 09/09/2026 |
| 5 | Confirmação escrita da aprovação — e-mail transcrito em D.1 | 10/09/2026, 14:04 |
| 6 | Reunião de acompanhamento sobre o concluído e o andamento do projeto | 10/09/2026, à noite |
| 7 | Congelamento do Caderno: tag `criterios-v1.1` | 10/09/2026 |

A alegação de não-circularidade da §9.1 se sustenta sobre o fato de a **especificação ter sido escrita antes do código** e o gabarito ter sido aplicado a partir dela — a data do e-mail é registro do aval, não o momento em que ele foi dado. Nenhum critério foi alterado após a aprovação.

---

## Referências

COMISSÃO DE QUÍMICA E FERTILIDADE DO SOLO — RS/SC. **Manual de calagem e adubação para os Estados do Rio Grande do Sul e de Santa Catarina.** 11. ed. Sociedade Brasileira de Ciência do Solo — Núcleo Regional Sul, 2016.

HÖFIG, P.; MOURA, N. S. V.; GIASSON, E. Aptidão agrícola das terras em Cerro Grande do Sul/RS. **Boletim Gaúcho de Geografia**, v. 42, n. 1, p. 352–368, jan. 2015.

RAMALHO FILHO, A.; BEEK, K. J. **Sistema de avaliação da aptidão agrícola das terras.** 3. ed. rev. Rio de Janeiro: EMBRAPA-CNPS, 1995. 65 p.

SOBRAL, L. F. et al. **Guia prático para interpretação de resultados de análises de solo.** Aracaju: Embrapa Tabuleiros Costeiros, 2015. (Documentos, 206).

EMBRAPA SOLOS; INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. **Mapa de aptidão agrícola das terras do Brasil, escala 1:500.000, 2ª aproximação.** 2025.
