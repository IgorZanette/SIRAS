# Handoff — módulo de aptidão edáfica do SIRAS

Contexto para implementação. Leia inteiro antes de escrever código.

---

## 1. O que é este módulo

Classificador determinístico baseado em regras. Recebe os atributos de uma análise química de solo e uma cultura alvo; devolve uma **classe de aptidão edáfica** em dois cenários (estado atual e estado projetado após as correções que o próprio SIRAS recomenda).

**Não é** avaliação de aptidão agrícola das terras. Não considera relevo, clima, erosão, drenagem, profundidade do perfil nem mecanização. Use sempre o termo *aptidão edáfica* na interface e nos laudos, nunca *aptidão agrícola*.

Escopo geográfico: RS e SC. Fonte normativa: Manual de Calagem e Adubação para os Estados do RS e SC, 11ª ed., 2016.

---

## 2. Status metodológico (importante para não quebrar)

Este módulo **não é uma hipótese de pesquisa** do TCC. É um artefato de projeto avaliado por **verificação de conformidade**: mede se a implementação reproduz a especificação, não se a especificação está agronomicamente correta.

A consequência prática: o CCAE foi **escrito e aprovado pelo orientador antes** da implementação — aval verbal em orientação, confirmado por escrito no e-mail de 10/09/2026, transcrito no Apêndice D do `CCAE-v1.1.md`. Ele é a autoridade. Se o código divergir do CCAE, o código está errado — mesmo que a saída pareça mais razoável agronomicamente. Divergências vão para o Apêndice B do CCAE e, se for caso de ambiguidade da especificação, geram nova versão do Caderno; nunca "correção silenciosa" no código.

---

## 3. Arquivos

| Arquivo | Papel |
|---|---|
| `docs/CCAE-v1.1.md` | **Especificação normativa.** Fatores F1–F7, graus, composição, cenários |
| `docs/CCAE-implementacao.md` | Estruturas JSON, contrato do motor, convenções de intervalo |
| `testes/casos/entradas_aptidao.json` | 84 casos, **só entradas** |
| `testes/casos/gabarito_aptidao.csv` | 84 linhas, **só respostas** |
| `testes/unidade/test_conformidade_aptidao.py` | Runner |
| `validar_anexo1.py` | Validação contra o Anexo 1 do Manual (oráculo externo) |

### Restrição de acesso

**Não abra `testes/casos/gabarito_aptidao.csv` durante a implementação.** Ele existe separado do arquivo de entradas exatamente para que o código seja escrito a partir da especificação, e não das respostas. Escrever a implementação com o gabarito à vista invalida a verificação de conformidade.

Se um teste falhar, a investigação é: reler o CCAE → conferir a tabela de origem no Manual → corrigir. Não é: abrir o gabarito e ajustar até passar.

---

## 4. Aviso técnico crítico: exceções à convenção de intervalo

`CCAE-implementacao.md` §2 estabelece a convenção canônica — representar cada classe pelo **limite superior**, comparar com `≤` em ordem crescente. Vale para as tabelas de P (6.3–6.5), K (6.8–6.10), argila, CTC e MO.

**Duas tabelas não seguem essa convenção, e implementá-las com `≤` produz erro silencioso em valores de fronteira:**

**F4 — Tabela 6.11 (Ca e Mg).** O Manual escreve `< 2,0` / `2,0 – 4,0` / `> 4,0`. Portanto Ca = 2,0 é **Médio**, não Baixo. Mesma lógica para Mg em `< 0,5` / `0,5 – 1,0` / `> 1,0`: Mg = 0,5 e Mg = 1,0 são **Médio**.

```python
def classe_ca(v): return "BAIXO" if v < 2.0 else ("MEDIO" if v <= 4.0 else "ALTO")
def classe_mg(v): return "BAIXO" if v < 0.5 else ("MEDIO" if v <= 1.0 else "ALTO")
```

**F1 — saturação por alumínio.** O CCAE escreve `m% < 30` / `30 ≤ m% ≤ 50` / `m% > 50`. Portanto m% = 30,0 é **FORTE**, não MODERADO.

