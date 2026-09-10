# Roadmap e estado do projeto

Atualize a coluna **Estado** ao concluir cada etapa. Legenda: `pendente` · `em andamento` ·
`concluído` · `bloqueado`.

## Pendências que dependem de terceiros (resolver primeiro)

| # | Pendência | Por quê | Estado |
|---|---|---|---|
| P1 | Definir o oráculo da aptidão edáfica (fonte independente + agrônomo para classificação às cegas) | Sem isso, a H1.2 é circular e o teste não mede nada | resolvido — H0.2/H1.2 removidas da proposta; aptidão migrou de hipótese de validação para objetivo de projeto, verificado por conformidade da implementação frente ao Caderno de Critérios de Aptidão Edáfica (`docs/CCAE-v1.1.md`, aprovado pelo orientador por e-mail em 10/09/2026 14:04 — transcrição no Apêndice D do Caderno; tag prevista `criterios-v1.1`), não por painel de especialistas. Auditoria agronômica qualitativa (parecer do orientador sobre laudos gerados) registrada como complemento, sem percentual — ver CCAE §10 |
| P2 | Confirmar necessidade de CEP/TCLE para o teste de usabilidade | Trâmite leva semanas; descobrir em novembro inviabiliza o capítulo | concluído — Confirmado que a avaliação de usabilidade não requer submissão ao CEP. Será aplicado TCLE aos participantes. (confirmado com o orientador Rafael Rieder) |
| P3 | Corrigir a proposta: método de calagem (SMP), atribuição do SUS, referência Ramalho Filho & Beek | Erros conhecidos no texto atual | em andamento |
| P4 | Localizar na literatura autores que tenham adotado parâmetro ou procedimento equivalente às decisões de julgamento do Apêndice A do CCAE (calagem) | Pedido do orientador no e-mail de aprovação de 10/09/2026: citar terceiros dá robustez à justificativa e mostra que a escolha não se apoia apenas no manual. Não é condição da aprovação, que já está dada | pendente — busca do autor; alvo: monografia e artigo |

## Sprints

| Sprint | Período | Entregável | Estado |
|---|---|---|---|
| S0 | 16–31/08 | Repositório, ambiente, estrutura, `dados/comum/` transcrito, `AnaliseSolo` + carregador + `Trace` | concluído |
| S1 | 01–15/09 | `motor/calagem.py` completo e testado; `mapa_culturas.json` com as 21 culturas de grãos; `motor/adubacao.py` consumindo `graos_adubacao_n/pk.json` | concluído — `motor/calagem.py` cobre os 15 critérios de grãos (`graos_pd_com_restricoes` implementado em 2026-08-23: decisão pela subsuperfície, dose por SMP médio das duas camadas — ver ADR 0003 D6 e ADR 0002 D10 — com CAL-10/CAL-11 como oráculo); `mapa_culturas.json` e `motor/adubacao.py` prontos |
| S2 | 16–30/09 | 21 grãos; formulário web; laudo em tela; **aptidão v0**; fluxo ponta a ponta — **marco M1** | pendente |
| S3 | 01–15/10 | Hortaliças (18), tubérculos (2), cana e tabaco | concluído — `motor/adubacao.py` cobre N/P2O5/K2O das 18 hortaliças, 2 tubérculos, cana (2 ciclos) e tabaco (2 tipos), com `grupo_exigencia` explícito por cultura (Anexo 2, p. 361-365) em vez de suposição; casos ADU-08/09/10/13/14 conferem |
| S4 | 16–31/10 | Frutíferas (17, três fases) e erva-mate — **marco M2** | concluído — `motor/adubacao.py` cobre as 17 frutíferas em pré-plantio e crescimento, e a manutenção nos formatos taxa/tonelada (8 culturas), bespoke (amoreira-preta, mirtileiro, morangueiro, nogueira-pecã — ADR 0004 D4.7) e correspondência solo-tecido da videira (N e P; K permanece pendente por decisão do Manual, D4.6); erva-mate (3 fases + recuperação); casos ADU-11/12/15-19 conferidos e com `referencia` (ADU-15 confirmado pelo autor em 2026-08-23, p. 199). Só ameixeira, macieira e pêssego/nectarina ficam fora de escopo na manutenção (teor foliar sem correspondência solo-tecido, D4.6) — pré-plantio e crescimento continuam cobertos |
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
| a | Estruturação da base de conhecimento (JSON) | em andamento — `dados/comum/` e a adubação dos 6 grupos (grãos, hortaliças, tubérculos, outras, frutíferas, erva-mate) transcritas e conferidas; falta `corretivos.json` (Cap. 8) e três lacunas que a conformidade da aptidão expôs: `grupo_p`/`grupo_k` da **alfafa** e do **gengibre** (Anexo 2, p. 361-366) e o mapeamento das **espécies florestais** em `mapa_culturas.json` para o critério `erva_mate_e_florestais` — ver CCAE-v1.1.md, Apêndice B, B-2 a B-4 |
| b | Definição formal das regras SE-ENTÃO | em andamento |
| c | Definição dos critérios de aptidão edáfica | concluído — `docs/CCAE-v1.1.md` (aprovado pelo orientador em 10/09/2026, Apêndice D), F1-F7 rastreados ao Manual e a Ramalho Filho &amp; Beek (1995); motor em `siras/motor/aptidao.py` (docs/decisoes/0005) |
| d | Módulo de entrada de dados | pendente |
| e | Motor de inferência | em andamento |
| f | Módulos de recomendação e aptidão | em andamento — `siras/motor/aptidao.py` implementado e verificado contra o `docs/CCAE-v1.1.md`; contrato de 3 argumentos do CCAE exposto por `avaliar_aptidao_ccae()`; sinonímia de nomes de cultura resolvida em duas camadas (`siras/dominio/nomes.py` + `dados/comum/aliases_culturas.json`) |
| g | Conjunto de casos de teste e oráculo | em andamento — conjunto de 84 casos integrado (`testes/casos/entradas_aptidao.json` + `gabarito_aptidao.csv`, separados para preservar a independência do gabarito); runner em `testes/unidade/test_conformidade_aptidao.py`. `validar_anexo1.py` passa 32/32 contra as Tab. A.2/A.3 do Anexo 1 (oráculo externo). Conformidade de classe e de fator determinante: **77/80 = 96,25%**. As 3 divergências e mais 1 de gabarito estão em CCAE-v1.1.md, Apêndice B (B-1 a B-4) — todas por lacuna da base de conhecimento ou do gabarito, nenhuma por defeito do motor; todas dependem do autor |
| h | Validação e análise dos resultados | pendente |
| i | Avaliação de usabilidade | pendente |
| j | Redação final | pendente |
