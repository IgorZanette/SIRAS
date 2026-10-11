# 0012 — Cena 3D do perfil de solo e acabamento da interface

- **Status:** aceito
- **Data:** 2026-10-11
- **Contexto:** pedido do autor de reformular a interface antes do congelamento, com a
  landing do Pampa Tickets como referência de acabamento e o `SIRAS-3D-kit-v4/` como
  ponto de partida da cena. Plano em [`../processo/plano-frontend-v2.md`](../processo/plano-frontend-v2.md)
- **Afeta:** `siras/web/templates/` (base, início, dados, parciais da cena),
  `siras/web/static/` (css, js, vendor, img), `siras/dominio/estado.py` (novo),
  `siras/web/rotas.py`
- **Não afeta:** o motor, a base de conhecimento, o laudo em tela e impresso

## A decisão de prazo, que veio antes de todas

O plano de frontend recomendava integrar **depois** da coleta de usabilidade, e o
próprio kit dizia o mesmo nas pré-condições. O autor decidiu o contrário, em 11/10, e
o argumento dele é melhor:

> Congelar **depois** do frontend novo faz os participantes avaliarem o sistema final.

A objeção original era contra mexer na interface **durante** a coleta, o que faria
participantes avaliarem sistemas diferentes. Antecipar para antes do congelamento não
tem esse problema: a coleta continua rodando sobre uma versão só. O que muda é que
`congelamento-v1` passa a incluir a interface nova — e a avaliação passa a medir o
sistema que o trabalho entrega, e não um estado intermediário dele.

## D12.1 — three.js vendorizado, e o que ele custa

A cena usa **three.js 0.160.0**, servido do próprio repositório:

| | |
|---|---|
| `three.module.min.js` | 670.681 bytes (654 KiB) |
| SHA-256 | `3e690ac7d180b0aadf0891bea39eec643e29e2d3e75c99b18689518665f69ba6` |
| Licença | MIT, distribuída junto |
| Total acrescentado | ~1,2 MB (three + motor + adaptador + CSS + 3 WebP de fallback) |

**A tensão precisa ser dita, e não escondida.** A decisão metodológica nº 1 deste
trabalho — [ADR 0001](0001-motor-em-python-puro.md) — foi **não** usar biblioteca de
inferência, para que o motor fosse auditável linha a linha. Trazer 670 KiB de código de
terceiros parece contradizê-la.

Não contradiz, e a diferença é o que justifica a decisão: **o three.js não participa de
nenhuma decisão agronômica.** Ele desenha. Nenhuma dose, classe de teor ou grau de
limitação passa por ele; a cena *espelha* o que o DOM já diz, e o DOM vem do mesmo motor
em Python puro de sempre. Se o three.js sumisse, o sistema continuaria recomendando o
mesmo, e a página continuaria inteira — há fallback estático e teste para isso.

O que **não** se admitiu, e vale registrar como fronteira:

- **CDN.** O sistema roda offline em `localhost`. A dependência é servida de `static/`,
  com LICENSE, versão e hash declarados, e um teste confere o hash.
- **Cadeia de build.** O motor da cena é módulo ES carregado por import map; o adaptador
  é IIFE, no mesmo padrão dos outros scripts do projeto. Não há npm, nem bundler.
- **3D no laudo.** O laudo é documento assinado por profissional habilitado. O cabeçalho
  da cena entra por **bloco Jinja**, e não em `base.html`, justamente para que a página
  do laudo não baixe um byte dela. Dois testes guardam isso, um em tela e um impresso.

Esse número precisa aparecer na seção de limitações do artigo.

## D12.2 — A Fase 2b foi cortada, e não adiada

O kit previa um painel 3D ao lado dos campos do formulário. Ele **não** foi integrado.

A tela de dados já tem o painel de leitura ao vivo, que interpreta cada valor digitado
contra as tabelas do Manual e mostra a classe com a régua e a fonte. É o elemento de
maior valor pedagógico do sistema, e a §9.3 do plano de front-end o justifica por um
motivo que uma ilustração não substitui. Pôr uma cena ao lado disputaria atenção com o
que ali já funciona.

`test_o_formulario_nao_recebe_cena` registra a decisão em código: se o parcial voltar, a
suíte avisa.

### Adenda de 11/10/2026 — REVERTIDA, e o argumento sobreviveu

A cena do formulário **voltou**, em outro lugar: como **cabeçalho do painel de leitura
ao vivo**, e não como painel ao lado dele.

