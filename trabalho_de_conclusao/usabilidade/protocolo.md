# Protocolo da avaliação de usabilidade

Corresponde à Seção 4.4, dimensão (iii), da proposta, e substitui a subseção "Usabilidade"
de [`protocolo de validação`](../validacao/protocolo.md), que passa a remeter para cá.

**Decidido com o orientador em 24/09/2026 e simplificado em 10/10/2026.** A proposta
previa o questionário **SUS**. Em seu lugar: três roteiros de teste com usuários do
público-alvo e um questionário pós-teste estruturado pelas **dez heurísticas de
Nielsen**, com perguntas abertas ao final. A proposta foi corrigida nesse ponto.

**A simplificação de 10/10/2026, por orientação do orientador:** nada de termo assinado,
nada de ficha de papel. O participante usa o sistema e responde ao formulário — e é só
isso. O rascunho de TCLE e a ficha do participante foram removidos do repositório (o
histórico do Git os preserva); a caracterização do participante passou a ser a Seção 1 do
próprio formulário. As folhas de observação dos roteiros viraram anotação livre do
pesquisador, e não instrumento a preencher.

---

## 1. Por que trocar o SUS

O SUS entrega **um número** — de 0 a 100 — sobre a usabilidade percebida do sistema como
um todo. É barato, comparável e validado, e por isso é o instrumento mais usado em TCC.
Mas responde a uma pergunta só: *foi fácil de usar?*

O que este trabalho precisa saber é diferente. O SIRAS não é um aplicativo qualquer: é uma
ferramenta que emite um documento técnico do qual dependem decisões de adubação e, no
limite, projetos de crédito rural. Interessa saber **onde** a interface falha, **quanto**
cada falha atrapalha e **o que fazer** a respeito. Um escore de 71 não diz nada disso.

As dez heurísticas dão uma grade de diagnóstico: cada problema relatado já chega
classificado pela dimensão de usabilidade que ele viola, com uma severidade atribuída, e a
consolidação produz uma lista de correções priorizada em vez de um número.

**Perde-se a comparabilidade com a literatura de SUS.** Isso é custo real e vai declarado
na monografia. Ganha-se um diagnóstico acionável, que é o que o capítulo precisa entregar.

## 2. Como esta etapa deve ser nomeada — e por que isso importa

**Nome correto:** *teste de usabilidade com usuários do público-alvo, seguido de
questionário pós-teste estruturado pelas dez heurísticas de Nielsen (1994)*.

**Nome errado, a evitar em todo o texto:** *avaliação heurística*.

Avaliação heurística, no método de Nielsen e Molich (1990), é **inspeção conduzida por
especialistas em usabilidade**, tipicamente de 3 a 5, que examinam a interface contra as
heurísticas **sem usuários** e sem tarefas. O que se faz aqui é o oposto no desenho: são
usuários finais, executando tarefas reais, que depois avaliam o que viveram usando as
heurísticas como grade de leitura.

O desenho é legítimo e é mais informativo para este trabalho — os participantes são
especialistas **no domínio**, e é o julgamento agronômico deles sobre o laudo que mais
interessa. Mas chamá-lo pelo nome do outro método daria à banca uma objeção metodológica
gratuita, e justa.

**Duas ressalvas correlatas, que vão escritas na monografia e não escondidas:**

1. A escala de severidade de 0 a 4 de Nielsen é atribuída **a problemas**, por avaliadores
   treinados. Aqui ela é atribuída **a heurísticas**, por usuários. É adaptação declarada,
   e a média por heurística é estatística descritiva do que os participantes perceberam —
   não um índice de severidade no sentido original.
2. O que a escala mede, portanto, é **percepção de gravidade pelo usuário**, não gravidade
   técnica. As duas costumam correlacionar, mas não são a mesma coisa: um problema que
   bloqueia uma tarefa e que o usuário contorna sem perceber recebe nota baixa.

## 3. Participantes

| Item | Definição |
|---|---|
| Quantidade | 5 a 8, mais 1 no piloto (que não entra na amostra) |
| Perfil | Agrônomos, técnicos agrícolas e estudantes concluintes de agronomia — o público-alvo declarado na proposta |
| Critério de inclusão | Ter, na rotina, contato com análise de solo ou recomendação de adubação |
| Critério de exclusão | Ter participado do desenvolvimento ou já conhecer o SIRAS |
| Recrutamento | Contato direto do autor; registrado como pendência **P8** no `docs/processo/roadmap.md` |
| Compensação | Nenhuma |

