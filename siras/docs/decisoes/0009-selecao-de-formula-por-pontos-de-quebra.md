# 0009 — Seleção da formulação NPK por pontos de quebra, em três caminhos

- **Status:** aceito
- **Data:** 2026-10-10
- **Contexto:** plano de seleção de formulação v2, elaborado pelo autor em 10/10/2026 a
  partir do §8.3 do Manual e da constatação de que **não existe catálogo oficial e único
  de fórmulas comercializadas no Brasil**
- **Revoga:** a [ADR 0008](0008-escolha-de-formula-pelo-metodo-do-manual.md) no que diz
  respeito à regra de dose, à função de ordenação e ao desempate. Permanecem da 0008 a
  separação entre método (do Manual) e catálogo (de mercado), a ausência de preço no
  ranking e a dose sem arredondamento no motor
- **Revoga também:** o que restava dos itens 5 e 6 da [ADR 0007](0007-indicacao-de-formulacao-do-adubo.md)

## Por que a terceira versão em dezessete dias

Vale registrar a progressão, porque ela é o argumento e não um acidente de percurso:

| | Regra de dose | Procedência |
|---|---|---|
| **0007** (24/09) | maior cobertura entre P e K | critério do autor |
| **0008** (10/10, manhã) | nutriente mais deficiente no solo | método do Manual, §8.3 |
| **0009** (10/10) | menor custo entre os pontos de quebra | ótimo demonstrável, que **contém** a regra do Manual |

A 0008 trocou um critério do autor por um método publicado --- ganho de rastreabilidade.
A 0009 observa que a regra do Manual é **um** dos dois candidatos possíveis e que avaliar
os dois nunca piora o resultado. Volta a haver decisão do autor, mas agora com
demonstração matemática por trás, o que é posição mais forte do que a da 0008.

## O problema que motivou a v2

Levantamento do autor em 10/10/2026: **não existe lista oficial de fórmulas
comercializadas**. O MAPA registra milhares de produtos, boa parte das fórmulas é feita
sob encomenda, e fabricantes consultados sequer publicam as garantias. Um sistema que
dependa de um catálogo fechado responde mal quando a fórmula indicada não existe na
revenda do usuário --- que é o caso comum.

A resposta é não depender de catálogo nenhum: o sistema entrega **três respostas
complementares** e deixa a escolha com quem compra.

| Caminho | O que o laudo mostra | Por que entra |
|---|---|---|
| **A. Fórmula ideal** | A proporção exata da recomendação e três fórmulas múltiplas dela | Método literal do Manual, p. 311; serve para pedir sob encomenda |
| **B. Melhores do catálogo** | As três melhores fórmulas existentes, com dose, complementos e excesso | O produto que se encontra na revenda |
| **C. Mistura de simples** | Doses de ureia, superfosfato triplo e cloreto de potássio | Sempre exata e sempre disponível; é a régua das outras duas |

**Argumento para a banca:** o SIRAS não depende de uma lista oficial que não existe. Ele
calcula a fórmula ideal, compara com o que o mercado oferece e mostra o custo nutricional
de cada desvio.

## Decisões

Prioridade **E** = essencial para a defesa; **D** = desejável. Todas as de prioridade D
foram implementadas, por decisão do autor em 10/10/2026, por mexerem na interface e o
aplicativo congelar em 12/10.

