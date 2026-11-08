# Questionário pós-teste — as dez heurísticas de Nielsen

**Para colar no Google Forms.** Cada bloco numerado abaixo é uma **seção** do formulário.
Texto em citação (`>`) é o que o participante lê; o resto são instruções para o autor.
**Não cole nada que não esteja em `>`.**

Protocolo em [`protocolo`](protocolo.md). O enunciado de cada heurística está
em linguagem de agrônomo e adaptado ao SIRAS, seguindo a orientação do orientador — não é
a redação genérica de Nielsen, e sim a pergunta que o público-alvo consegue responder sobre
**este** sistema.

---

## Versão aplicada — revisão do orientador (antes da coleta, novembro de 2026)

O orientador revisou o formulário no Google Forms antes da primeira sessão. **A versão
aplicada aos 8 participantes é a do Forms**, e não a redação abaixo. Os enunciados da
versão aplicada, como saíram no CSV exportado, são estes; as opções de cada pergunta
fechada estão no Forms. Três mudanças importam para a análise:

1. **Tratamento por "você"** em vez de "tu" (o script aceita as duas formas).
2. **Perguntas finais de 5 para 4.** As antigas 12.3a (sobre a ferramenta) e 12.3b (sobre a
   recomendação) viraram uma pergunta só. Isso reabre a ameaça 6 do protocolo (§9): a
   resposta mistura o juízo sobre a interface e o juízo sobre a recomendação, e o artigo
   declara essa limitação.
3. A pergunta de recomendação passou a pedir também se o participante **concorda com os
   resultados**.

| Seção | Enunciado aplicado |
|---|---|
| 1 | Código do participante (eu te passo na hora do teste — P1, P2, ...) |
| 1 | Qual a sua formação/atuação? |
| 1 | Há quanto tempo você trabalhas com análise de solo ou recomendação de adubação? |
| 1 | Como você faz a recomendação hoje? Marca todas as que se aplicam. |
| 1 | Como você se sente ao usar ferramentas digitais no trabalho? |
| 1 | Como você usou o sistema SIRAS? |
| 1 | Você já conhecias o SIRAS antes deste teste? |
| 2–11 | Hn — Qual a gravidade dos problemas que encontraste neste aspecto? |
| 2–11 | Hn — Descreva o que deu errado e em que tela aconteceu. |
| 2–11 | Hn — O que você faria diferente? |
| 12 | Se você pudesse alterar apenas uma coisa no SIRAS, qual seria? |
| 12 | Você usaria essa ferramenta no seu trabalho? Por quê? |
| 12 | Em relação à recomendação agronômica gerada pelo sistema: ela é confiável, clara e útil? Você concorda com os resultados? Recomendaria essa recomendação ao produtor exatamente como está? |
| 12 | Falta algo no sistema para que ele atenda perfeitamente à sua rotina de trabalho? Se sim, o quê? |

O texto abaixo fica como registro do desenho original e das justificativas de cada
pergunta.

---

## Configuração do formulário

| Ajuste | Valor | Por quê |
|---|---|---|
| Coletar endereços de e-mail | **Desligado** | Não há termo nem cadastro: a Seção 1 já caracteriza quem respondeu, e e-mail seria dado pessoal guardado sem necessidade |
| Permitir edição de resposta | **Ligado** | São dez seções; a pessoa precisa poder pausar e retomar |
| Limitar a uma resposta | **Desligado** | Exigiria login e, com ele, a conta Google do participante |
| Ordem embaralhada | **Desligado** | As heurísticas têm ordem canônica e devem sair na mesma ordem para todos |
| Barra de progresso | **Ligada** | Dez seções sem barra parecem não acabar, e a taxa de abandono sobe |

**Sem termo de consentimento.** Decisão do orientador em 10/10/2026: a avaliação não
requer submissão ao CEP (pendência P2) e **não exige termo assinado** — basta o
participante responder ao formulário. O rascunho de TCLE que existia foi removido do
repositório; o histórico do Git o preserva, caso a banca pergunte. A abertura do
formulário diz, mesmo assim, que a participação é voluntária e pode ser interrompida: isso
não é termo, é o mínimo que se diz a quem dá o próprio tempo.

### Duas regras que o script de consolidação depende de que sejam seguidas

