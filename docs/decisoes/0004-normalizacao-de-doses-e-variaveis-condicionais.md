# 0004 — Normalização de doses, variáveis condicionais e classes de matéria orgânica

- **Status:** aceito
- **Data:** 2026-08-22
- **Contexto:** etapas S3 (hortaliças, tubérculos, cana, tabaco) e S4 (frutíferas, erva-mate)
- **Substitui/complementa:** 0002 (políticas do motor), 0003 (se aplicável)

## Contexto

A base de conhecimento das etapas S3 e S4 trouxe três problemas que não existiam no grupo de
grãos e que afetam simultaneamente o modelo de dados, o motor de inferência e o critério de
aceitação da hipótese H1.1.

1. Nem toda dose do Manual é um escalar. Há faixas (alcachofra: 180–240 kg de N/ha; tabaco
   Virgínia: 160–180) e há limites superiores, grafados `≤` (batata com MO > 5,0%: até 80 kg
   de N/ha). O critério de concordância da Seção 4.4.1 fala em coincidência de valores, o que
   não tem significado definido para esses dois casos.
2. Algumas culturas exigem variáveis que não vêm da análise de solo: ciclo e produtividade
   (cana), tipo (tabaco), fase (aspargo, frutíferas, erva-mate), tipo de uva (videira), manejo
   do galho grosso e massa verde (erva-mate).
3. O tabaco usa seis faixas de matéria orgânica, e não as três usadas por todas as demais
   culturas.

## Decisão

### D4.1 — Normalização em intervalo, apenas na comparação

Toda dose passa a ter uma projeção canônica em intervalo fechado `[mín, máx]`:

| Forma no Manual | Representação no JSON | Projeção |
|---|---|---|
| valor exato `120` | `{"valor": 120}` | `[120, 120]` |
| faixa `180 – 240` | `{"min": 180, "max": 240}` | `[180, 240]` |
| limite `≤ 80` | `{"valor": 80, "qualificador": "ate"}` | `[0, 80]` |

A projeção é implementada como `para_intervalo(dose) -> (min, max)` e usada **somente** na
comparação com o oráculo. O domínio e o laudo preservam a forma original.

**Justificativa da ressalva.** `[0, 80]` e `≤ 80` não são equivalentes para o leitor: o
primeiro sugere indiferença entre zero e 80, o segundo é uma instrução de teto. Um laudo que
imprimisse "0 a 80 kg de N/ha" seria tecnicamente ambíguo e, pior, indistinguível de uma faixa
real cujo limite inferior fosse zero — situação que de fato ocorre (mirtileiro, classe Muito
alto, `0`). Normalizar para comparar e preservar para comunicar resolve os dois usos sem perda.

**Consequência para a Seção 4.4.1.** A redação passa a ser:

> As doses recomendadas nem sempre são valores pontuais: o Manual expressa parte das
> recomendações como faixas e parte como limites superiores. Para permitir comparação objetiva,
> toda dose — tanto a gerada pelo SIRAS quanto a de referência — é normalizada em um intervalo
> fechado [mín, máx]: valores pontuais tornam-se intervalos degenerados [d, d]; faixas preservam
> seus extremos; limites superiores tornam-se [0, d]. Um caso de teste é considerado concordante
> quando, para todos os nutrientes avaliados, o intervalo emitido pelo sistema é igual ao
> intervalo de referência, comparados após o arredondamento definido para a saída. A
> normalização aplica-se apenas à comparação; o laudo apresenta a recomendação em sua forma
> original.

A necessidade de calagem permanece escalar em t/ha e continua regida pelas políticas do
ADR 0002 (arredondamento, teto de 5 t/ha, dose zero com motivo enumerado). A Seção 4.4.1
precisa, portanto, de dois parágrafos: um para calagem e um para adubação.

### D4.2 — Ponto em aberto: ajuste de rendimento sobre dose com teto

O Manual manda acrescentar quantidade por tonelada adicional acima de um limiar (cebola,
batata, tomate, ameixeira, pessegueiro). Quando a dose de base é um teto — cebola na classe
Muito alto é `≤ 80` kg de K₂O/ha, e acima de 30 t/ha soma-se 3 kg/t — não está definido se o
resultado é `[0, 80 + acréscimo]` ou `[acréscimo, 80 + acréscimo]`.

**Decisão provisória:** somar apenas ao limite superior, preservando o zero como limite
inferior — isto é, `≤ 80` com acréscimo de 30 vira `≤ 110`. O motor registra no *trace* que
houve ajuste sobre uma dose com qualificador.

**Pendência:** confirmar com o orientador antes de calcular o oráculo dos casos afetados. A
ambiguidade é do Manual, não da implementação, e deve ser registrada como tal na monografia.

### D4.3 — Variáveis condicionais dirigidas pelos dados

