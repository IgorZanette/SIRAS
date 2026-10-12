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

### D11.2 — O anexo abre em folha própria ~~(revertida — ver abaixo)~~

Decisão do autor. A primeira parte fecha sozinha como laudo entregável, e quem só quer a
recomendação não precisa do resto. Custa uma quebra de página e entrega um documento cuja
primeira folha basta.

> **Revertida em 11/10/2026, depois de ver o PDF.** Num laudo de um talhão o essencial não
> enche a folha, e a quebra deixava **60% dela em branco** antes de o anexo começar de
> supetão na seguinte. O anexo voltou ao fluxo contínuo.
>
> A fronteira não se perde: a regra horizontal e o rótulo "ANEXO" já a marcam, e são
> separação visual que não gasta folha. O que o rótulo precisa é não ficar órfão no pé de
> uma página, e disso cuida `break-after: avoid` no `.anexo__cab`.
>
> Vale o registro de como a decisão se desfez, porque é o padrão destas três rodadas: ela
> era razoável no papel — "a primeira folha basta" continua sendo um bom princípio — e só
> ficou errada quando houve um PDF para olhar. Nenhuma das três correções de paginação
> saiu de raciocínio; as três saíram de um documento impresso.

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

## Adendo de 11/10/2026 — o que um PDF real mostrou

O autor imprimiu dois laudos e o resultado contradisse a estimativa: **cebola em 4 folhas,
milho de seis talhões em 18**. A inspeção dos PDFs encontrou quatro defeitos, três deles
na mesma causa.

### A causa: as regras estavam na folha errada

`siras-impressa.css` só é carregado em `/analise/laudo?formato=impressa`. O botão
**"Salvar em PDF" chama `window.print()` sobre o laudo EM CORES** — que é o caminho que
quase todo mundo usa, e o que o autor usou. Ali nenhuma das regras de densidade e quebra
valia.

Elas foram para o `@media print` de `siras-telas.css`, carregado nas **duas** versões.
`siras-impressa.css` fica só com o que é exclusivo dela, a conversão para preto e branco.
É uma fronteira melhor do que a anterior, e o comentário no topo de cada arquivo a declara.

### D11.6 — Rolagem lateral não existe no papel

`.tabela-rolagem` usa `overflow-x: auto`, que em tela rola e **no papel corta**. O quadro
comparativo saía com as colunas "Classe P", "Classe K" e "Aptidão" decepadas na borda
direita da A4, com a barra de rolagem impressa junto. No papel o container passa a
`overflow: visible`.

Junto, a causa de a tabela exceder a folha: `white-space: nowrap` no cabeçalho, com
títulos de cartão longos ("Nitrogênio (N)", "Fósforo (P₂O₅)") usados como cabeçalho de
nove colunas. O quadro passou a usar as siglas do Manual — N, P₂O₅, K₂O — e o cabeçalho
pode quebrar em duas linhas.

### D11.7 — O documento não muda de tom entre os temas

O `.doc` já redefinia a escala de neutros, mas herdava do tema os quatro sinais
(`--sig-*`) e, com eles, a **rampa diagnóstica inteira**: `--d-mb` a `--d-ma` derivam
deles. O selo "Aptidão restrita" saía em `#FF9F3D` no tema escuro e `#D96D00` no claro —
o mesmo laudo, dois documentos, e só um deles medido contra o branco em
`scripts/conferir_contraste.py`.

O laudo é papel branco em qualquer tema e vai impresso. `.doc` passa a fixar os sinais, a
rampa e as bordas nos valores do tema **claro**, que são os calibrados contra fundo
branco. Não há mais o que manter em sincronia entre os dois temas.

### D11.8 — Blocos partidos e cabeçalho que não volta

Os selos de aptidão ficavam no pé de uma folha e as notas que os explicam na seguinte,
órfãs do que descreviam. A matriz de talhões atravessava a quebra sem repetir o cabeçalho,
e metade dela não dizia de qual talhão era cada coluna. A legenda da tabela, em
`caption-side: bottom`, era renderizada partida e saía como meia linha de letras soltas.