1. **Todo enunciado de pergunta é único.** O Forms usa o enunciado como nome da coluna do
   CSV. Se as dez heurísticas tivessem a mesma pergunta, o CSV teria dez colunas de mesmo
   nome — e o leitor de CSV guardaria só a última, transformando dez heurísticas em uma.
   Por isso as perguntas A, B e C de cada heurística levam o prefixo **`H1 —` a `H10 —`**.
   Não o remova. O script recusa, com mensagem explicando, um CSV com colunas repetidas.
2. **Nas perguntas abertas finais, evite as palavras "gravidade", "descreve", "deu errado"
   e "diferente".** São elas que o script usa para reconhecer as colunas das heurísticas.

---

## Seção 1 — Abertura e identificação

**Título:** `Avaliação de usabilidade do SIRAS`

**Descrição:**

> Obrigado por participar. Este formulário tem dez blocos, um para cada aspecto de
> usabilidade, e quatro perguntas abertas no final. Leva cerca de quinze minutos, e tu
> podes pausar e retomar depois — a resposta fica salva.
>
> Responde pensando **no que tu viveste** ao usar o sistema: a demonstração, o cenário
> que tu preencheste sozinho e o laudo que tu geraste livremente.
>
> **O que me serve é a crítica.** Nota baixa não me magoa; nota alta que esconde um
> problema me faz entregar um sistema pior. Se alguma coisa te irritou, escreve.
>
> A participação é voluntária: tu podes parar a qualquer momento, sem precisar explicar
> por quê. Tu não precisas te identificar, e nenhuma resposta será publicada com teu nome.
> As primeiras perguntas servem só para descrever o perfil do grupo que avaliou.
>
> ---
>
> **A escala de 0 a 4**, a mesma em todos os blocos:
>
> - **0** — Não é um problema.
> - **1** — Problema estético: incomoda, mas não atrapalha o uso.
> - **2** — Problema leve: atrapalha pouco, dá para contornar.
> - **3** — Problema grave: atrapalha muito e atrasa o trabalho.
> - **4** — Catástrofe: impede de usar, ou faz sair informação errada.
>
> Se tu não passaste pela situação de algum bloco, marca **Não observei** — é diferente
> de dar zero.

*Nota para o autor, não colar:* as perguntas de caracterização abaixo estavam numa ficha
de papel à parte e foram trazidas para dentro do formulário em 10/10/2026, por orientação
do orientador: um instrumento só, sem burocracia em volta. São elas que permitem ler as
notas com contexto — severidade alta vinda de quem usa ferramenta digital todo dia
significa coisa diferente da mesma nota vinda de quem nunca usou.

**Pergunta 1.1** — *Resposta curta, obrigatória*

> Código do participante (eu te passo na hora do teste — P1, P2, ...)

**Pergunta 1.2** — *Múltipla escolha, obrigatória, com a opção "Outro" (texto) ligada*

> Qual a tua formação/atuação?

- Engenheiro(a) agrônomo(a)
- Técnico(a) agrícola
- Estudante de agronomia
- Outro: ______

**Pergunta 1.3** — *Múltipla escolha, obrigatória*

> Há quanto tempo tu trabalhas com análise de solo ou recomendação de adubação?

- Ainda não atuo
- Menos de 2 anos
- 2 a 5 anos
- 6 a 10 anos
- Mais de 10 anos

**Pergunta 1.4** — *Caixas de seleção, obrigatória*

> Como tu fazes a recomendação hoje? Marca todas as que se aplicam.

- À mão, com o Manual
- Planilha própria
- Software de cooperativa ou revenda
- Sistema do laboratório
- Não faço recomendação

*Caixas de seleção, e não múltipla escolha, porque é comum usar mais de um método — o
laboratório interpreta, o técnico confere no Manual.*

**Pergunta 1.5** — *Múltipla escolha, obrigatória*

> Qual o teu conforto com ferramentas digitais no trabalho?

- Muito confortável
- Confortável
- Neutro
- Pouco confortável
- Desconfortável

**Pergunta 1.6** — *Múltipla escolha, obrigatória*

> Como tu usaste o sistema?

- Presencialmente, no computador do pesquisador
- Remotamente, com controle da tela

**Pergunta 1.7** — *Múltipla escolha, obrigatória*

> Tu já conhecias o SIRAS antes deste teste?

- Não
- Sim, já tinha visto ou usado

*Confirma o critério de exclusão do protocolo (§3). Uma resposta "Sim" não é descartada
automaticamente: é anotada e decidida caso a caso, e a decisão vai declarada.*