O `Contexto` ganha campos opcionais, e **cada cultura declara** no JSON, no nó
`variavel_adicional`, quais são obrigatórios para ela:

```json
"variavel_adicional": { "campo": "tipo", "valores": ["virginia", "burley"], "obrigatorio": true }
```

O formulário renderiza a partir desse nó. **É proibido codificar `if cultura == "cana"` no
template ou no motor.** Aspargo (fase), cana (ciclo + produtividade), tabaco (tipo), videira
(tipo de uva), frutíferas (fase + ano do pomar + produtividade) e erva-mate (programa, fase,
manejo do galho grosso, massa verde) são todos casos da mesma regra; tratar dois deles como
exceção obriga a reescrever o formulário na etapa seguinte.

Notas:

- `expectativa_rendimento_t_ha` é um campo **único e compartilhado**, não um campo da cana:
  já é exigido por cebola, batata, tomate, grãos, frutíferas e mirtileiro. O que varia é o
  modo de uso — indexação de coluna (cana, mirtileiro, morangueiro) ou incremento linear em
  kg por tonelada adicional (cebola, batata, tomate) —, e isso é declarado no JSON.
- A base da estimativa varia (colmos, bulbos, frutos, massa verde) e deve ser declarada no
  JSON para compor o rótulo do formulário.
- As faixas de produtividade da cana **dependem do ciclo** (`<90/90–120/>120` para cana-planta,
  `<60/60–90/>90` para cana-soca): a validação do campo só é possível após o ciclo ser informado.

### D4.4 — Classes de MO resolvidas por referência, sem *fallback*

O motor não codifica as três faixas tradicionais. Cada bloco de dose declara
`"classes_mo": "<nome>"`, resolvido contra o nó `classes_mo` do cabeçalho do arquivo. Se o nome
não resolver, o motor **levanta erro** — nunca cai no `padrao`.

**Justificativa.** Um *fallback* silencioso produziria exatamente o bug que o override existe
para evitar: tabaco com MO de 1,5% cairia na faixa "≤ 2,5" e receberia a dose de outra
cultura, sem qualquer sinal de erro.

Teste de invariante associado: para cada cultura, o número de chaves em `doses` deve ser igual
ao número de faixas resolvidas.

### D4.5 — Fronteiras das faixas de MO

O Manual imprime "≤ 2,5" e "2,6 – 5,0", deixando o intervalo aberto `2,5 < MO < 2,6` sem classe.
Um laudo com MO = 2,55% é perfeitamente possível.

**Decisão:** as faixas são codificadas como semiabertas e contíguas — `(null, 2.5]`,
`(2.5, 5.0]`, `(5.0, null)` —, de modo que 2,55% cai na segunda faixa. O mesmo critério vale
para os cinco intervalos análogos das seis faixas do tabaco.

Trata-se de **interpretação do SIRAS, não do Manual**, e deve ser declarada como tal na
monografia.

### D4.6 — Escopo da adubação de manutenção das frutíferas

Três das dezessete frutíferas — ameixeira, macieira e pessegueiro/nectarineira — têm a
adubação de manutenção indexada pelo **teor foliar** do nutriente, e a macieira depende ainda
do crescimento dos ramos em cm. Nenhuma dessas variáveis vem de uma análise de solo, e o
Manual não oferece, para essas espécies, correspondência entre classes de solo e classes
foliares.

**Decisão (confirmada pelo autor em 2026-08-23, após reconferir as notas de rodapé das
três espécies, p. 196-197, 207-208, 224-225):** para essas três espécies, o SIRAS entrega
pré-plantio e crescimento normalmente e, na manutenção, informa explicitamente que a
recomendação exige análise foliar, indicando a tabela do Manual a consultar. O campo
`manutencao.implementado_no_siras` no JSON dirige esse comportamento — a regra é **dado,
não código**. É uma limitação de **fase**, não de cultura: as 61 culturas do escopo
continuam 61 (`siras/motor/adubacao.py::calcular_adubacao_frutiferas`, `fase="manutencao"`
levanta `NotImplementedError` só para essas três, com a mensagem citando o motivo).

A videira é o caso oposto e por isso está implementada (2026-08-23): suas tabelas também
são indexadas por classe de tecido, mas o próprio Manual declara a correspondência a
partir do solo na ausência de análise foliar — MO para o N, classe de P no solo para o P
(fontes **diferentes**: não deriva uma da outra — ver caso ADU-19,
`testes/unidade/test_adubacao_grupos.py::TestFrutiferasBespoke`, que usa o mesmo laudo
para produzir classes de tecido diferentes de N e de P de propósito).

