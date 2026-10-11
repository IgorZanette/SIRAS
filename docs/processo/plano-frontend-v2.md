# Plano de frontend v2 — SIRAS como plataforma

> **Executado em 11/10/2026, antes do congelamento.** Este documento foi escrito
> recomendando integrar depois da coleta; o autor decidiu antecipar, com um argumento
> melhor que o meu — congelar depois do frontend novo faz os participantes avaliarem o
> sistema final, e não um estado intermediário dele. O que de fato entrou, e o que ficou
> de fora, está na [ADR 0012](../decisoes/0012-cena-3d-e-acabamento-da-interface.md).
>
> O diagnóstico e a avaliação do kit abaixo continuam valendo como registro do raciocínio.

Documento de **estruturação**, escrito em 11/10/2026 a pedido do autor. Nada aqui foi
implementado: é o mapa do que fazer, em que ordem e sob quais restrições.

Três entradas o originaram: a reformulação do frontend pedida pelo autor, a landing do
[Pampa Tickets](https://www.pampatickets.com.br/) como referência de acabamento, e o
`SIRAS-3D-kit-v4/` colocado na raiz do repositório.

---

## 0. A restrição que manda em tudo

**A implementação encerra em 12/10/2026**, por definição do orientador, e a coleta de
usabilidade roda sobre a tag `congelamento-v1` entre 20/10 e 14/11. Mexer na interface no
meio da coleta faria os participantes avaliarem **sistemas diferentes**, e a consolidação
por heurística deixaria de somar — é a dependência estrutural declarada no roadmap desde
24/09.

O próprio kit chegou consciente disso. O `PROMPT.md` dele diz, em pré-condições:

> **Congelamento (12/10/2026).** O teste com usuários roda sobre `congelamento-v1`.
> Integre só depois da coleta. Antes disso, cabem a Fase 0 (só leitura) e a página da
> defesa (fora do repositório).

Então a pergunta não é *o quê*, e sim *quando*. Há duas janelas, e a escolha é do autor
com o orientador:

| Janela | O que cabe | Risco |
|---|---|---|
| **Antes de 12/10** | Fase 0 do kit (diagnóstico, sem tocar no repositório) e a página da defesa, que vive fora do repositório | Nenhum |
| **Depois de 14/11** | Tudo o mais deste plano | Nenhum para a pesquisa; o artigo precisa estar escrito |

Uma terceira hipótese — adiar o congelamento para integrar antes — **custa a validade da
avaliação de usabilidade**, que é um capítulo inteiro do TCC. Não a recomendo, e ela não
é minha para decidir: é conversa com o orientador.

---

## 1. Diagnóstico: o que a landing do SIRAS já tem

Comparando `siras/web/templates/inicio.html` (428 linhas) com a referência, seção a seção:

| Pampa Tickets | SIRAS hoje | Situação |
|---|---|---|
| Hero com rótulo de status, título, subtítulo, 2 botões e mock de interface | Hero com promessa, subtítulo e botões | **Tem** |
| Problema em cartões | "Pilares" do problema, 3 cartões com ícone | **Tem** |
| Solução / fluxo em 3 etapas | "Como funciona", 3 cartões | **Tem** |
| Recursos em cartões | Comparativo em tabela (antes × com o SIRAS) | **Tem**, em formato melhor |
| Para quem é | "Público", 2 perfis | **Tem** |
| Prévia / mock | Prévia do laudo, sem valores | **Tem** |
| FAQ | Perguntas frequentes em `details` | **Tem** |
| Status do projeto, em etapas rotuladas | — | **Falta** |
| Equipe | — | Não se aplica (TCC individual) |
| Prova social, números, depoimentos | — | Não existe na referência também |

**A conclusão é a parte útil deste diagnóstico: a estrutura já está lá.** O que separa as
duas não é a lista de seções — é o **acabamento**: movimento, profundidade, ritmo de
leitura e a sensação de peça acabada. Reescrever a página seção a seção seria refazer o
que já existe.

> **Limite do que pude verificar.** A leitura da referência retornou texto e estrutura, e
> não a camada visual: cores, tipografia, sombras e animações não vieram. O que transfiro
> abaixo é padrão de estrutura e de microcopy, que é o que o texto revela. A direção
> visual precisa de uma passada do autor com as duas páginas abertas lado a lado.

### O que a referência faz e vale copiar

1. **Rótulo de status no topo do hero.** "Em desenvolvimento · protótipo navegável". O
   SIRAS tem uma honestidade equivalente a declarar — é TCC, roda local, é apoio à
   decisão — e hoje ela só aparece no rodapé do laudo.
2. **Seção de status do projeto, com etiquetas** "Concluído / Em andamento / Próximo".
   Para uma banca, isso é ouro: mostra método, e não só produto.
3. **Títulos afirmativos terminados em ponto**, com subtítulo que explica. O SIRAS já usa
   esse padrão em parte; vale uniformizar.
4. **Abas por perfil.** A referência tem "três passos para cada perfil"
   (organizador/participante/fotógrafo). O SIRAS tem dois públicos declarados — técnico e
   estudante — e hoje os mostra lado a lado em vez de em abas.
5. **"Pular para o conteúdo"** como primeiro foco. Acessibilidade que o SIRAS ainda não tem.

---

## 2. As cinco frentes

Ordenadas por **razão entre o que entregam e o que custam**, e não por vistosidade.

### F1 — Acabamento da interface atual (sem 3D)

O maior ganho por hora de trabalho, e o único que não depende do kit.

- **Movimento com propósito:** entrada em cascata das seções ao rolar
  (`IntersectionObserver` + `prefers-reduced-motion`), e não animação decorativa. O SIRAS
  já tem `animation: entrar-tela` nas telas; falta o mesmo ritmo dentro da landing.
- **Profundidade:** a paleta já tem `--sombra-doc` e `--luz-topo`. Hoje quase só o
  documento os usa. Cartões, painéis e o hero podem ganhar a mesma linguagem.
- **Estados de interação:** `:hover` e `:focus-visible` com transição em tudo que é
  clicável. Parte existe; falta consistência.
- **Ritmo tipográfico:** a escala existe em tokens. Falta aplicá-la com hierarquia mais
  marcada entre título de seção, subtítulo e corpo.

Custo: 1 a 2 dias. Risco: baixo, é CSS. **Nada aqui muda texto, ordem ou função** — o que
importa se for feito depois da coleta e houver desejo de comparar as duas versões.

### F2 — Seção de status e rótulo de honestidade

Direto da referência. Uma seção com as etapas do projeto e sua situação, alimentada **do
roadmap** e não escrita à mão no template — senão diverge na primeira semana.

Para a banca, é a seção que transforma "um sistema" em "um trabalho com método".

Custo: meio dia.

### F3 — Cena 3D do perfil de solo (o kit v4)

Ver a seção 3 abaixo, que é longa o bastante para ter a sua.

### F4 — Fluidez entre telas

O SIRAS é um fluxo de três etapas, e hoje cada uma é um carregamento de página seco.

- Barra de progresso contínua entre as etapas (existe, mas estática).
- Transição de saída da tela anterior, casando com a `entrar-tela` que já existe.
- A tela de espera já é o melhor momento do sistema; vale usá-la de modelo para o resto.

Custo: 1 dia. **Cuidado:** nada disso pode introduzir dependência de JavaScript para
navegar — o fluxo funciona sem JS hoje, e isso é requisito de acessibilidade (WCAG 2.1.1).

### F5 — Oportunidades que o kit não cobre

O autor pediu explicitamente para não se prender ao kit. Em ordem de valor:

1. **Comparar dois talhões lado a lado na tela**, com as réguas alinhadas. O laudo já traz
   o quadro comparativo; a tela não tem nada equivalente.
2. **Histórico local da sessão** — as últimas análises feitas, em `sessionStorage`, para
   voltar a uma sem redigitar. Respeita "sem banco": nada sai do navegador.
3. **Atalhos de teclado** no formulário: avançar entre blocos, enviar. Público técnico
   que preenche muitos laudos ganha tempo real.
4. **Exportar o laudo em CSV** além do PDF, para quem leva os números a uma planilha.
5. **Tela de tabelas com busca** — são 7 tabelas e 141 culturas no Anexo 2; hoje só há
   rolagem.
6. **Primeira visita guiada** — existe `guia.js`, hoje subaproveitado.

---

## 3. O kit 3D v4 — avaliação

### O que ele resolve, e que a v2 não resolvia

A versão anterior do kit trazia React, CDN e uma narrativa que prometia produtividade. A
v4 corrige os três:

| Objeção à v2 | Situação na v4 |
|---|---|
| React, incompatível com Flask + Jinja | **IIFE sem build**, no mesmo padrão dos outros scripts do SIRAS |
| three.js por CDN, contra a regra de rodar offline | **Vendorizado** em `static/vendor/three/0.160.0/`, com LICENSE e SHA-256 |
| Sem testes | **40 testes** no próprio kit, que rodei: todos passam |
| Narrativa com promessa de produtividade | Regra explícita: "nenhuma promessa de produtividade", "nenhum número agronômico na cena" |
| Risco de mexer no laudo | Cabeçalho da cena entra **por bloco Jinja**, só nas páginas que a usam, com teste de que o laudo sai byte a byte igual |

É um kit bem feito, e escrito por quem leu o `CLAUDE.md`.

### Fase 0, executada agora (só leitura, nada alterado)

**(a) Peso da dependência — confirmado.**

| | Medido |
|---|---|
| `three.module.min.js` 0.160.0 | **670.681 bytes** (654 KiB) |
| SHA-256 | `3e690ac7…65f69ba6`, bate com o `VERSAO.txt` |
| Licença | MIT, presente |
| Total que o repositório ganha | **~1,2 MB** (three + motor + adaptador + CSS + 3 WebP de fallback) |

**Esse número precisa ir à seção de limitações do artigo.** É a primeira dependência de
terceiros do projeto, num trabalho cuja decisão metodológica nº 1 — a
[ADR 0001](../decisoes/0001-motor-em-python-puro.md) — foi justamente **não** usar
biblioteca de inferência, para manter o sistema auditável. A cena não é o motor, e a
comparação não é direta, mas a tensão existe e precisa ser dita antes que alguém da banca
a note primeiro.

**(b) Testes do kit:** `pytest testes/unidade` → **40 passed**.

**(c) Contraste do texto sobre a cena:** não medido. Depende de a cena estar montada no
repositório, e a Fase 0 não altera o repositório. Fica para a Fase 1, com
`scripts/conferir_contraste.py`, que já existe e tem o mesmo cálculo que o kit pede.

**(d) Compatibilidade com a tela de espera atual — o achado que reduz o risco.**
`gerando.js` já escreve `data-etapa="N"` e `.passou-N` no véu, que é **exatamente o
contrato que o adaptador da cena observa**. A integração da tela de espera não exige
mudar `gerando.js`, nem o `ESPERA_MINIMA_MS` de 6 s, nem os textos dos passos. É sorte
boa, e torna a Fase 3 bem menos arriscada do que o plano do kit supõe.

### O que eu mudaria no kit

1. **A ADR da dependência vem antes da Fase 1, e não depois.** O kit a põe como registro
   a fazer durante a integração; ela é condição para começar. O modelo está em
   `references/decisao-three.md`.
2. **A Fase 2b (painel no formulário) deveria ser cortada, não adiada.** A tela de dados
   já tem o painel de leitura ao vivo, que é o elemento de maior valor pedagógico do
   sistema. Pôr uma cena 3D ao lado dele disputa atenção com o que já funciona, e a §9.3
   do plano de front-end justifica aquele painel por um motivo que a cena não substitui.
3. **Medir o custo de partida.** Um `canvas` WebGL na página inicial atrasa o primeiro
   desenho. O kit tem fallback para máquina sem aceleração, mas não mede o atraso em
   máquina com. Vale medir antes de decidir que a hero ganha cena — a landing é a primeira
   impressão, e uma hero que demora é pior que uma hero estática.
4. **A página da defesa é o item de maior valor imediato.** `defesa/apresentacao.html` é um
   arquivo único, abre com duplo clique, roda offline e **não toca no repositório**. Se
   fosse para fazer uma só coisa do kit antes do congelamento, seria revisar essa página:
   ela serve à banca em novembro, independentemente de a cena entrar ou não no sistema.

---

## 4. Ordem recomendada

```
AGORA (antes de 12/10, sem tocar no repositório)
  Fase 0 do kit ................................ FEITA, relatório acima
  Revisar defesa/apresentacao.html ............. opcional, fora do repo

12/10          CONGELAMENTO, tag congelamento-v1
20/10 a 14/11  COLETA DE USABILIDADE (nada muda na interface)
13/10 a 28/11  ARTIGO

DEPOIS DA COLETA, se houver tempo antes da entrega
  1. F1   acabamento da interface ............... 1-2 dias, risco baixo
  2. F2   seção de status ....................... meio dia
  3. ADR da dependência three.js ................ antes de qualquer código 3D
  4. F3   cena 3D, fases 1 → 2 → 3 → 4 .......... 3-4 dias, risco médio
  5. F4   fluidez entre telas ................... 1 dia
  6. F5   o que couber .......................... aberto
```

**O que a avaliação de usabilidade disser muda esta ordem.** É a razão mais forte para
fazer a coleta primeiro: a lista priorizada de correções que sai das dez heurísticas é um
dado melhor sobre o que melhorar do que qualquer plano escrito antes dela — **inclusive
este**.

---

## 5. O que este plano não propõe

- **Não propõe reescrever a landing.** A estrutura dela resiste à comparação com a
  referência; o que falta é acabamento.
- **Não propõe framework.** Nem React, nem cadeia de build. O sistema roda offline em
  `localhost`, e a ausência de build é uma propriedade, não uma falta.
- **Não propõe 3D no laudo.** O laudo é documento assinado por profissional habilitado. O
  kit concorda, e tem teste para isso.
- **Não propõe mexer no motor.** Nada aqui toca em cálculo, dose ou critério.
