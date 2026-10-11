# 0013 — Integração real da cena 3D, e fundos que medir decidiu

- **Status:** aceito
- **Data:** 2026-10-11
- **Contexto:** o autor abriu a interface nova e encontrou quatro defeitos de uma vez —
  landing com elementos sobrepostos e colados na borda, fundos invisíveis, cena do
  formulário duplicada e sem dizer o que lia, e a tela de espera ainda mostrando a
  animação 2D antiga. Sucede e corrige a [ADR 0012](0012-cena-3d-e-acabamento-da-interface.md)
- **Afeta:** `siras/web/templates/` (início, parciais da cena, gerando),
  `siras/web/static/css/` (telas, cena-solo), `siras/web/static/js/cena-solo.js`
- **Não afeta:** o motor, a base de conhecimento, o laudo em tela e impresso

---

## A causa comum dos quatro defeitos

Nenhum deles era um bug isolado. **Os parciais da v7 foram colados no projeto e nunca
integrados** — eles ainda traziam os comentários `AJUSTAR` do kit e liam variáveis que
nenhuma rota fornece (`formulacao_npk`, `atributos_cena`, `cultura_selecionada`).

Um parcial colado funciona o suficiente para parecer pronto: a cena sobe, o canvas
pinta, a suíte passa. O que ele não faz é ocupar lugar — e é aí que os quatro defeitos
nascem, todos da mesma raiz de "a peça está na página, mas não tem endereço nela".

A suíte não pegou nada disso, e não poderia: ela verificava que o parcial existia, que
tinha `aria-hidden`, que o motor estava vendorizado. **Nenhum teste podia ver que dois
elementos ocupavam o mesmo espaço**, e é por isso que este ciclo, como os três do laudo
impresso na ADR 0011, só começou quando alguém olhou a tela. Vale repetir o padrão: em
trabalho de interface, a captura de tela é instrumento de medição, não ilustração.

---

## D13.1 — A cena da hero era fundo; virou peça

Ela estava **fora do contêiner**, como último filho da `<section class="hero">`, com
`position: absolute; inset: 0; z-index: -1`. Três coisas davam errado ao mesmo tempo:

| sintoma | causa |
|---|---|
| o monólito cobria o cartão da régua | o canvas tinha a largura inteira da hero, e a cena desenha no centro dele |
| controles e legenda colados na borda da tela | eles **não** são absolutos: caíam no fluxo, fora da margem do `.env` |
| a legenda esticada numa tira no pé da página | sete colunas de `auto-fill` na largura total |
| o parágrafo dos limites espremido na direita | ele virou item da fileira *flex* dos controles |

Agora a cena é a peça de cima da coluna direita, dentro de `.hero__coluna`, e o cartão
da régua desceu para baixo dela. Tudo que explica a cena — controles, legenda, limites —
mora junto dela.

A caixa usa `aspect-ratio: 761/711`, a proporção do próprio fallback, e não altura fixa:
o monólito é um objeto 3D enquadrado pela câmera, e uma caixa que muda de proporção com
a largura da coluna ou o corta, ou o deixa nadando no vazio.

## D13.2 — A duplicação do painel era uma linha de cascata

Na tela de dados apareciam **dois** blocos de solo, um por cima do outro: a imagem
estática e o canvas vivo.

```css
.cena-solo--ativa  .cena-solo__fallback { display: none; }   /* linha 39 */
.cena-solo--painel .cena-solo__fallback { display: block; }  /* linha 89 */
```

Mesma especificidade — 0-2-0 — e a segunda vem depois no arquivo, então vence. O
`cena-solo--ativa` que o adaptador acrescenta quando o canvas sobe não desligava mais
nada. A correção é `:not(.cena-solo--ativa)` no seletor do painel: não muda a
especificidade, só tira a regra do caminho quando a cena está viva.

É o tipo de defeito que não aparece em revisão de código — as duas regras estão certas
isoladamente — e que salta aos olhos na primeira captura de tela.

## D13.3 — Um ponto aceso sem nome não informa nada

A cena do formulário acendia e pulsava o marcador do atributo preenchido, e não dizia
**qual**. Os marcadores são sprites 3D sem texto (`soilScene.js`, `layoutMarkers`), e
pôr rótulo flutuante sobre cada um quebra em tela estreita — metade do público usa
tablet em campo.

O nome passa a viver em HTML abaixo da cena, num inventário de sete linhas com o estado
de cada atributo, mais a contagem (*"4 de 7 atributos informados"*), que responde a
pergunta que a cena sozinha não respondia: **quanto falta**.