**Pendência resolvida:** o Manual **não** declara correspondência solo-tecido para o **K
da videira** — a nota da p. 231 cobre apenas o P. Decisão do autor: **não** assumir a
correspondência do P por analogia. A p. 230 alerta que doses de K acima das tabeladas
favorecem a elevação do pH do vinho, sobretudo em tintos — extrapolar sem respaldo textual
arrisca justamente a qualidade do produto, não só a adubação. `calcular_adubacao_frutiferas`
sempre retorna `k2o=None` para a videira, com uma explicação e o encaminhamento às Tabelas
6.5.18 (peciolos) e 6.5.19 (folhas), nunca uma dose estimada.

### D4.7 — Manutenção bespoke implementada (amoreira-preta, mirtileiro, morangueiro, nogueira-pecã)

As quatro frutíferas restantes com manutenção fora do formato genérico
(`taxa_por_tonelada_estimada`) foram implementadas em 2026-08-23, cada uma com sua própria
leitura direta em `calcular_adubacao_frutiferas` (não pelo motor de leitura genérico
`_navegar`/`_calcular_pk_generico`, que não cobre colunas nomeadas nem eixos assimétricos):

- **Amoreira-preta**: N indexado por MO × "coluna" — e a coluna não é um índice ordinal do
  ano: `ano_1` é sempre zero (ano de plantio), `ano_2` e `ano_3_mais` têm sub-colunas por
  faixa de produtividade próprias. P/K por classe de teor × produtividade (faixas
  diferentes das de N).
- **Mirtileiro**: `crescimento_e_manutencao_unificados` — a cultura não tem fase de
  crescimento separada; chamar direto com `fase="manutencao"` (chamar com
  `fase="crescimento"` levanta `ErroAdubacao` apontando para `manutencao`). N e P/K por
  3 faixas de produtividade compartilhadas.
- **Morangueiro**: mesma unificação de fase. N **ignora a MO de propósito** (p. 214: o
  substrato orgânico do sistema de produção contribui pouco em N) — indexado só por
  produtividade. P é uma única coluna por classe (sem produtividade); só K cruza classe ×
  produtividade. É também a única tabela do grupo com platô entre Alto e Muito alto (doses
  iguais) — o teste de monotonicidade genérico (`validar_adubacao_por_grupo`) já tolera
  não-decrescente, não exige estritamente decrescente, então o dado correto não é rejeitado.
- **Nogueira-pecã**: N por produtividade simples (faixas fracionárias, 1,5/3,0 — únicas do
  grupo); P/K por taxa/tonelada (mesmo mecanismo de D4.1, `_dose_taxa_por_tonelada`),
  produzindo os únicos valores não inteiros da base (9,2 e 9,6). Tem um ajuste percentual
  documentado no Manual (redução de 50% do N em "ano de alternância de produtividade" para
  nove cultivares nomeadas, p. 217) implementado como parâmetro opcional
  `ano_de_alternancia`, diferente da política geral de D4.2/ajustes genéricos (que seguem
  fora de escopo): aqui o valor (50%) é dado explicitamente pelo Manual, não uma
  extrapolação.

**ADU-15 (amoreira-preta) — descasamento resolvido pelo autor em 2026-08-23, confirmado
na p. 199.** O rascunho original tinha entrada com argila 45% (classe de solo 2, onde
P = 15,0 mg/dm³ cai em Alto) e um P₂O₅ esperado de 84 (valor da classe Médio, que só bate
com argila 32%). Decisão: manter argila 45% e corrigir o esperado para **70** (linha Alto,
coluna de produtividade "10-15", Tab. 6.4/p. 199) — não baixar a argila para 32%, pelos
dois motivos que o autor deu: (a) é a única cobertura da base para a classe de argila 2
(faixa 41-60%, Tabela 6.4); baixar para 32% eliminaria essa faixa da suíte de testes; (b)
com 45%, P classifica Alto e K (mesmo caso) classifica Médio — as duas classes divergem no
mesmo laudo, o que expõe um motor que classifique P e K numa única chamada e propague
acidentalmente a classe de um nutriente para o outro. Com 32% ambos ficariam em Médio e
essa detecção desapareceria. Caso final: `n=117, p2o5=70, k2o=171` (N e K não mudam — a
classe de argila não entra em nenhum dos dois cálculos). Já integrado como oráculo em
`test_adubacao_grupos.py::TestFrutiferasBespoke` e em
`testes/casos/casos_recomendacao.json` (ADU-15).

## Consequências

- A Seção 4.4.1 da proposta precisa ser reescrita (dois parágrafos: calagem e adubação).
- A Seção 4.7 (limitações) ganha um item: a manutenção de três frutíferas fica fora do alcance
  de uma ferramenta baseada em análise de solo.
- O `Contexto` ganha campos opcionais; a validação de obrigatoriedade passa a ser dirigida
  pelo JSON da cultura.
- D4.2 (ajuste de rendimento sobre dose com teto) segue como pendência técnica antes do
  cálculo do oráculo. D4.6 (K da videira) foi resolvida em 2026-08-23.
