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
| S2 | 16–30/09 | 21 grãos; formulário web; laudo em tela; **aptidão v0**; fluxo ponta a ponta — **marco M1** | concluído — `siras/motor/laudo.py` expõe `gerar_laudo()`, o ponto de entrada único declarado em `CLAUDE.md`, orquestrando calagem, adubação e os dois cenários de aptidão (CCAE §7) numa saída só; `siras/web/` serve o formulário em `/analise/dados` e o laudo em `/analise/laudo`, com a camada de apresentação isolada em `siras/relatorio/apresentacao.py`. O fluxo ponta a ponta é verificado pelo POST real da aplicação em `testes/integracao/test_web_analise.py`: ADU-01 e CAL-01 produzem no HTML os valores do campo `referencia`. Com `mapa_culturas.json` completo (2026-09-12), o despacho passou a cobrir os seis grupos do escopo — ver etapa e |
| S3 | 01–15/10 | Hortaliças (18), tubérculos (2), cana e tabaco | concluído — `motor/adubacao.py` cobre N/P2O5/K2O das 18 hortaliças, 2 tubérculos, cana (2 ciclos) e tabaco (2 tipos), com `grupo_exigencia` explícito por cultura (Anexo 2, p. 361-365) em vez de suposição; casos ADU-08/09/10/13/14 conferem |
| S4 | 16–31/10 | Frutíferas (17, três fases) e erva-mate — **marco M2** | concluído — `motor/adubacao.py` cobre as 17 frutíferas em pré-plantio e crescimento, e a manutenção nos formatos taxa/tonelada (8 culturas), bespoke (amoreira-preta, mirtileiro, morangueiro, nogueira-pecã — ADR 0004 D4.7) e correspondência solo-tecido da videira (N e P; K permanece pendente por decisão do Manual, D4.6); erva-mate (3 fases + recuperação); casos ADU-11/12/15-19 conferidos e com `referencia` (ADU-15 confirmado pelo autor em 2026-08-23, p. 199). Só ameixeira, macieira e pêssego/nectarina ficam fora de escopo na manutenção (teor foliar sem correspondência solo-tecido, D4.6) — pré-plantio e crescimento continuam cobertos. **Correção de 13/09/2026, achada pela bancada de 61 culturas × 10 cenários:** a lista acima estava incompleta. Além das três de teor foliar, duas combinações levantam `NotImplementedError` por implementação pendente, e não por decisão do Manual: a manutenção do **maracujazeiro** (indexação `classe_mo_e_produtividade_estimada`, formato próprio que aguarda caso de teste calculado à mão — mesma política de `graos_pd_com_restricoes`) e o crescimento da **videira** (`crescimento.n.tipo='por_classe_mo_ano_e_tipo_uva'`). As cinco passaram a ser recusadas com explicação na tela; antes derrubavam a aplicação com HTTP 500 |
| S5 | 01–15/11 | Aptidão v1; 60–80 casos de teste com oráculo; script de concordância | em andamento — antecipado em parte na etapa g: 84 casos de aptidão com gabarito separado e runner de conformidade passando integralmente (reverificado em 13/09/2026); 13 casos de recomendação, todos com `referencia`. Falta o que depende do autor: os 3 campos `PREENCHER` de `testes/casos/casos_aptidao.json` |
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
| d | Módulo de entrada de dados | concluído — fluxo de três etapas em `siras/web/`: `/analise` (escolha entre os seis grupos e as 61 culturas), `/analise/dados` (formulário completo, com divulgação progressiva das variáveis condicionais lidas de `variavel_adicional` na base) e `/analise/laudo`. As opções de cultura, de sistema de manejo e de variável condicional saem todas da base de conhecimento — nenhuma lista escrita em template —, então a tela não oferece uma opção que o motor recusaria. Leitura ao vivo por `POST /api/interpretar` (ADR: opção B do plano de front-end), com `testes/unidade/test_leitura.py` travando a concordância entre o que o painel mostra e o que o laudo emite. Ampliado em 12–13/09/2026: vários talhões num laudo único (a análise de solo se repete por talhão; cultura, manejo e corretivo são compartilhados), área opcional com o total a comprar quando todas as áreas são informadas, propriedade e talhão separados, identificação do responsável técnico com CPF ou CNPJ pontuado pela contagem de dígitos, cultura antecedente oferecida só quando a cultura a exige e só com as opções que ela aceita, "Editar a análise" devolvendo o formulário preenchido, campos opcionais marcados e com o motivo de preenchê-los, e aviso próprio de campo obrigatório no lugar da bolha do navegador. Laudo com a marca do SIRAS no cabeçalho e no rodapé, e versão impressa em A4 preto e branco ao lado do PDF em cores |
| e | Motor de inferência | concluído — `gerar_laudo()` despacha os seis grupos do escopo e devolve calagem, adubação e os dois cenários de aptidão com a trilha completa. Grãos mantêm caminho próprio por serem a exceção do Manual (correção e manutenção em separado, com algoritmo por cultivo); os outros cinco compartilham um despacho parametrizado pelas variáveis condicionais que cada um exige. `_faixas_da_classe()` confere que a classe usada pela adubação bate com a releitura das faixas e estoura se divergirem. Desde 13/09/2026 a rota trata os limites declarados do motor (`NotImplementedError`) como recusa explicada, em vez de devolver HTTP 500 |
| f | Módulos de recomendação e aptidão | em andamento — `siras/motor/aptidao.py` implementado e verificado contra o `docs/CCAE-v1.1.md`; contrato de 3 argumentos do CCAE exposto por `avaliar_aptidao_ccae()`; sinonímia de nomes de cultura resolvida em duas camadas (`siras/dominio/nomes.py` + `dados/comum/aliases_culturas.json`) |
| g | Conjunto de casos de teste e oráculo | em andamento — conjunto de 84 casos integrado (`testes/casos/entradas_aptidao.json` + `gabarito_aptidao.csv`, separados para preservar a independência do gabarito); runner em `testes/unidade/test_conformidade_aptidao.py`. `validar_anexo1.py` passa 32/32 contra as Tab. A.2/A.3 do Anexo 1 (oráculo externo). Conformidade de classe e de fator determinante: **80/80 = 100%** desde 2026-09-10. As 4 divergências registradas em CCAE-v1.1.md, Apêndice B (B-1 a B-4) foram todas fechadas — 3 por lacuna da base de conhecimento e 1 por erro de geração do gabarito, nenhuma por defeito do motor, e **nenhum critério do CCAE foi alterado**. Suíte em 13/09/2026: **4400 testes passando, 1 pulado**, em duas camadas — rápida (1687 testes, ~45 s, inclui a conformidade do CCAE) e completa (`--completa`, ~4 min 30 s, acrescenta a bancada de 61 culturas × 10 perfis de solo percorrendo cada estado que a tela oferece). `validar_anexo1.py`: 0 divergências em 32 classificações de P e K |
| h | Validação e análise dos resultados | pendente |
| i | Avaliação de usabilidade | pendente |
| — | **Débitos técnicos registrados** | 1. Mover o operador de comparação de F1, ramo (b), do código para a base: hoje o valor `40.0` está em `criterios_aptidao.json` e o `>=` está em `siras/motor/aptidao.py`, enquanto a calagem lê os dois da base (`"tipo": "v_menor_igual"`) — a assimetria é a fresta por onde a divergência de B-6 passou sem que nenhum teste a enxergasse. Não altera comportamento. 2. Suprimir `calagem indicada: 0,0 t/ha` na camada de apresentação, sem tocar na lógica — é ruído de laudo, e aparece justamente no ponto `V% = 40`. 3. Fazer `grupo_exigencia()` resolver por `catalogo_anexo2.json` como fonte única. 4. Teste exigido pela §7.1 da v1.2: comparar a fórmula de `NC` duplicada entre `motor/aptidao.py` e `motor/calagem.py` nas culturas do ramo (b) em que ambas existem — a duplicação é deliberada e só é aceitável se testada. 5. Rodar o conjunto de conformidade sob a v1.1 e sob a v1.2 e registrar saídas iguais, convertendo em resultado medido a afirmação do Apêndice C de que o conjunto não foi invalidado. 6. Implementar a manutenção do maracujazeiro e o crescimento da videira depois que o autor calcular à mão os casos de referência (política de `graos_pd_com_restricoes`); hoje as duas combinações são recusadas com explicação. 7. Preencher os 3 campos `PREENCHER` de `testes/casos/casos_aptidao.json` (autor). 8. A pendência A-10 segue aberta: `validar_anexo1.py` confirma que o Anexo 1 não a resolve. 9. Conferir se `--v-200` a `--v-500` aparecem como componente sobre o fundo claro em algum template: são 4 pares abaixo de 3:1 em `scripts/conferir_contraste.py` que, ao contrário dos de verde como texto, o script não marca como informativos |
| j | Redação final | pendente |