O ponto cheio contra o círculo tracejado distingue informado de ausente por
preenchimento, e não só por cor, para funcionar em daltonismo e em tela sob sol.

O inventário continua sem interpretar nada: ele diz "informado" ou "não informado". A
classe de teor é do motor, no servidor, e aparece na leitura ao vivo logo abaixo.

## D13.4 — A tela de espera mostrava as duas ilustrações

O SVG 2D de 109 linhas **nunca foi removido** quando a cena 3D entrou. E a cena 3D
herdara o `z-index: -1` do uso como fundo da hero, o que dentro desta tela a punha
atrás do véu opaco: **ela rodava, invisível, enquanto o desenho antigo aparecia por
cima.** Os textos soltos no topo do véu eram o chrome de exemplo do kit, renderizando
vazio.

O SVG saiu, e com ele as cerca de 150 linhas de CSS que o animavam e dez tokens de cor.
CSS órfão de um elemento que não existe mais é a forma mais silenciosa de uma folha de
estilo apodrecer — e foi exatamente assim que as duas ilustrações chegaram a coexistir
sem ninguém notar.

**O que se perdeu, e o que não:** o broto que crescia com o progresso não tem
equivalente na cena 3D. Não faz falta, e há um argumento para que não volte: um perfil
que fica mais vivo a cada passo diz, sem número nenhum, que o laudo melhora a lavoura
enquanto é calculado. `test_a_cena_nao_melhora_o_solo_enquanto_calcula` passa a guardar
isso. A etiqueta do capítulo consultado também saiu; o que o passo consulta continua no
`<small>` dele — e aí melhorou, porque a etiqueta vivia dentro de um SVG `aria-hidden`
e quem não enxergava nunca a teve.

Quem desliga o movimento também mudou de lugar. No SVG era CSS, `animation: none` em
cada peça. Num canvas não há peça a desligar, há um laço de render: quem para é o motor,
por `reducedMotion`, que o adaptador lê da aplicação e reaplica quando o usuário troca a
preferência.

## D13.5 — Os fundos: medir mudou o desenho, não só o número

A primeira tentativa (ADR 0012, D12.6) pôs as artes como textura sobre a seção inteira,
a 16% de opacidade. Elas sumiram. Medir explicou por quê, e a explicação mudou o
desenho duas vezes.

**Primeiro: sobre fundo escuro, misturar não funciona.** Arte escura sobre fundo escuro
em composição normal a 16% move o fundo em **7 de 255** — nada. O que faz uma arte
escura aparecer sobre fundo escuro é `screen`, que só clareia: a 55%, o mesmo par move
31. Era operação errada, e não opacidade baixa.

| | normal 16% | screen 55% |
|---|---|---|
| sobre `#0A0F0C` | delta 7 | delta **31** |
| sobre `#F6F8F5` | delta 34 | delta 0,3 |

**Segundo, e decisivo: ela não pode ficar atrás de texto, em opacidade nenhuma.** O teto
de luminância de fundo que sustenta o `--n-400` (texto terciário, `.t-aux`) a 4,5:1 é
**0,027**. A região mais clara da `op-3` em screen cheio chega a **0,57** — vinte vezes
o teto. Não há dosagem que resolva: ou a arte aparece, ou o texto secundário se lê.

A saída não foi dosar, foi **mudar de lugar**. A arte vai onde não há texto nenhum:

- **atrás do monólito**, dentro da vitrine da cena, em força total — é o único lugar da
  página sem nada escrito por cima, e é o que a arte foi feita para fazer;
- **nas calhas**, as faixas vazias fora da coluna de 1200px. Eram exatamente o "fundo
  chapado" de que o autor reclamou, e agora são o único lugar da página onde a paisagem
  cabe sem disputar com nada.

A máscara horizontal é `calc(50% - 600px)`: abaixo de 1200px não há calha, a máscara
fecha sozinha e a textura desaparece. **Em telefone não sobra nada atrás de texto, sem
media query** — a regra se degrada pela própria geometria.

As faixas alternadas recebem a textura pela própria classe, e não uma a uma no template:
a regra é "as faixas escuras carregam a paisagem nas calhas". Aplicar caso a caso daria
uma página onde a textura aparece e some sem motivo visível ao rolar.

No tema claro `screen` não faz nada — clarear o que já é quase branco move 0,3 de 255. A
operação que marca ali é a inversa, `multiply`, bem fraca, e nas mesmas calhas.

