# 0008 — Escolha da fórmula NPK pelo método do Manual, §8.3

- **Status:** aceito
- **Data:** 2026-10-10
- **Contexto:** levantamento das fontes de formulações feito pelo autor em 10/10/2026, que
  localizou no Cap. 8 do Manual um **procedimento publicado** para converter a recomendação
  em fórmula comercial
- **Revoga:** os itens **5 (critério de dose)** e **6 (critério de escolha)** da
  [ADR 0007](0007-indicacao-de-formulacao-do-adubo.md). Os demais itens da 0007 — separação
  entre norma e mercado, `_fonte` por entrada, catálogo vazio não ser erro, indicação dentro
  do laudo e preço fora, dose sem arredondamento no motor — **permanecem em vigor**

## Por que uma ADR nova

A 0007 resolveu o problema certo com um critério do autor. Em 24/09/2026 não havia método
publicado à vista, e a escolha foi declarada como escolha: dose pela maior cobertura entre
P e K, ranking pelo menor excesso total.

O levantamento de 10/10/2026 mostrou que **o Manual publica o procedimento** — §8.3,
p. 310-311 — e ainda o ilustra com um exemplo numérico resolvido. Isso muda o estatuto da
decisão: deixa de ser escolha do autor e passa a ser transcrição de método, que é
exatamente o que o princípio P1 do CCAE exige do resto do sistema.

Trocar um critério defensável por um rastreável é ganho de robustez na banca. Manter o
critério do autor quando o Manual tem um seria a escolha difícil de justificar.

## O método do Manual (§8.3, p. 310-311)

1. a fórmula adequada é **múltipla da proporção** da recomendação (o Manual deriva
   `10-120-80 → 1:12:8` e lista `02-18-12`, `02-24-16`, `03-30-20`);
2. não havendo fórmula exata, a dose se ajusta ao **nutriente mais deficiente no solo**,
   que passa a ser atendido exatamente;
3. o N que a fórmula traz é descontado do N total, e o **saldo vai para cobertura**;
4. entre fórmulas adequadas, preferir a de **menor custo por unidade de NPK**, incluindo
   transporte e aplicação.

## O que mudou no comportamento

| | ADR 0007 (24/09) | ADR 0008 (10/10) |
|---|---|---|
| Dose | maior entre a que cobre P e a que cobre K — nenhum fica devendo | ancorada no nutriente mais deficiente, que é atendido na medida |
| Falta | impossível por construção | possível, e vira **complemento** com fertilizante simples |
| Sobra | único critério de ranking | entra no desvio, com o mesmo peso da falta |
| Ranking | menor excesso de P+K; desempate pela menor falta de N | menor desvio relativo; desempate pela fórmula mais concentrada |
| N | fora da dose, falta declarada | fora da dose, **saldo vai para cobertura com ureia** |
| Rastreabilidade | critério do autor | método do Manual |

A diferença prática é grande: a regra antiga **nunca** deixava faltar nutriente, e por isso
sempre sobrava do outro. A do Manual aceita faltar e resolve a falta com fonte simples —
que é o que se faz no campo, e é mais barato do que aplicar o dobro de uma fórmula para
acertar um nutriente só.

## Decisões do autor que permanecem

O método do Manual não cobre tudo. Estas são escolhas declaradas, isoladas em constantes
de `siras/motor/formulacao.py`, no espírito do princípio P3 do CCAE:

| # | Decisão | Fundamentação | Fragilidade |
|---|---|---|---|
| D1 | **Empate de classe** entre P e K: ancora no de maior dose recomendada | O Manual diz "mais deficiente no solo" e não trata o empate. A maior dose é o maior risco de erro absoluto | Baixa |
| D2 | **Classe ausente** (fases de frutífera que não dosam por classe): ancora na maior dose e **declara** que ancorou assim | Sem classe não há como saber qual está mais deficiente. A alternativa — não indicar — tiraria a seção de um grupo inteiro de culturas. O laudo diz que a âncora é leitura do SIRAS | Média |
| D3 | **Falta e excesso pesam igual** no desvio | Falta exige uma operação a mais; excesso é adubo pago e não aproveitado. Nenhuma fonte gradua os dois | Média |
| D4 | **Fontes de complemento:** superfosfato triplo (P), cloreto de potássio (K), ureia (N em cobertura) | As mais concentradas de cada nutriente na Tab. 8.4, p. 304: menos massa transportada | Baixa |
| D5 | **Complemento mínimo de 0,5 kg/ha** | Abaixo disso não compensa uma passada de máquina | Baixa |
| D6 | **Desempate pela fórmula mais concentrada** | O Manual observa na p. 310 que a concentração reduz frete e aplicação | Baixa |
| D7 | **O laudo filtra o catálogo por `uso = plantio`** | O laudo publica a recomendação de implantação; o N de cobertura sai nomeado, como complemento | Baixa |
| D8 | **Leguminosas:** o N da fórmula conta como excesso | Fiel ao Manual, que não recomenda adubação nitrogenada para leguminosas (fixação biológica). Penaliza fórmulas ricas em N na soja | **A revisitar** — ver abaixo |

### Sobre a D8, que o autor precisa decidir com o orientador

Com `N = 0` na recomendação, toda fórmula com nitrogênio acumula excesso e cai no ranking.
O efeito é que, para soja, o sistema prefere fórmulas pobres em N — o que é **fiel ao
Manual** e **diverge da prática corrente**, em que a 05-20-20 é comum.

A penalidade é proporcional, não eliminatória: o excesso de N entra no desvio dividido por
`P2O5 + K2O`, de modo que 13 kg/ha de N a mais sobre um alvo de 200 pesa 6,5%. Uma fórmula
assim ainda pode vencer se acertar melhor P e K.

**O SIRAS fica com a leitura fiel ao Manual**, e o laudo explica o excesso em vez de
escondê-lo. Se o orientador entender que a prática de starter em leguminosa deve ser
tolerada, a mudança é de uma linha — e precisa virar decisão declarada aqui, não ajuste
silencioso no peso.

## O que o SIRAS não faz do método

**O passo 4 — escolher pelo menor custo por unidade de NPK.** O SIRAS não tem preços: eles
são de quem compra, mudam por revenda e por semana, e colocá-los no laudo poria número
comercial num documento técnico assinado (a mesma linha da ADR 0007, item 7).

O ranking é, portanto, **nutricional**. O laudo diz isso com todas as letras, e a
comparação de custo continua na calculadora, com os preços que a pessoa informar. A
monografia precisa declarar essa diferença entre o método publicado e o implementado.

## Verificação

O mais forte é oráculo externo, e não escrito por nós: o Manual publica, na p. 311, as
doses das três fórmulas que atendem a recomendação `10-120-80` — 667, 500 e 400 kg/ha.
`TestExemploDoManual`, em `testes/unidade/test_formulacao.py`, reproduz as três.

Um achado do catálogo que vale para a defesa: para essa mesma recomendação, o motor
encontra também a **08-30-20**, citada por produtores do RS, PR e MS nos painéis da Embrapa
Trigo. Ela tem a mesma proporção 3:2 e atende P e K exatamente — é uma fórmula **real de
mercado** que o Manual não cita. O método mais o catálogo acham o que cada um sozinho não
acharia.

Demais testes: âncora por classe, empate, fallback sem classe, falta virando complemento,
sobra declarada, N de cobertura, leguminosa, ordenação, determinismo, catálogo vazio e as
invariantes dos arquivos reais (`testes/integracao/test_laudo_formulacao.py`).