## Validação técnica da plataforma — 13/09/2026

Executada sobre o commit `3052d7a`. Verifica que o sistema funciona ponta a ponta para todo o
escopo; **não substitui** a validação agronômica da etapa h, que compara as recomendações com
o gabarito calculado pelo autor.

| Verificação | Resultado |
|---|---|
| Suíte completa (`python -m pytest --completa`) | 4400 passando, 1 pulado, 4 min 28 s |
| Bancada: 61 culturas × 10 perfis de solo | todos os laudos completos — quatro doses, dois cenários de aptidão, trilha — e sem vocabulário de máquina no documento |
| Estados que a tela oferece | 340 geram laudo; 22 são recusados nomeando o campo que a fase exige; 5 são recusados por limite declarado; nenhum derruba a aplicação |
| Oráculo externo (`validar_anexo1.py`) | 0 divergências em 32 classificações de P e K |
| Rotas | 61 telas de cultura, 5 tabelas do Manual e páginas principais respondendo; rota inexistente devolve 404 |
| Contraste (`scripts/conferir_contraste.py`) | texto e sinais passam o piso nos dois temas; 18 pares de verde ficam abaixo dele. 14 estão nas seções que o próprio script marca como informativas — verde usado como texto: `--v-700` e `--v-800` sobre o tema escuro, `--v-200` a `--v-600` sobre o claro. Os outros 4 — `--v-200` a `--v-500` como componente sobre o fundo claro — não têm essa ressalva, e ficam a conferir contra os templates antes do teste de usabilidade (débito 9) |

Defeitos encontrados nesta rodada e corrigidos: `(None)` impresso na observação da dose de N das
culturas que não dosam N por faixa de matéria orgânica; HTTP 500 ao escolher fases sem
recomendação implementada; fase "Crescimento" oferecida ao mirtileiro e ao morangueiro, que a
base declara unificada com a manutenção.

## Como rodar os testes

```
python -m pytest              # camada rápida (~45 s): motor, conformidade do CCAE, telas, laudo
python -m pytest --completa   # tudo, inclusive as bancadas lentas (~4 min 30 s)
```

Rode a completa antes de todo push e sempre que mexer na base de conhecimento, no formulário ou
no despacho de grupos. A conformidade do CCAE fica na camada rápida de propósito: é o oráculo do
trabalho, e uma alteração que a quebre precisa aparecer na hora.