Resolvidos por `break-inside: avoid` em `.cenarios`, `.veredito`, `.talhao`,
`.detalhe-adubo__item`, `.orientacao` e nas linhas de tabela; `display: table-header-group`
no `thead`; e a legenda movida para o topo no papel.

### D11.9 — A matriz dizia "limitação" 42 vezes

Cada célula da matriz de aptidão trazia "limitação moderada", "limitação nula". A palavra
não distinguia uma célula de outra, e a linha já se chama "Acidez". Ficou só o grau.

### O que ainda depende de conferência

A contagem de folhas **não foi medida por este trabalho**: a estimativa em caracteres não
enxerga altura, e o autor é quem tem o navegador. As quatro correções acima atacam
exatamente o que os PDFs mostraram, mas o número final precisa sair de um Ctrl+P.

## Segunda passada, 11/10/2026 — o que o PDF seguinte mostrou

Com a paginação corrigida, dois PDFs novos: **erva-mate, um talhão, em 5 folhas** e
**milho, seis talhões, em 18**. A tabela já não saía cortada e os blocos já não partiam,
mas sobrava espaço vazio.

O que o milho mostrou: **cada talhão gastava duas folhas**, porque a aptidão nunca cabia
no que restava da primeira. Medindo o que cada peça ocupa, por talhão:

| | Altura |
|---|---|
| Os dois selos de aptidão | ~45 mm (`min-height: 150px` cada) |
| A tabela de fatores | ~35 mm |
| Os quatro cartões de dose | ~32 mm |
| As duas réguas | ~30 mm |

O selo era o maior, e o mais fácil de encolher **sem perder nada**: o que ele informa é o
rótulo da classe, não o tamanho da caixa. No papel a caixa encolhe e o rótulo continua
legível; em tela ele permanece grande, porque ali é o elemento de diagnóstico que o olho
procura. O ícone diminui mas **não sai** — é ele que distingue apta de inapta à distância.

O que a erva-mate mostrou: uma **quinta folha com uma frase só**. O rodapé do documento
era partido pela quebra de página. Assinatura e rodapé passaram a ser blocos inteiros.

Junto: a margem da `@page` de 15 mm para 12 mm, que ainda é folga de encadernação numa
A4, e a escala do veredito de 20 pt para 17 pt — hierarquia de documento, e não de tela.

## Leitura ao vivo com a tela já preenchida

Defeito encontrado no mesmo dia, fora do laudo. O painel de leitura ao vivo só reagia a
eventos, e evento só acontece quando alguém digita: quem carregava um exemplo via a tela
inteira com valores e o painel ainda dizendo *"a interpretação aparece aqui assim que você
digitar o primeiro valor"*. Precisava mexer num campo qualquer para ele acordar — e o
mesmo valia na volta do laudo para editar a análise.

O painel passa a interpretar uma vez ao carregar, quando há o que interpretar. O gatilho é
**ter valor**, e não ser exemplo: o painel lê o que está na tela, venha de onde vier.

## D11.10 — O espaço de assinar é padding, e não margem

Terceiro PDF, terceiro defeito que só o papel mostra. Na soja, a página 4 trazia a
assinatura **partida e sem lugar para assinar**: a linha ficou no pé da página 3 e o nome
no topo da 4, colado na borda.

Duas causas independentes, as duas sutis:

**A margem some na quebra.** O espaço de assinar era `margin-top: 22mm`. Margem superior é
**descartada pelo navegador quando o bloco começa numa página nova** — exatamente quando o
espaço mais faz falta. Virou `padding-top: 20mm`, que pertence à caixa e viaja com ela.

**`break-inside: avoid` não vale sobre grid.** A seção é `display: grid` em tela, e os
motores de fragmentação não respeitam a regra de forma confiável sobre um container de
grid. Foi por isso que ela partiu, apesar de a regra estar declarada duas vezes. No papel
a seção passa a `display: block`, onde a regra vale; o empilhamento centrado se mantém com
`text-align` e `margin-inline: auto`.

Vale o registro de que **nenhum dos dois apareceria em revisão de código**: a primeira é
uma regra de colapso de margem que só se manifesta na fragmentação, e a segunda é uma
limitação de motor. As duas vieram de olhar um PDF.