| ID | Pri. | Decisão | Origem |
|---|---|---|---|
| D1 | E | A dose de cada fórmula é escolhida entre os **pontos de quebra** `rᵢ·100/fᵢ`, apenas para P₂O₅ e K₂O | Manual p. 311 + convexidade (abaixo) |
| D2 | E | N não é âncora: o N da fórmula é descontado do N total e o saldo vai para **cobertura com ureia** | Manual p. 311 |
| D3 | E | Leguminosas: `n_total = 0`, e todo N da fórmula conta como excesso | Manual (fixação biológica) |
| D4 | E | Pesos: `W_EXC` = 1,0/kg · `W_FALTA` = 0,2/kg · `W_OP` = 10 por produto de complemento | **Autor** |
| D5 | E | A ureia de cobertura não conta como operação extra: a cobertura existe em qualquer opção | Autor |
| D6 | E | Complementos: superfosfato triplo (P), cloreto de potássio (K), ureia (N) | Manual, Tab. 8.4 |
| D7 | E | A saída traz sempre os três caminhos, A, B e C | Autor |
| D8 | E | Sem preço; o custo financeiro fica como trabalho futuro | Escopo |
| D9 | E | **Desempate** entre fórmulas de mesmo custo: menor **massa total aplicada** (fórmula + complementos + ureia), depois menor dose, depois id | Autor; Manual p. 310, concentração reduz frete |
| D10 | E | **Fórmula ideal:** escalar a recomendação para que o maior entre P₂O₅ e K₂O valha `T ∈ {18, 24, 30}`, arredondando ao inteiro | Manual p. 311 |
| D11 | D | O usuário pode **cadastrar a fórmula que tem**; ela entra no ranking marcada como informada por ele | Autor |
| D12 | D | **Avisos fixos** no laudo: critério sem preço, enxofre em fórmulas concentradas, compatibilidade da mistura | Manual p. 310, 311 e Fig. 8.2 |

Os pesos de D4 e os alvos `T` de D10 são constantes nomeadas num único lugar do código,
e **não** são configuráveis pela interface: são parâmetros do método, não preferência de
uso.

### A fragilidade de D4, declarada

`W_EXC` e `W_FALTA` são por quilo; `W_OP` é uma constante. A função de custo, portanto,
**mistura unidades**, e o que ela afirma na prática é: *uma operação de campo a mais custa
o mesmo que 10 kg de nutriente desperdiçado*. Não há fonte que gradue essa troca --- é
julgamento do autor, e é o ponto mais atacável do método.

Duas coisas atenuam. A primeira é que `W_FALTA` ser menor que `W_EXC` tem razão
agronômica: o que falta ainda pode ser corrigido com fonte simples, enquanto o que sobra
já foi comprado e aplicado. A segunda é que os três pesos são constantes nomeadas: mudar
a troca é mudar um número, e o efeito sobre o ranking é mensurável rodando a suíte.

## A regra de seleção (caminho B)

Para uma fórmula de teores `f = (f_N, f_P, f_K)` em % e dose `d` em kg/ha, o fornecido de
cada nutriente é `d·fᵢ/100`. O custo é

```
custo(d) = W_EXC   · Σ_{i ∈ {N,P,K}} max(0, d·fᵢ/100 − rᵢ)
         + W_FALTA · Σ_{i ∈ {P,K}}   max(0, rᵢ − d·fᵢ/100)
         + W_OP    · (nº de complementos de P e K com dose ≥ 0,5 kg/ha)
```

Os dois primeiros termos são **lineares por partes e convexos** em `d`, e soma de convexas
é convexa. O mínimo de uma função linear por partes convexa está em um ponto de quebra.
Basta, portanto, avaliar

```
d ∈ { r_P · 100 / f_P ,  r_K · 100 / f_K }
```

e ficar com o de menor custo. O termo `W_OP` é constante por trechos e é avaliado nos
mesmos pontos.

**A regra do Manual é um desses dois pontos.** O SIRAS avalia os dois e escolhe pelo
critério declarado, de modo que o resultado **nunca é pior** que o do Manual sob esse
critério --- afirmação verificada por propriedade sobre grade, no teste T8, e não por
argumento.

**Mistura de simples (caminho C):** `TSP = r_P·100/41`, `KCl = r_K·100/58` e
`ureia = r_N·100/45`, com as garantias da Tab. 8.4.

## A fórmula ideal (caminho A)

1. Proporção básica: dividir o N **de plantio**, o P₂O₅ e o K₂O pelo maior entre P₂O₅ e K₂O.
2. Para cada `T ∈ {18, 24, 30}`: garantias = proporção × `T`, arredondadas ao inteiro, meio
   para cima.
3. Dose = (dose do nutriente de maior valor) × 100 / garantia correspondente.
4. Saldo de N (`n_total − n_fornecido`) vai para cobertura com ureia.