```python
def grau_al(m): return "MODERADO" if m < 30.0 else ("FORTE" if m <= 50.0 else "MUITO_FORTE")
```

Esses dois pontos derrubaram uma verificação anterior. Os casos `CONF-FR-21`, `CONF-FR-23`, `CAL-13` e os três `ANX-G3-*` existem justamente para pegá-los.

Use `Decimal(str(valor))` nas comparações de fronteira. Em float, comparações como `20.1 <= 20.0` e somas de decimais falham de formas que os casos de fronteira expõem.

---

## 5. Contrato do motor

```python
avaliar_aptidao(analise: dict, cultura: str, cenario: str) -> ResultadoAptidao
```

`ResultadoAptidao` precisa expor:

- `.classe` — `"APTA"` | `"APTA_COM_RESTRICOES"` | `"RESTRITA"` | `"INAPTA_SEM_CORRECAO"` | `"INDETERMINADA"`
- `.grau_final` — inteiro 0–4
- `.fator_determinante` — string
- `.fatores` — iterável de objetos com `.id`, `.grau`, `.rotulo`, `.evidencia`, `.fonte`
- `.derivados` — dict com `v_percent`, `m_percent`, `classe_argila`, `classe_ctc`
- `.alertas`, `.rebaixamento_aplicado`, `.versao_criterios`

> `.derivados` amplia o contrato descrito em `CCAE-implementacao.md` §6, que não o previa. O runner de conformidade o exige.

**IDs canônicos dos fatores** (fixados na v1.1, usados pelo gabarito):

```
F1_acidez  F2_fosforo  F3_potassio  F4_ca_mg  F5_ctc  F6_mo  F7_textura
```

**Função pura:** sem I/O, sem estado global, sem data/hora. Mesma entrada, mesma saída, sempre.

**Desempate do fator determinante:** havendo mais de um fator no grau máximo, vence o de menor índice (F1 antes de F2, e assim por diante).

**Mapeamento grau → classe (CCAE §8.1):**

```
0 NULO       -> APTA
1 LIGEIRO    -> APTA          <-- atenção: 0 E 1 vão para APTA
2 MODERADO   -> APTA_COM_RESTRICOES
3 FORTE      -> RESTRITA
4 MUITO_FORTE-> INAPTA_SEM_CORRECAO
```

O deslocamento dessa tabela em uma casa já causou 63 erros numa tentativa anterior. É o ponto mais fácil de errar do sistema inteiro.

**Falha explícita:** campo obrigatório ausente, valor fora de faixa ou cultura desconhecida retornam `INDETERMINADA`. Nunca imputar média, mediana ou valor típico. Nunca usar fallback de grupo de exigência.

---

## 6. Ordem de trabalho

1. `faixas.py` — utilitário de intervalos com `Decimal`, contemplando as exceções do §4 acima.
2. `dados/criterios_aptidao.json` — todas as tabelas, com campo `_fonte` por bloco.
3. `dados/catalogo_culturas.json` — transcrição do Anexo 2 do Manual (p. 361–366), com `grupo_p` e `grupo_k` **independentes**.
4. `motor/interpretacao.py` — classes de disponibilidade de P e K.
5. **Rodar `validar_anexo1.py`. Precisa passar 32/32 antes de seguir.**
6. `motor/aptidao.py` — fatores e composição.
7. Rodar a conformidade.

O passo 5 não é opcional. Ele valida a camada de interpretação contra dados publicados pelo próprio Manual; não faz sentido construir a composição sobre base não verificada.

---

## 7. Armadilhas conhecidas do catálogo

**`grupo_p` e `grupo_k` divergem em várias culturas.** Nunca derive um do outro, e nunca derive nenhum dos dois a partir do ramo de F1.

| Cultura | grupo_p | grupo_k |
|---|---|---|
| Mandioquinha-salsa | 2 | 1 |
| Tomateiro | 2 | 1 |
| Batata-doce | 3 | 1 |
| Gengibre | 2 | 3 |
| Mandioca | 3 | 2 |

A mandioca é o caso-sentinela: não tem pH de referência (ramo b de F1) mas é grupo 2 em K. Uma regra do tipo "ramo b → grupo 3" acertaria as sete florestais e quebraria nela.