---

## Seções 2 a 11 — as dez heurísticas

**Estrutura idêntica em todas as dez.** Substitua o título, a descrição e o número do
prefixo `Hn —` nas três perguntas.

**Ao final de cada descrição, cole este lembrete:**

> Se tu deste 3 ou 4, por favor descreve na pergunta seguinte — sem a descrição eu não
> consigo corrigir.

- **Pergunta A** — *Múltipla escolha, obrigatória*
  Enunciado: `Hn — Qual a gravidade dos problemas que tu encontraste neste aspecto?`
  Opções, exatamente nesta ordem e com o número no início:
  - `0 — Não é problema`
  - `1 — Problema estético: incomoda, mas não atrapalha o uso`
  - `2 — Problema leve: atrapalha pouco, dá para contornar`
  - `3 — Problema grave: atrapalha muito e atrasa o trabalho`
  - `4 — Catástrofe: impede de usar, ou faz sair informação errada`
  - `Não observei — não passei por essa situação`
- **Pergunta B** — *Parágrafo, opcional*
  `Hn — Descreve o que deu errado e em que tela aconteceu.`
- **Pergunta C** — *Parágrafo, opcional*
  `Hn — O que tu farias diferente?`

> **Por que múltipla escolha, e não escala linear.** Por dois motivos. A escala linear
> não tem lugar para "Não observei", e sem ela quem não passou pela situação é empurrado
> para o 0 — que é uma afirmação ("não é problema"), e puxaria a média para baixo. É o
> caso típico da H7 (quem não lançou vários talhões) e da H9 (quem não errou nenhum campo
> não viu mensagem de erro). E a múltipla escolha deixa o rótulo da nota à vista em cada
> bloco, sem obrigar a pessoa a voltar à Seção 1 para lembrar o que é "2".
>
> O script lê o número no início da opção e ignora o rótulo; "Não observei" fica fora da
> média e é contado à parte, na coluna *Não observou* do relatório.
>
> **Por que B não é obrigatória para nota 3 ou 4.** O Forms só desvia de seção a partir de
> múltipla escolha, e B está na mesma seção que A: tornar B condicional exigiria uma seção
> extra por heurística — vinte seções em vez de dez, e a barra de progresso andando pela
> metade. O lembrete na descrição faz o mesmo papel sem o custo. Nota alta sem descrição
> continua sendo o pior resultado possível, e é por isso que o lembrete está em todas.

### Seção 2 — Heurística 1: Visibilidade do status do sistema

> O sistema te deixa saber o que está acontecendo? Por exemplo: enquanto o laudo é gerado,
> fica claro que ele está sendo processado e o que está sendo consultado? Quando tu digitas
> um teor, dá para perceber na hora em que classe ele caiu? Quando uma ação dá certo, o
> sistema avisa?

### Seção 3 — Heurística 2: Correspondência com o mundo real

> Os termos, as unidades e os nomes de cultura são os que tu usas no teu trabalho? O
> sistema fala a língua da agronomia — pH, SMP, PRNT, CTC, cmolc/dm³ — ou aparecem palavras
> de computador que não dizem nada para quem é do campo? A sequência de telas segue a ordem
> em que tu efetivamente farias a coisa?

### Seção 4 — Heurística 3: Controle e liberdade do usuário

> Quando tu erras — escolhe a cultura errada, digita o teor no campo trocado —, é fácil
> voltar atrás? Dá para editar a análise depois de gerar o laudo sem ter de preencher tudo
> de novo? Tu te sentiste preso em alguma tela, sem saída visível?

### Seção 5 — Heurística 4: Consistência e padrões

> As telas se parecem entre si? Botões parecidos fazem coisas parecidas, as cores querem
> dizer sempre a mesma coisa, e as informações ficam sempre no mesmo lugar? O laudo na tela
> e a versão impressa dizem a mesma coisa?

### Seção 6 — Heurística 5: Prevenção de erros

> O sistema te impede de errar por distração? Por exemplo: avisa quando falta um campo
> obrigatório, antes de deixar tu gerares um laudo incompleto; impede valor impossível numa
> análise de solo; deixa claro quando uma variável é exigida para aquela cultura
> específica?

### Seção 7 — Heurística 6: Reconhecimento em vez de memorização