**Por que 5 a 8.** Nielsen e Landauer (1993) mostram que cerca de cinco participantes
revelam a maior parte dos problemas de usabilidade de uma interface, e que o retorno por
participante adicional cai rápido. Oito dá margem para perfis heterogêneos — campo e
escritório, mais e menos familiarizados com ferramenta digital — sem estender a coleta.

**O que a amostra não permite.** Nada de inferência estatística. As médias de severidade
são descritivas, e assim devem ser apresentadas: sem teste de hipótese, sem intervalo de
confiança, sem generalização para a população de agrônomos. Esta etapa **não testa as
hipóteses** H1.1 e H1.2, como a própria proposta já declara.

## 4. Desenho: duas partes

Decidido em 24/09/2026. A sessão e o questionário ficam separados.

**Parte 1 — sessão de roteiros (~35 min), com o pesquisador presente.**

| Roteiro | O quê | Duração | Quem conduz |
|---|---|---|---|
| [R1](roteiros/roteiro-1-demonstracao.md) | Cenário pronto, demonstrado pelo pesquisador. Primeiro contato: mostra o que a ferramenta faz e como se navega | ~10 min | Pesquisador |
| [R2](roteiros/roteiro-2-cenario-guiado.md) | Cenário pronto em ficha impressa, preenchido pelo participante **sozinho** | ~15 min | Participante |
| [R3](roteiros/roteiro-3-livre.md) | O participante escolhe cultura e dados e gera um laudo livre | ~10 min | Participante |

**Parte 2 — questionário (~15 min), respondido depois, no Google Forms.**

Fora da sessão de propósito. Respondido com o pesquisador olhando, o participante tende a
suavizar a crítica; e as dez seções mais as abertas cansam ao fim de 35 minutos de tarefa.
O formulário fica com **"permitir edição de resposta"** ligado, para que se possa pausar e
retomar.

**Por que R1 vem antes de R2.** É treinamento deliberado. Este teste não mede
descobribilidade em primeiro uso sem ajuda — mede se a ferramenta serve a quem foi
apresentado a ela, que é o cenário real de adoção. Isso vai declarado nas ameaças à
validade (§9).

## 5. Ambiente

- SIRAS rodando em `localhost`, na máquina do pesquisador, na versão congelada da §8.
- Presencial quando possível; remoto por videochamada com **controle remoto** cedido ao
  participante, nunca só compartilhamento de tela — em R2 e R3 é o participante que digita.
- Gravação de tela **só se o participante concordar**, perguntado de viva voz, e sem
  áudio nem imagem dele. Serve para o pesquisador reconstruir o que aconteceu.
- Navegador em janela limpa, sem histórico de sessões anteriores.

## 6. Instrumentos

**Um instrumento só.** O [questionário](questionario.md), no
Google Forms, com a caracterização do participante na Seção 1. Os
[roteiros](roteiros/) são material do pesquisador para conduzir a sessão, não papel que o
participante preenche.

**Identificação.** Cada participante recebe um **código** (`P1` a `P8`) dito na hora do
teste, e é por ele que o formulário identifica a resposta. A coleta de e-mail fica
**desligada**: sem termo e sem cadastro, guardar e-mail seria dado pessoal sem
finalidade.

**Antes de aplicar:** o orientador pediu para revisar o formulário montado. Mandar o link
a ele antes da primeira sessão.

## 7. O que se coleta

**Na sessão (anotação livre do pesquisador, sem formulário a preencher):**

- se a tarefa foi concluída, concluída com ajuda, ou não concluída;
- em que passo a pessoa hesitou, se voltou atrás, e o que disse enquanto fazia;
- erros de preenchimento e como a interface reagiu a eles;
- perguntas feitas ao pesquisador — cada pergunta é um ponto em que a tela não respondeu
  sozinha.

Tempo de tarefa **não** é métrica primária. Com amostra desta dimensão e primeiro contato
guiado, tempo mede mais a conversa do que a interface. Anota-se, e não se conclui dele.

**No questionário:** severidade de 0 a 4 por heurística; descrição livre das falhas e da
tela em que ocorrem; sugestões de melhoria; e quatro perguntas abertas finais.

## 8. Congelamento da versão avaliada

**A interface é congelada antes da primeira sessão e não muda até a última.** Corrigir um
problema no meio da coleta faria os participantes avaliarem sistemas diferentes, e as
médias por heurística deixariam de somar.

- A versão avaliada recebe a tag Git `congelamento-v1`, e o commit fica registrado no
  relatório.
