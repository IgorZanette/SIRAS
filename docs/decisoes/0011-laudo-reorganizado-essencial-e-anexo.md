# 0011 — O laudo reorganizado em essencial e anexo

- **Status:** aceito
- **Data:** 2026-10-11
- **Contexto:** o laudo de um talhão saía em **5 folhas A4**; o de seis, em **27**. A
  estrutura repetia o documento inteiro por área
- **Afeta:** `siras/relatorio/apresentacao.py`, `siras/web/rotas.py`,
  `siras/web/templates/laudo.html`, `_parciais/laudo_essencial.html` (novo),
  `_parciais/laudo_anexo.html` (novo), `_parciais/laudo_corpo.html` (removido),
  `siras/web/static/css/siras-impressa.css`, `siras-telas.css`
- **Não afeta:** o motor. Nenhuma dose, classe ou grau de limitação mudou — esta decisão
  é inteiramente de apresentação

## O que a medição mostrou

Num laudo de **um** talhão, por seção:

| Seção | % do texto |
|---|---|
| De onde vem cada número | **38%** |
| Qual adubo comprar | **33%** |
| Aptidão edáfica | 15% |
| Cabeçalho e as quatro doses | 8% |
| Interpretação dos atributos | 3% |
| Como aplicar | 3% |

**71% do documento eram as duas seções que são complemento**, e não a recomendação. E
num laudo de **seis** talhões:

- **"Como aplicar" saía seis vezes, idêntica.** Depende do critério de calagem e da
  cultura, que são compartilhados por todas as áreas — duplicação pura.
- **A trilha citava a mesma regra e a mesma fonte seis vezes.** O que varia entre áreas é
  a saída, não a regra.
- **A aptidão trazia duas listas de fatores por talhão** — "na situação atual" e "o que
  permanece depois da correção" —, e o mesmo fator aparecia nas duas, com o mesmo nome e
  a mesma evidência. Doze listas num laudo de seis áreas.
- **Comparar talhões era impossível.** Para saber qual área pedia mais calcário era
  preciso folhear seis blocos iguais.

## A decisão

**Nada foi omitido.** O que era parágrafo repetido virou linha de tabela, e o que era
igual em todas as áreas passou a aparecer uma vez. A estrutura:

```
Cabeçalho
Quadro comparativo dos talhões        ← novo, só com 2+ áreas
Por talhão:  4 doses · interpretação · aptidão
Quantidade total a comprar
──────────────── ANEXO, em folha própria ────────────────
Qual adubo comprar      explicação 1× + tabela por talhão
Como aplicar            1× por documento
De onde vem cada número regras 1× + matriz de saídas
```

### D11.1 — Quadro comparativo

Uma tabela, uma linha por talhão: área, as quatro doses, classe de P, classe de K e
aptidão atual → potencial. Seis áreas cabem em meia página, e a comparação que antes
exigia folhear o documento passa a ser uma leitura de cima para baixo.

Os valores saem do `veredito` já formatado, e não de uma releitura do motor: a tabela e
o cartão de dose nunca podem divergir no arredondamento.

### D11.2 — O anexo abre em folha própria

Decisão do autor. A primeira parte fecha sozinha como laudo entregável, e quem só quer a
recomendação não precisa do resto. Custa uma quebra de página e entrega um documento cuja
primeira folha basta.

### D11.3 — A trilha separa regra de valor

A regra e a fonte no Manual são as mesmas em todas as áreas. A trilha passa a listar cada
par **(regra, fonte)** uma vez, com o que ela decidiu; quando a decisão varia entre
talhões, a saída vai para uma matriz com uma coluna por área.

O par, e não o rótulo sozinho: o mesmo critério citado por fontes diferentes são duas
decisões diferentes. No laudo de seis talhões isso acontece de verdade —
`graos_pd_com_restricoes` aparece uma vez citando a Tab. 5.2 (onde houve dose) e outra
citando só a Tab. 5.3 (onde não houve). Colapsar as duas esconderia um caminho percorrido.

A trilha passou a mostrar o **resumo** da decisão ("limitação moderada", "7,2 t/ha") em
vez da evidência por extenso. A evidência não sumiu: ela está impressa na tabela de
fatores da aptidão e na régua de interpretação, que é onde pertence. O que a trilha tem de
responder continua inteiro — **qual** regra, **o que** decidiu e **em que tabela** do
Manual isso está escrito.

### D11.4 — A aptidão ganhou densidade, e não menos espaço

É uma das propostas centrais do trabalho e **fica no essencial**, por talhão. As duas
listas de fatores viraram **uma tabela com os dois cenários em colunas** — o que, além de
economizar, mostra o que a prosa não mostrava: por fator, o que a recomendação resolve e o
que permanece, que é a pergunta que os dois cenários existem para responder (CCAE §7).

Os fatores sem limitação em nenhum dos cenários saem da tabela e viram uma linha de
resumo: sete linhas dizendo "Nula → Nula" ocupavam espaço para informar que não há o que
informar.

A ressalva de escopo — relevo, clima e erosão fora da avaliação — passou a aparecer uma
vez: é propriedade do método, não da área analisada.

### D11.5 — Densidade só na folha impressa

`siras-impressa.css` ganhou escala, espaçamento e grade próprios. **A tela não mudou**: lá
a rolagem é de graça e a folha não é. Entraram também `break-inside: avoid` nos cartões,
linhas de tabela e passos da trilha — meia régua numa página e meia na outra não se lê.

Dois cenários de aptidão passaram a ficar lado a lado também no papel. A consulta de 720px
da folha de tela os empilhava ali, porque a largura útil de uma A4 retrato cabe dentro
dela — era meia página a mais **por talhão**.

## Resultado

Medido em caracteres de texto do documento:

| | Antes | Depois | |
|---|---|---|---|
| 1 talhão | 7.953 | 6.111 | −23% |
| 2 talhões | 14.921 | 9.290 | −38% |
| 4 talhões | 26.115 | 14.203 | −46% |
| 6 talhões | 42.623 | 19.344 | **−55%** |

O texto é um indicador parcial: os ganhos de `siras-impressa.css` são de altura, e não
aparecem nesta contagem. **A contagem de folhas tem de ser conferida no navegador**, com
Ctrl+P sobre a versão impressa.

A redução cresce com o número de talhões, que é o comportamento desejado: o que foi
atacado era a repetição, e ela crescia linearmente.

## O que NÃO foi feito, e por quê

- **A aptidão não foi para o anexo.** É uma das propostas centrais do trabalho; tratá-la
  como complemento contradiria o que o artigo afirma sobre ela.
- **Nenhum dos três caminhos do adubo saiu.** A ADR 0009 argumenta que indicar um só
  seria fingir uma certeza que o mercado não tem. Os três continuam, em colunas.
- **Nenhum passo do Trace foi filtrado.** O `CLAUDE.md` exige que toda decisão do motor
  deixe rastro, e a exigência continua cumprida.