> Tu precisaste decorar alguma coisa de uma tela para usar na seguinte? As informações de
> que tu precisavas para decidir estavam à vista, ou tu tiveste de lembrar o que havia
> preenchido antes? As opções de cultura, manejo e fase estavam visíveis, ou era preciso
> saber de antemão qual escolher?

### Seção 8 — Heurística 7: Flexibilidade e eficiência de uso

> Pensando em usar isso **toda semana**, e não uma vez só: o sistema te deixa trabalhar
> rápido? Lançar vários talhões no mesmo laudo funciona bem? Corrigir um número e gerar o
> laudo de novo, sem redigitar a análise inteira, é rápido? Alguma etapa te pareceu lenta
> ou repetitiva demais para quem faz isso todo dia?
>
> *O que falta no sistema — um recurso que não existe — vai na última seção. Aqui, avalia
> o que existe.*

*Por que a ressalva:* a versão anterior desta pergunta sugeria recursos que o SIRAS não
tem (repetir análise anterior, salvar manejo, importar do laboratório). Isso transformava a
nota de gravidade numa lista de desejos e duplicava a 12.4. Os desejos continuam
bem-vindos — na 12.4, onde não contaminam a severidade.

### Seção 9 — Heurística 8: Estética e design minimalista

> As telas mostram o que interessa, ou há excesso de texto e de informação competindo pela
> tua atenção? O laudo tem coisa demais? Tem coisa de menos? Alguma seção tu simplesmente
> não usaria?

### Seção 10 — Heurística 9: Ajuda para reconhecer e corrigir erros

> Quando algo deu errado — campo faltando, valor recusado, combinação que o sistema não
> cobre —, a mensagem explicou o problema em português claro e disse o que fazer? Ou
> apareceu um texto técnico que não ajudava?

### Seção 11 — Heurística 10: Ajuda e documentação

> Se te desse uma dúvida sobre como usar alguma função, dava para achar ajuda dentro do
> próprio sistema? As explicações que existem — a apresentação em três passos que aparece
> na tela inicial, as notas dos campos, as tabelas do Manual, a trilha de onde vem cada
> número — foram suficientes?

---

## Seção 12 — Perguntas abertas finais

**Título:** `Para fechar`

**Descrição:**

> Quatro perguntas abertas, a terceira em duas partes. São as mais importantes do formulário — responde com o que te
> vier, sem filtrar.

**Pergunta 12.1** — *Parágrafo, obrigatória*

> Se tu pudesses mudar **uma coisa só** no SIRAS, qual seria?

**Pergunta 12.2** — *Parágrafo, obrigatória*

> Tu usarias essa ferramenta no teu trabalho? Por quê — ou por que não?

**Pergunta 12.3a** — *Parágrafo, obrigatória*

> **Sobre a ferramenta:** ela é confiável, clara, útil?

**Pergunta 12.3b** — *Parágrafo, obrigatória*

> **Sobre a recomendação agronômica** que ela gerou: tu concordas com ela? Recomendarias
> ao produtor como está?

*Por que 12.3a e 12.3b são campos separados, e não um só:* o participante avalia a interface e a
recomendação ao mesmo tempo, e as duas coisas são distintas (protocolo, §9, ameaça 6).
Num campo só, as respostas misturam os dois juízos e cabe ao autor separá-los depois, por
interpretação — exatamente o que não se quer. Divergência agronômica vai para a auditoria
do orientador, não para o capítulo de usabilidade. "Recomendarias ao produtor", e não
"assinarias o laudo": estudante não assina, e técnico agrícola tem atribuição limitada —
a pergunta precisa servir a toda a amostra.

**Pergunta 12.4** — *Parágrafo, obrigatória*

> Falta alguma coisa no sistema para que ele servisse à tua rotina de verdade? O quê?

---

## Depois da coleta

Exporte as respostas em CSV pela aba **Respostas** e rode, da raiz do repositório:

```
py siras/scripts/consolidar_heuristicas.py respostas.csv --saida trabalho_de_conclusao/validacao/resultados/
```

O script produz, por heurística, média, mediana, mínimo, máximo, contagem e quantos
marcaram "Não observei"; o ranking de prioridade; e todos os relatos agrupados,
identificados pelo código do participante. Saída em Markdown e CSV, prontos para a
monografia.

**Antes da primeira sessão real**, responda o formulário uma vez você mesmo, exporte o CSV
e rode o comando acima. Se o script reclamar de colunas repetidas, algum enunciado ficou
sem o prefixo `Hn —`.