O corte estava certo pelo motivo que deu — um painel rival disputaria atenção com o
elemento mais pedagógico da tela. O que a reversão descobriu é que *ao lado* era a única
posição considerada. Como cabeçalho do mesmo painel as duas não disputam, porque
respondem perguntas diferentes e em sequência:

| | pergunta que responde | linguagem |
|---|---|---|
| a cena, acima | o que já foi informado | um ponto aceso por atributo |
| a leitura, abaixo | o que aquilo significa | classe, régua e tabela do Manual |

Inventário e depois interpretação. A cena continua **sem interpretar nada**: ela mostra
"lido" ou "ausente", e só — `seguirFormulario` segue proibida de usar `limitante` e
`corrigido`, e o teste continua verificando isso. O que mudou de verdade é que o usuário
passa a ver, sem rolar, quanto da análise já entrou.

O mapa de qual campo acende qual ponto fica em `ATRIBUTO_DA_CENA`, no macro `campo()`, e
não em cada chamada: o macro é chamado em sete lugares, e um argumento a mais em todos
divergiria na primeira tela que alguém esquecesse.

`test_a_cena_do_formulario_e_cabecalho_da_leitura_e_nao_painel_rival` substitui o teste
anterior e guarda as duas metades: a cena está dentro do painel, e não interpreta.

## D12.3 — A landing não foi reescrita

O diagnóstico do plano encontrou o que não se esperava: **a estrutura da landing já
resistia à comparação com a referência.** Hero, problema, comparativo, como funciona,
público, prévia e FAQ já existiam, e o comparativo em tabela é formato melhor que os
cartões de recursos da referência.

O que faltava era acabamento. Então o que entrou foi acabamento:

- **Revelação ao rolar** (`revelar.js`): 14 px de deslocamento e 420 ms. O conteúdo
  *chega*, não desfila. Cada elemento é revelado uma vez e o observador o solta.
- **Profundidade**: `--luz-topo` e `--sombra-doc` já existiam na paleta e quase só o
  documento os usava.
- **Foco visível único**, em tudo que recebe foco por teclado. Antes cada componente
  resolvia por conta, e alguns não resolviam.
- **"Pular para o conteúdo"** como primeiro foco (WCAG 2.4.1), que o SIRAS não tinha.

**A guarda que mais importa aqui é a `tem-js`.** O defeito mais fácil de introduzir ao
animar entrada é esconder o conteúdo no CSS e revelá-lo por JavaScript: quem estiver sem
JS fica com a página em branco. A classe entra no mesmo script inline que aplica o tema
antes da primeira pintura, e sem ela nenhuma regra de revelação se aplica. Quem pediu
menos movimento vê tudo de uma vez, e a impressão desfaz a revelação inteira — os três
casos têm teste.

## D12.4 — A seção de status vem de uma fonte só

Direto da referência: uma seção dizendo em que pé o trabalho está, com etiquetas
*Concluído / Em andamento / Próximo*. Para uma banca, é o que transforma "um sistema" em
"um trabalho com método".

As etapas moram em `siras/dominio/estado.py`, e **não** no template. Escritas no
template, divergiriam de `docs/processo/roadmap.md` na primeira semana — alguém atualiza
um e esquece o outro, e a página passa a afirmar um estado que o projeto não tem.
`testes/unidade/test_estado_do_projeto.py` confere que cada etapa da tela aparece no
roadmap, que a ordem é a do percurso e que o template não escreve nenhuma à mão.

Esse teste já serviu: ao rodar pela primeira vez, apontou que a tela dizia "Aplicação
web" e o roadmap, "Módulo de entrada de dados". As duas fontes passaram a usar as mesmas
palavras.

A seção também trouxe o **selo de natureza** para o alto do hero — *Trabalho de Conclusão
de Curso · em desenvolvimento · roda local e offline*. Estava só no rodapé do laudo. Um
TCC que se apresenta como produto acabado perde mais credibilidade do que ganha.

## D12.5 — As dez cenas da v7, e onde cada uma coube

A v7 do kit trouxe dez cenas, e o pedido foi que todas entrassem no sistema. Elas não
são dez telas: são dez momentos, e o sistema tem três lugares onde um momento desses faz
sentido.