**Sinonímia da Tabela 5.1 vs Anexo 2:** almeirão = Chicória, manjericão = Alfavaca, mirtilo = Mirtileiro, tomate = Tomateiro, palmeira-real = Palmeira real australiana, arroz de sequeiro = Arroz. Implemente como aliases.

**Lacuna real da fonte:** *abobrinha* aparece na Tabela 5.1 com pH de referência 6,0 mas **não tem entrada no Anexo 2**. Deixe fora do catálogo ou retornando `INDETERMINADA`. Não invente grupo. Mesma situação para as consorciações de gramíneas e leguminosas, que a Tabela 5.1 menciona e o Anexo 2 só lista por espécie individual.

---

## 8. Parâmetros configuráveis

Todas as decisões de julgamento do autor vivem em `dados/config_aptidao.json`, nunca embutidas em código:

```json
{
  "REBAIXAMENTO_POR_ACUMULO": false,
  "REBAIXAMENTO_MIN_FATORES": 3,
  "F4_GRAU_MAXIMO": "MODERADO",
  "F5_GRAU_MAXIMO": "MODERADO",
  "F6_GRAU_MAXIMO": "MODERADO",
  "F7_ATIVO": true,
  "MUITO_ALTO_REBAIXA": false,
  "NC_MAX_INCORPORADO_T_HA": 20.0,
  "NC_MAX_SUPERFICIAL_T_HA": 5.0
}
```

O gabarito foi construído com **essa configuração exata**. `REBAIXAMENTO_POR_ACUMULO` em `true` invalida o gabarito — ele existe só para a análise de sensibilidade.

---

## 9. Conjunto de casos

84 casos, 100% gabaritados. 80 entram na métrica de conformidade; 4 são de rejeição de entrada e ficam fora por definição.

| Bloco | N | Cobre |
|---|---|---|
| `anexo1_manual` | 12 | Glebas do Anexo 1; classes de P e K publicadas pelo Manual |
| `fator_determinante` | 21 | 3 por fator, F1 a F7 |
| `fronteira` | 17 | Limiares exatos e ±0,1 |
| `calibracao` | 14 | 20 culturas distintas |
| `cenario_potencial` | 10 | 5 pares ATUAL/POTENCIAL |
| `ramo_b_sem_ph_referencia` | 6 | Culturas sem pH de referência |
| `entrada_invalida` | 4 | Fora das métricas |

**Casos de fronteira construídos com aritmética reversa** — batem no limiar exato e são os que mais quebram implementações:

- `CONF-FR-23`: m% = 30,0 exatos
- `CONF-FR-24`: m% = 50,0 exatos
- `CONF-RB-04`: V% = 40,0 exatos
- `CONF-FR-05` / `CONF-FR-06`: argila 20,0 e 20,1 — **devem produzir resultados diferentes**. Se saírem iguais, o limiar de classe de argila foi aplicado errado.

**Pares deliberados:** `CONF-F2-02` (alho) e `CONF-F2-03` (eucalipto) têm análise idêntica e grupos de exigência distintos.

---

## 10. Decisão em aberto

O CCAE §7.2 diz que, quando a dose de calcário excede o teto operacional, F1 no cenário POTENCIAL "permanece um grau acima de NULO", isto é, LIGEIRO. Mas o §8.1 mapeia LIGEIRO para `APTA` — **a penalidade por inexequibilidade é invisível no resultado**. O caso `CONF-PT-03` (SMP 4,4 → 21,0 t/ha, acima do teto de 20) sai como `APTA`.

**Implemente conforme o CCAE v1.1 está escrito**, e o gabarito reflete isso. A correção é decisão pendente do autor com o orientador, e vira v1.2 com regabarito do PT-03.

---

## 11. Histórico que explica o estado atual

Resumo do que já foi resolvido, para não se refazer:

- **Escopo.** A aptidão deixou de ser hipótese de pesquisa e virou artefato de projeto com verificação de conformidade, porque a hipótese original era circular: o autor definia os critérios, implementava e gerava o gabarito com os mesmos critérios.
- **CCAE.** Criado com o princípio de que nenhum limiar numérico é invenção. Toda faixa rastreia a uma tabela do Manual; só a arquitetura (graus de limitação, fator mínimo) vem de Ramalho Filho e Beek (1995).
- **Ancoragem do mapeamento.** A conversão classe de disponibilidade → grau de limitação usa as faixas de rendimento relativo que o próprio Manual publica (~40%, 40–75%, 75–90%, ≥90%). Não é arbitrária.
- **Gap de catálogo.** As florestais não tinham entrada explícita em `grupo_p`/`grupo_k`. Resolvido pela transcrição do Anexo 2, não por regra de catch-all.
- **Validação externa.** As tabelas de interpretação foram conferidas contra as Tabelas A.2 e A.3 do Anexo 1: **32 de 32 classificações coincidem**.
- **Erro sistemático corrigido.** Uma primeira geração do gabarito deslocou o mapeamento grau → classe em uma casa, errando 63 de 76 casos. Daí o destaque do §5.
- **Conferência.** As 76 avaliações ATUAL foram recalculadas de forma independente; 75 coincidiram. A divergência (`CONF-FR-06`, classe de argila em 20,1) foi corrigida e está registrada no CSV.
- **Casos removidos.** `CONF-PT-06` (tabaco com regime de plantio direto, que é de culturas de grãos — caso malformado) e `CONF-PT-07` (exigia a coluna de pH 6,5 da Tabela 5.2, não transcrita). Consequência: o regime de calagem de frutíferas perenes da Tabela 5.6 não é exercitado por nenhum caso.

---

## 12. Definição de pronto

- [x] `validar_anexo1.py` passa 32/32
- [ ] Conformidade em 100% dos 80 casos, com a configuração baseline
- [ ] Cobertura de ramos de `motor/aptidao.py` em 100% (`coverage.py`)
- [ ] Testes de monotonicidade de P e K, determinismo e integridade do catálogo passando
- [x] Toda divergência encontrada registrada no Apêndice B do CCAE
- [ ] Análise de sensibilidade nas 4 configurações, com distribuição de classes reportada

---

## 13. Estado da integração no repositório (2026-09-09)

> Seção acrescentada na integração. Não faz parte da especificação; registra onde o
> código real difere do handoff e o que ficou bloqueado.

**Onde o contrato do §5 mora.** O repositório já tinha `avaliar_aptidao(analise: AnaliseSolo,
cultura_id, cenario, contexto, trace, dados=None)` — a função do sistema, que recebe análise
já validada, Contexto e Trace porque o laudo exige trilha de inferência (CLAUDE.md) e o
técnico escolhe PRNT e profundidade. O contrato de três argumentos do §5 é a assinatura que
a verificação exercita, e vive ao lado como `avaliar_aptidao_ccae()`, que deriva V%, monta
Contexto com PRNT 100% / 20 cm (a condição em que a Tabela 5.2 publica a dose) e converte
falha de entrada em `INDETERMINADA`. Nenhuma das duas foi mutilada para caber na outra.

**Sinonímia (§7) em duas camadas.** Acento, hífen, underscore e maiúscula são normalização
ortográfica pura e ficam em `siras/dominio/nomes.py`. Só equivalências entre nomes realmente
distintos (mirtilo/mirtileiro, tomate/tomateiro) ficam em `dados/comum/aliases_culturas.json`,
porque essas são julgamento. A busca exata sempre vence a por sinônimo.

**Divergência entre o §5 e o código quanto a fallback.** O §5 diz "nunca usar fallback de
grupo de exigência". `_resolver_grupo_p_ou_k()` tem uma segunda camada que cai em
`grupo_exigencia()` de `motor/adubacao.py`, que inclui um fallback de grãos (ADR 0005, D5.7).
As duas regras se contradizem e a divergência **não foi resolvida** — decisão do autor.

**Bloqueios.** Quatro casos não conformam, todos por lacuna de base ou do gabarito, nenhum
por defeito do motor. Estão registrados em CCAE-v1.1.md, Apêndice B, itens B-1 a B-4.
