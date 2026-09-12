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
| P5 | Aprovar o rascunho do CCAE v1.2 com o orientador (`docs/CCAE-v1.2.md`) | Clarifica a §7.1, ramo (b), ligando F1 à dose em vez do gatilho — fecha B-5 e B-6 sem alterar limiar nem gabarito. Antes de submeter, resolver a única cláusula em aberto: se F1 lê `NC` antes ou depois do arredondamento de apresentação | concluído — cláusula de precisão de `NC` decidida pelo autor (leitura antes do arredondamento, porque arredondar antes do corte tornaria o limiar efetivo função da CTC); aprovada pelo orientador em reunião de 10/09/2026; congelada na tag `criterios-v1.2` |

## Sprints

| Sprint | Período | Entregável | Estado |
|---|---|---|---|
| S0 | 16–31/08 | Repositório, ambiente, estrutura, `dados/comum/` transcrito, `AnaliseSolo` + carregador + `Trace` | concluído |
| S1 | 01–15/09 | `motor/calagem.py` completo e testado; `mapa_culturas.json` com as 21 culturas de grãos; `motor/adubacao.py` consumindo `graos_adubacao_n/pk.json` | concluído — `motor/calagem.py` cobre os 15 critérios de grãos (`graos_pd_com_restricoes` implementado em 2026-08-23: decisão pela subsuperfície, dose por SMP médio das duas camadas — ver ADR 0003 D6 e ADR 0002 D10 — com CAL-10/CAL-11 como oráculo); `mapa_culturas.json` e `motor/adubacao.py` prontos |
| S2 | 16–30/09 | 21 grãos; formulário web; laudo em tela; **aptidão v0**; fluxo ponta a ponta — **marco M1** | concluído — `siras/motor/laudo.py` expõe `gerar_laudo()`, o ponto de entrada único declarado em `CLAUDE.md`, orquestrando calagem, adubação e os dois cenários de aptidão (CCAE §7) numa saída só; `siras/web/` serve o formulário em `/analise/dados` e o laudo em `/analise/laudo`, com a camada de apresentação isolada em `siras/relatorio/apresentacao.py`. O fluxo ponta a ponta é verificado pelo POST real da aplicação em `testes/integracao/test_web_analise.py`: ADU-01 e CAL-01 produzem no HTML os valores do campo `referencia`. O despacho por grupo em `gerar_laudo()` cobre só `graos`; o mapeamento cultura→critério deixou de ser o bloqueio (ver etapa d) e o que falta para os demais grupos é ligar as funções de adubação já prontas ao orquestrador |
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
| a | Estruturação da base de conhecimento (JSON) | em andamento — `dados/comum/` e a adubação dos 6 grupos (grãos, hortaliças, tubérculos, outras, frutíferas, erva-mate) transcritas e conferidas; falta `corretivos.json` (Cap. 8). As três lacunas que a conformidade da aptidão expôs foram fechadas em 2026-09-10 (CCAE-v1.1.md, Apêndice B, B-2 a B-4): alfafa (`grupo_p` 2, `grupo_k` 2) e gengibre (2 e 3) transcritos do Anexo 2 para `interpretacao_p/k.json`, e as seis espécies florestais restantes mapeadas em `mapa_culturas.json` para `erva_mate_e_florestais`. O Anexo 2 completo foi transcrito em 2026-09-10 (`dados/comum/catalogo_anexo2.json`, 141 culturas) e confere com as duas transcrições anteriores sem nenhuma divergência, travado por `testes/unidade/test_integridade_catalogo_anexo2.py`. Falta o refactor que faz `grupo_exigencia()` resolver por essa fonte única em vez das listas `culturas` de `interpretacao_p/k.json` — plano aprovado, execução adiada |
| b | Definição formal das regras SE-ENTÃO | em andamento |
| c | Definição dos critérios de aptidão edáfica | concluído — versão vigente `docs/CCAE-v1.2.md` (aprovada em reunião de 10/09/2026, tag `criterios-v1.2`), sucedendo a `docs/CCAE-v1.1.md` (aprovada por e-mail no mesmo dia, Apêndice D), F1-F7 rastreados ao Manual e a Ramalho Filho &amp; Beek (1995); motor em `siras/motor/aptidao.py` (docs/decisoes/0005) |
| d | Módulo de entrada de dados | em andamento — formulário completo para grãos em `siras/web/templates/dados.html`, cobrindo o modelo de domínio inteiro (inclusive Ca, Mg, PRNT, profundidade de incorporação, cultivo, antecedente e a camada 10–20 cm) em vez de presumir PRNT 100% e 1º cultivo. As opções de cultura e de sistema de manejo saem da própria base: cada opção de manejo é um critério transcrito, então nenhuma combinação escolhida na tela deixa de resolver, e os critérios que as notas marcam fora do escopo (arroz irrigado) não são oferecidos. **Mapeamento completo em 2026-09-12:** `dados/comum/mapa_culturas.json` passou de 29 para 67 entradas — as 61 culturas do escopo (21 grãos, 18 hortaliças, 2 tubérculos, 17 frutíferas, 1 erva-mate, 2 outras) mais as 6 espécies florestais, que seguem mapeadas para a aptidão e fora do escopo de recomendação (docs/decisoes/0006). A conferência do autor corrigiu de passagem duas questões de mérito nas hortaliças, pelas seções do Manual: alface entra no grupo de almeirão/chicória/rúcula/salsa (6.3.3, uma cultura), e repolho e tomate são duas (6.3.19 e 6.3.20). `testes/unidade/test_coerencia_mapa_culturas.py` passa a travar a coerência entre o mapa e as culturas transcritas na adubação, nas duas direções — a divergência de identificador entre os dois lados é silenciosa: passa em schema, passa no carregador, e só aparece quando alguém gera o laudo |
| e | Motor de inferência | em andamento |
| f | Módulos de recomendação e aptidão | em andamento — `siras/motor/aptidao.py` implementado e verificado contra o `docs/CCAE-v1.1.md`; contrato de 3 argumentos do CCAE exposto por `avaliar_aptidao_ccae()`; sinonímia de nomes de cultura resolvida em duas camadas (`siras/dominio/nomes.py` + `dados/comum/aliases_culturas.json`) |
| g | Conjunto de casos de teste e oráculo | em andamento — conjunto de 84 casos integrado (`testes/casos/entradas_aptidao.json` + `gabarito_aptidao.csv`, separados para preservar a independência do gabarito); runner em `testes/unidade/test_conformidade_aptidao.py`. `validar_anexo1.py` passa 32/32 contra as Tab. A.2/A.3 do Anexo 1 (oráculo externo). Conformidade de classe e de fator determinante: **80/80 = 100%** desde 2026-09-10. As 4 divergências registradas em CCAE-v1.1.md, Apêndice B (B-1 a B-4) foram todas fechadas — 3 por lacuna da base de conhecimento e 1 por erro de geração do gabarito, nenhuma por defeito do motor, e **nenhum critério do CCAE foi alterado**. Suíte completa: 1291 testes passando, 1 pulado |
| h | Validação e análise dos resultados | pendente |
| i | Avaliação de usabilidade | pendente |
| — | **Débitos técnicos registrados** | 1. Mover o operador de comparação de F1, ramo (b), do código para a base: hoje o valor `40.0` está em `criterios_aptidao.json` e o `>=` está em `siras/motor/aptidao.py`, enquanto a calagem lê os dois da base (`"tipo": "v_menor_igual"`) — a assimetria é a fresta por onde a divergência de B-6 passou sem que nenhum teste a enxergasse. Não altera comportamento. 2. Suprimir `calagem indicada: 0,0 t/ha` na camada de apresentação, sem tocar na lógica — é ruído de laudo, e aparece justamente no ponto `V% = 40`. 3. Fazer `grupo_exigencia()` resolver por `catalogo_anexo2.json` como fonte única. 4. Teste exigido pela §7.1 da v1.2: comparar a fórmula de `NC` duplicada entre `motor/aptidao.py` e `motor/calagem.py` nas culturas do ramo (b) em que ambas existem — a duplicação é deliberada e só é aceitável se testada. 5. Rodar o conjunto de conformidade sob a v1.1 e sob a v1.2 e registrar saídas iguais, convertendo em resultado medido a afirmação do Apêndice C de que o conjunto não foi invalidado |
| j | Redação final | pendente |