**E 8,6 MB continuavam sendo servidos** como PNG para pintar isso: `scripts/gerar_fundos.py`
converte para WebP e os originais ficam em `docs/fundos/`. 8,6 MB → 175 KB, sem
diferença visível.

---

## Segunda rodada, 11/10/2026 — o que a tela mostrou

Com a primeira rodada no ar, o autor voltou com cinco pontos. Três deles corrigem
decisões desta mesma ADR, e um deles por um motivo que vale registrar.

### A arte certa vale mais que o filtro bem ajustado

A D13.5 gastou duas tentativas forçando as cinco paisagens escuras a servir nos **dois**
temas. Medir mostrou que não dava: sobre quase-branco, `screen` move 0,3 de 255 e
`multiply` dá uma sombra cinza — nenhuma das duas desenha uma paisagem.

O autor entregou então três artes **claras**: as mesmas colinas sob névoa, luminância
média 226 contra os 43 das escuras, mais uma quadrada para a vitrine do monólito. Com
elas o tema claro dispensa mesclagem: é composição normal, e aparece.

A lição fica no teste `test_cada_tema_tem_a_sua_arte_de_fundo`: **quando um ajuste de
mesclagem precisa de três tentativas, o problema costuma ser o material, e não o
número.** Eu estava afinando um filtro para fazer uma arte dizer o que ela não dizia.

### A cautela que sobrou de um caso que não existia

A primeira rodada pôs a textura a 50% de opacidade por causa do teto de contraste do
`--n-400`. Mas o mesmo desenho já tinha posto a textura **só nas calhas**, onde não há
texto — e lá o teto não se aplica. Era cautela herdada de um problema que a solução
anterior já tinha eliminado. Agora vão em 78% (escuro) e 85% (claro).

### A camada passou a ser global e fixa

O pedido era que o fundo valesse em todas as telas, e não só na inicial. Tabelas,
cultura e dados não têm faixas para receber uma camada própria, então a camada foi para
o `body`, `position: fixed`, com a mesma máscara de calhas.

Fixa, ela não rola: a paisagem fica como horizonte atrás da página inteira, em vez de
passar como objeto. E uma camada só não empilha com ela mesma — seções vizinhas com
textura própria somavam duas artes na mesma calha e embarravam a cor.

### A cena da espera nascia sem área

Ela continuava invisível, e não era mais o z-index: o véu nasce `hidden`, e a cena
montava o contexto WebGL numa caixa de 0×0 dentro de uma subárvore `display: none`.
Chegava à tela sem nunca ter pintado. O `ResizeObserver` de `soilScene.js` reenquadra,
mas reenquadrar um contexto que nasceu sem área é tarde demais.

Agora **toda cena dentro de um escopo `hidden` espera o escopo abrir**. Isso resolve
duas coisas de uma vez: ela nasce com o tamanho certo, e não há um segundo canvas
consumindo GPU durante todo o preenchimento do formulário — que era a travada relatada
na tela de dados.

### A espera passou de 6 s para 24 s

A pedido do autor, porque as cinco coreografias não tinham tempo de acontecer: o
calcário caía e a tela já trocava. Em 24 s cada passo fica com cerca de 4,6 s.

**É uma decisão de risco assumido, e fica registrada como tal.** Vinte e quatro segundos
de espera deliberada para um cálculo que leva dezenas de milissegundos é muito, e a
avaliação de usabilidade pode condená-la. O argumento do autor é que esta tela não tem
função — o laudo já está calculado — e existe para ser vista. O contra-argumento é que
tempo de espera é o item que usuários mais reclamam em teste. O número está numa
constante só, `ESPERA_MINIMA_MS`, e mudá-lo não quebra mais nada.

### A leitura ao vivo tinha teto errado

Ela era `sticky` e crescia sem limite: com a análise toda preenchida ficava mais alta
que a janela, e aí grudar no topo não adianta — o fim do painel some embaixo e não
volta. **Quanto mais completa a leitura, menos dela se via.**

Agora o painel tem altura máxima da janela, o cabeçalho e a cena ficam parados, e só a
interpretação rola por dentro. A cena caiu de 320 px para `clamp(120px, 17vh, 185px)`:
ela ilustra o que já foi informado, não é o assunto, e o tamanho tem de dizer isso.

### A décima cena saiu da hero

O parágrafo "Ilustração conceitual…" repetia, em quatro linhas, o que a legenda logo
abaixo já diz em cinco palavras: *exemplo ilustrativo, sem valores*. Saiu da hero e
continua na tela de espera, que é onde a planta cresce e onde a ilustração mais se
parece com uma promessa de safra.

