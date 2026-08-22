# Roadmap e estado do projeto

Atualize a coluna **Estado** ao concluir cada etapa. Legenda: `pendente` · `em andamento` ·
`concluído` · `bloqueado`.

## Pendências que dependem de terceiros (resolver primeiro)

| # | Pendência | Por quê | Estado |
|---|---|---|---|
| P1 | Definir o oráculo da aptidão edáfica (fonte independente + agrônomo para classificação às cegas) | Sem isso, a H1.2 é circular e o teste não mede nada | pendente |
| P2 | Confirmar necessidade de CEP/TCLE para o teste de usabilidade | Trâmite leva semanas; descobrir em novembro inviabiliza o capítulo | concluído — Confirmado que a avaliação de usabilidade não requer submissão ao CEP. Será aplicado TCLE aos participantes. (confirmado com o orientador Rafael Rieder) |
| P3 | Corrigir a proposta: método de calagem (SMP), atribuição do SUS, referência Ramalho Filho & Beek | Erros conhecidos no texto atual | em andamento |

## Sprints

| Sprint | Período | Entregável | Estado |
|---|---|---|---|
| S0 | 16–31/08 | Repositório, ambiente, estrutura, `dados/comum/` transcrito, `AnaliseSolo` + carregador + `Trace` | em andamento |
| S1 | 01–15/09 | `motor/calagem.py` completo e testado; 10 culturas de grãos transcritas; `motor/adubacao.py` | pendente |
| S2 | 16–30/09 | 21 grãos; formulário web; laudo em tela; **aptidão v0**; fluxo ponta a ponta — **marco M1** | pendente |
| S3 | 01–15/10 | Hortaliças (18), tubérculos (2), cana e tabaco | pendente |
| S4 | 16–31/10 | Frutíferas (17, três fases) e erva-mate — **marco M2** | pendente |
| S5 | 01–15/11 | Aptidão v1; 60–80 casos de teste com oráculo; script de concordância | pendente |
| S6 | 16–30/11 | Validação, análise de discordâncias, comparação com FertFacil, SUS | pendente |
| S7 | 01–07/12 | Revisão final, formatação, slides, ensaio | pendente |

Redação da monografia: contínua a partir de S2. Ao fim de cada sprint, escrever o parágrafo
correspondente enquanto o assunto está fresco.

## Camadas de escopo (definição de pronto)

Se houver atraso, o escopo é reduzido por camadas, nesta ordem — nunca sacrificando a validação:

1. **Mínimo defensável:** núcleo comum + 21 grãos + laudo + aptidão v0 (alvo: M1)
2. **Alvo da proposta:** + hortaliças, tubérculos, cana e tabaco (alvo: M2)
3. **Completo:** + frutíferas e erva-mate (alvo: 15/11)
4. **Extra:** persistência em SQLite, deploy remoto

## Etapas do método (Seção 4.3 da proposta)

| | Etapa | Estado |
|---|---|---|
| a | Estruturação da base de conhecimento (JSON) | em andamento |
| b | Definição formal das regras SE-ENTÃO | pendente |
| c | Definição dos critérios de aptidão edáfica | bloqueado por P1 |
| d | Módulo de entrada de dados | pendente |
| e | Motor de inferência | pendente |
| f | Módulos de recomendação e aptidão | pendente |
| g | Conjunto de casos de teste e oráculo | pendente |
| h | Validação e análise dos resultados | pendente |
| i | Avaliação de usabilidade | bloqueado por P2 |
| j | Redação final | pendente |