| cenas | onde | por quê ali |
|---|---|---|
| 1 a 3 — o solo, o que a análise revela, aptidão potencial | estágios da hero | são o arco inteiro do sistema em três cliques, que é o que uma hero precisa dizer |
| 4 — durante o preenchimento | cabeçalho da leitura ao vivo | ver a análise entrando enquanto se digita (D12.2, adenda) |
| 5 a 9 — diagnóstico, calagem, adubação, formulação, aptidão | tela de espera | uma coreografia por módulo do motor |
| 10 — limites desta camada visual | texto, junto dos controles da hero | ver abaixo |

A décima é a única que **não** virou movimento, e de propósito: ela diz o que a
ilustração não é, e uma animação que explica os limites de uma animação é um nó. O texto
é o da própria apresentação, quase palavra por palavra — *"Ilustração conceitual: a
planta é genérica, nenhum valor aparece na cena, não há promessa de produtividade, e o
laudo, em tela e impresso, não tem 3D."*

Ela importa mais do que o tamanho sugere. Uma cena 3D convence mais do que deveria: o
perfil desenhado tem aparência de medição, e a planta que cresce entre os estágios tem
aparência de promessa de safra — que é exatamente o que um sistema de recomendação não
pode insinuar. É a mesma regra que proíbe número sem tabela no resto do sistema,
aplicada ao desenho.

O texto fica **dentro** de `.cena-solo-controles`, que é `hidden` até o motor 3D subir:
sem WebGL não há ilustração, e um aviso sobre uma ilustração ausente só confunde.

`test_as_dez_cenas_da_v7_estao_todas_em_uso` é o inventário em código — é assim que esse
tipo de coisa se perde numa refatoração.

### A tela de espera estava mentindo

Ao encaixar as cinco coreografias apareceu um defeito que não tinha nada a ver com a
cena: **os passos anunciados não eram mais os do motor.** A tela dizia "Montando a
trilha" e não dizia "Formulação", que `gerar_laudo()` executa desde a ADR 0007.

Era uma lista escrita à mão, e o teste que a verificava era outra lista escrita à mão —
as duas envelheceram juntas, concordando entre si. Agora a expectativa deriva de
`_ORDEM_DOS_MODULOS`, a mesma constante que agrupa a trilha do laudo: um módulo novo no
motor volta a quebrar o teste, que é o ponto de ele existir.

## D12.6 — Os fundos entram como atmosfera, não como imagem

As cinco artes de fundo são paisagens de lavoura ao amanhecer, e **todas são escuras**.
Isso, e não o gosto, decidiu onde elas podiam entrar.

Uma imagem escura a baixa opacidade sobre fundo claro não vira textura: vira uma mancha
cinza que derruba o contraste do texto. Então elas entram nos dois lugares onde a página
já tem atmosfera — a **hero**, dissolvendo-se antes do conteúdo, e a **chamada final**,
entrando por baixo para a página terminar num horizonte — e recuam de 16% para 5% no
tema claro, no limite de serem percebidas.

São `background-image`, e não `<img>`: não entram na árvore de acessibilidade, nenhum
texto depende delas, e somem na impressão.

### 8,6 MB que estavam sendo servidos

As cinco artes entraram em `static/` no commit da identidade, e estavam sendo baixadas
inteiras: 8,6 MB de PNG para pintar uma textura a 16% de opacidade. PNG é formato sem
perda — ele preservava com precisão um degradê de céu que, no uso final, está sob uma
camada de 84% de fundo sólido. Numa tela de campo, por 4G, é o produtor esperando por
aquilo que ele não vê.

`scripts/gerar_fundos.py` converte para WebP a 1600 px: **8,6 MB viraram 175 KB**, e a
diferença visível é zero. O padrão é o mesmo da marca — a arte original fica em
`docs/fundos/`, que não é servido, e o script registra como o arquivo servido foi
produzido. `test_os_fundos_servidos_sao_leves` impede o PNG de voltar.

As cinco são geradas, com duas em uso: elas são opções do autor, e trocar o fundo da hero
é mudar uma linha de CSS — o que só é verdade se as cinco estiverem lá. A 35 KB cada, as
três de reserva custam menos que o PNG de uma.

## O que a avaliação de usabilidade ainda pode desfazer

Esta ADR registra escolhas de interface feitas **antes** de haver dado de usuário. A
lista priorizada que sair das dez heurísticas é evidência melhor sobre o que melhorar do
que qualquer uma delas, e pode contradizer várias — a começar pela própria cena, se os
participantes a acharem ruído.

Isso não é defeito do plano: é a ordem que o prazo impôs. Vale dizê-lo no artigo junto
com os resultados, para que a leitura da usabilidade não seja lida como aprovação do que
veio antes dela.