Com N de plantio 10, P₂O₅ 120 e K₂O 80, a regra produz **02-18-12 (667 kg/ha),
02-24-16 (500) e 03-30-20 (400)** --- exatamente as três fórmulas do exemplo do Manual,
com as doses que ele publica. A soma das garantias é ≥ 18 por construção, já que o maior
teor vale `T`, o que atende o mínimo legal da IN 39/2018 para ternárias.

### O N de plantio não está na base, e por isso é entrada do usuário

O Manual separa o N de semeadura do N de cobertura, mas a base de conhecimento do SIRAS
**guarda o total**: `graos_adubacao_n.json` registra a dose com a nota "Semeadura +
cobertura", e as hortaliças trazem o parcelamento apenas em prosa ("50% a lanço na
semeadura e o restante em cobertura"). Derivar um número a partir dessa prosa seria
inferência agronômica do sistema, que o `CLAUDE.md` proíbe.

**Decisão:** `n_plantio` é campo **opcional do formulário**. Informado, a fórmula ideal
sai ternária. Ausente, vale 0, a fórmula ideal sai binária (P-K), todo o N vai para
cobertura, e o laudo e a trilha declaram que foi assim. Uma fórmula binária tem mínimo
legal de 15%, igualmente atendido por construção.

Consequência metodológica que precisa estar no artigo: **o exemplo do Manual só é
reproduzido quando o usuário informa o N de plantio.** O teste T11 passa esse valor
explicitamente, e é isso que ele verifica.

### Limite conhecido da fórmula ideal

A regra **não verifica se a fórmula é fabricável** com as matérias-primas disponíveis ---
cada fonte traz nutrientes acoplados, como o N que vem junto do MAP. Por isso o laudo a
apresenta como *referência para pedido sob encomenda*, e não como produto garantido. O
arredondamento ao inteiro também pode desviar o nutriente secundário em poucos kg/ha, e
o laudo mostra esse desvio.

## Consequências

- O laudo ganha três blocos em lugar de um, mais os avisos de D12. É mais texto numa
  seção já densa, e o peso disso na legibilidade é justamente o que o teste de
  usabilidade vai medir --- a heurística 8 trata de excesso de informação.
- `Contexto` ganha dois campos opcionais: `n_plantio` e `formulas_usuario`.
- O catálogo deixa de ser o único caminho: com ele vazio, A e C continuam funcionando, e
  só B desaparece. O sistema fica menos dependente de um dado que não é normativo.
- A trilha registra, por fórmula avaliada, os pontos de quebra, o custo em cada um, a
  dose escolhida e o motivo do desempate.

## Verificação

Dezessete casos, T1 a T17, em `testes/unidade/test_formulacao.py`. Os mais importantes:

- **T11** reproduz as três fórmulas e as três doses do exemplo do Manual, p. 311 ---
  oráculo externo, não escrito por nós;
- **T8** é teste de propriedade sobre grade: o custo do ótimo é sempre menor ou igual ao
  custo da âncora do Manual. É o que sustenta a afirmação central desta ADR;
- **T9**, também sobre grade: fórmula mais complementos nunca deixam faltar P ou K;
- **T3** foi escrito **antes** do código, por determinação do plano, e guarda a regressão
  da proporção 60:120;
- **T14** fixa o desempate por massa total de D9.

As propriedades usam `pytest.mark.parametrize` sobre a grade, e não `hypothesis`: o
`CLAUDE.md` restringe as dependências.

## Fora de escopo, para trabalhos futuros

- **Custo financeiro:** trocar os pesos por R$/kg transforma o problema em programação
  linear de custo mínimo, que é o critério literal do Manual, p. 310. O modelo já comporta.
- **Fabricabilidade** da fórmula ideal, verificando se as garantias cabem em 100 kg com as
  matérias-primas disponíveis.
- **Teor declarado dos simples**, usando o do produto real (ureia 46%, por exemplo) em vez
  do mínimo legal.
- **Fórmulas de cobertura**, escolhendo um NK quando a cultura parcela o potássio.
- **Enxofre como critério de escolha**, e não apenas como aviso.