A declaração não se perdeu, e é isso que separa remover texto redundante de remover uma
garantia: `test_a_cena_da_hero_se_declara_ilustrativa` guarda a que ficou.

---

## Terceira rodada — o ritmo da espera

### A primeira etapa não se movia, e a causa não era o tempo

Com a cena enfim visível, ela abria parada em "Lendo a análise de solo" — e a segunda
rodada tinha acabado de dar a essa etapa 4,6 s de nada.

A causa estava em `soilScene.js`, na criação da cena:

```js
const params  = { ...stages[initialStage].targets, hover: 0 };
const targets = { ...stages[initialStage].targets };
```

**`params` e `targets` nasciam iguais.** A cena abria já no estado final do primeiro
estágio, então não havia o que animar: a varredura que devia atravessar o perfil já
estava no fim antes de começar. As outras quatro etapas se moviam porque cada uma entra
vindo da anterior; só a primeira não tinha de onde vir.

Nos outros usos isso é o comportamento certo — a hero deve abrir mostrando o solo, e
não montando-o. Numa **sequência**, não: a opção `enterFrom` dá à cena um estado de
partida, e na espera ela entra do repouso (`BASE`, de stages.js). A primeira etapa vira
uma transição como qualquer outra.

Vale notar onde o defeito estava: não no tempo, que era o sintoma, mas na inicialização.
Alongar a etapa tinha piorado — mais segundos de imagem parada.

### 24 s era espera exaustiva

Metade: **12 s**. O objetivo da tela é passar robustez de recomendação, e uma tela que
demora demais passa o contrário — falta de desempenho. O risco que a segunda rodada
registrou se confirmou antes mesmo da avaliação de usabilidade, e por observação do
próprio autor.

### O tempo deixou de ser dividido por igual

É isto, e não o total, que faz 12 s bastarem:

| etapa | tempo | por quê |
|---|---|---|
| Lendo a análise | 1,45 s | uma varredura que atravessa o perfil uma vez |
| Calagem | 2,62 s | o calcário cai e fica na superfície |
| Adubação | 2,62 s | fósforo e potássio sobem da camada de referência |
| Formulação | 2,62 s | os três montes se agrupam |
| Aptidão | 1,78 s | a alternância se entende no primeiro ciclo |

As três do meio têm coreografia de verdade e precisam de tempo para serem lidas como
movimento, e não como corte. As duas das pontas não — dar a elas o mesmo tempo era
alongar a espera sem acrescentar nada para ver.

Duas consequências que o ritmo desigual obrigou:

- **A barra passou a medir tempo, e não passos.** Encher um quinto por etapa com etapas
  desiguais a faria parar e disparar.
- **A alternância dos cenários caiu de 3,2 s para 1,1 s.** Com a aptidão em 1,78 s, a
  3,2 s ela não chegava a acontecer uma vez — e uma etapa que anuncia "os dois cenários"
  mostrando um só é pior que não alternar. `test_o_tempo_vai_para_as_etapas_que_tem_coreografia`
  guarda a relação entre os dois números, e não cada um deles.

Os pesos são relativos (`PESOS_DAS_ETAPAS`): mexer em `ESPERA_MINIMA_MS` redistribui
tudo sozinho, e um passo novo no template entra com peso 1 em vez de quebrar a tela.

### E o motor chega antes

Os módulos da cena passaram a ser pré-carregados quando o formulário abre; o que espera
o véu é a criação do contexto WebGL, que precisa de caixa. Baixar e compilar o motor no
meio da primeira etapa era a outra metade da sensação de travamento.

---

## O que isto não resolve

As duas verificações que só a tela dá, e que a suíte não substitui:

1. **A opacidade das calhas e da vitrine é escolha visual.** Os números acima garantem
   que o texto se lê; não garantem que fique bonito. É uma linha de CSS por lugar, e as
   cinco artes estão geradas para trocar.
2. **A cena da espera monta com o véu `hidden`**, logo com caixa 0×0. O `ResizeObserver`
   de `soilScene.js` deve reenquadrá-la quando a tela aparece, e `resize()` protege o
   caso com `Math.max(1, …)`. Está certo no papel; falta ver rodando.

E continua valendo o aviso da ADR 0012: estas escolhas de interface foram feitas antes
de haver dado de usuário, e a lista das dez heurísticas pode contradizer várias.