- Problema encontrado durante a coleta é **anotado**, não corrigido.
- Exceção única: defeito que **impeça** a conclusão de um roteiro para todos os
  participantes seguintes. Nesse caso a correção é feita, a tag avança, e o relatório
  declara quais participantes usaram qual versão.
- O orientador fixou isso de forma independente: **a partir de segunda, 12/10/2026, o
  aplicativo não recebe mais alteração.** O foco passa a ser teste com usuários e artigo.

## 9. Ameaças à validade

Declaradas aqui para irem ao texto, e não descobertas na arguição.

| # | Ameaça | Mitigação |
|---|---|---|
| 1 | **O pesquisador é o autor do sistema.** O participante tende a poupar a crítica de quem está do lado dele | Questionário respondido fora da sessão e sem o pesquisador; a abertura do formulário diz, com todas as letras, que a crítica é o resultado útil |
| 2 | **R1 treina o participante** antes de R2 e R3 | Declarada como escolha de desenho: mede-se adoção assistida, não descoberta autônoma |
| 3 | **Severidade por heurística, respondida por usuário**, não é a severidade de Nielsen | Adaptação declarada na §2; resultados apresentados como percepção, não como índice |
| 4 | **Amostra pequena e por conveniência** | Sem inferência estatística; resultados descritivos e qualitativos |
| 5 | **A heurística 10 (ajuda e documentação) tende a pontuar alto** num sistema sem seção de ajuda, e isso pode inflar a média geral de severidade | Relatar por heurística, nunca só a média global |
| 6 | **O participante avalia a recomendação agronômica junto com a interface** — e as duas são coisas distintas | A pergunta aberta final separa explicitamente os dois juízos; divergências agronômicas vão para a auditoria do orientador (CCAE §10), não para o capítulo de usabilidade |

## 10. Análise dos resultados

`scripts/consolidar_heuristicas.py` lê o CSV exportado do Google Forms e produz, num
comando, o material da monografia:

- **por heurística:** média, mediana, mínimo, máximo e número de respostas;
- **ranking de prioridade** pela média de severidade, do maior para o menor;
- **todos os relatos** de falha e sugestão, agrupados por heurística e identificados pelo
  código do participante;
- saída em Markdown e CSV.

Mediana ao lado da média de propósito: com cinco a oito respostas, um avaliador severo
desloca a média inteira, e ver os dois números juntos mostra quando isso aconteceu.

A consolidação vira uma **lista de correções priorizada**, que é o produto desta etapa. O
que for corrigido antes da entrega é registrado com a heurística que originou a correção —
é assim que o capítulo mostra que a avaliação teve efeito, e não só resultado.

## 11. Cronograma

| Etapa | Janela | Depende de |
|---|---|---|
| Congelamento da interface, tag `congelamento-v1` | 12/10/2026 | suíte completa passando |
| Piloto com 1 participante, fora da amostra | 13–17/10/2026 | formulário montado e revisado pelo orientador |
| Coleta com 5 a 8 participantes | 20/10 a 14/11/2026 | recrutamento (P8) |
| Consolidação e redação da seção | 17–28/11/2026 | — |

A proposta concentra a usabilidade em novembro. A antecipação para outubro é folga ganha
com S3 e S4 concluídos antes do previsto, e cabe numa nota de rodapé — não exige alterar o
cronograma da proposta.

## 12. O que depende do autor

1. **Recrutar os participantes** (P8) — é o caminho crítico desta etapa.
2. **Completar as fichas de análise de solo** de R1 e R2: os roteiros trazem os campos que
   vêm de casos já conferidos, e marcam `PREENCHER` os que faltam. Ver a nota de cada
   roteiro sobre por que esses campos não foram preenchidos por antecipação.
3. **Montar o formulário no Google Forms** a partir de
   [`questionario.md`](questionario.md)
   **e mandar o link ao orientador para revisão**, que foi o que ele pediu.

## Referências

NIELSEN, J. **Enhancing the explanatory power of usability heuristics.** In: Proceedings of
the SIGCHI Conference on Human Factors in Computing Systems (CHI '94). Boston: ACM, 1994.
p. 152–158.

NIELSEN, J.; MOLICH, R. **Heuristic evaluation of user interfaces.** In: Proceedings of the
SIGCHI Conference on Human Factors in Computing Systems (CHI '90). Seattle: ACM, 1990.
p. 249–256.

NIELSEN, J.; LANDAUER, T. K. **A mathematical model of the finding of usability problems.**
In: Proceedings of the INTERACT '93 and CHI '93 Conference on Human Factors in Computing
Systems. Amsterdam: ACM, 1993. p. 206–213.
