# 0005 — Motor de aptidão edáfica: reuso de arquitetura e tratamento de erro

- **Status:** aceito
- **Data:** 2026-09-07
- **Contexto:** implementação do módulo de aptidão edáfica (docs/CCAE-v1.0.md, depois
  substituído pela v1.1 — aprovada por escrito pelo orientador em 10/09/2026, ver Apêndice D
  do `docs/CCAE-v1.1.md`), etapa "c"/"f" do ROADMAP, pendência P1
- **Substitui/complementa:** 0002 (políticas do motor), 0003 (modelagem de entrada), 0004
  (normalização de doses) — nenhuma revogada; este ADR é específico de `motor/aptidao.py`

## Contexto

O CCAE-v1.0.md e seu companheiro técnico (`docs/CCAE-implementacao.md`) foram escritos
como especificação abstrata, antes de qualquer código de aptidão existir, e descrevem um
layout de arquivos genérico (`siras/dados/`, `motor/faixas.py`, `catalogo_culturas.json`
etc.). Quando chegou a hora de implementar, `siras/` já tinha uma arquitetura madura para
calagem e adubação — `AnaliseSolo`/`Contexto` (docs/decisoes/0003), `Trace`, um
`Carregador` central com JSON Schema e invariantes, e a maior parte das tabelas
numéricas de F2 a F6 do CCAE já transcritas e conferidas em `dados/comum/` para outros
fins. Implementar o CCAE literalmente como descrito teria duplicado essa base inteira.

Este ADR registra as decisões tomadas para encaixar o CCAE na arquitetura real, e os
pontos em que o comportamento diverge do estilo já estabelecido por `motor/calagem.py` e
`motor/adubacao.py`.

## Decisão

### D5.1 — Reuso de dados existentes; `criterios_aptidao.json` só guarda a camada nova

`dados/comum/interpretacao_p.json`, `interpretacao_k.json` e `interpretacao_geral.json`
já eram a transcrição conferida das Tabelas 6.2–6.6, 6.7–6.10 e 6.1/6.11 do Manual.
`criterios_aptidao.json` (novo) não duplica nenhuma dessas faixas: guarda apenas a camada
que o Manual não fornece — os graus de Ramalho Filho e Beek, o mapeamento
disponibilidade→grau (CCAE §4.1), os limiares de m% de Sobral et al. (CCAE F1) e os
mapeamentos classe→grau de F4/F5/F6/F7 (CCAE F4–F7, decisões A-2 a A-5). Isso também
resolveu a pendência A-10 sem tocar em nenhum valor: a Tabela 6.5 já estava correta em
`interpretacao_p.json`, só usando uma convenção de limite (`de`/`ate`, `de` exclusivo)
equivalente à do CCAE, mas nunca antes comparada lado a lado — ver o texto atualizado em
`docs/CCAE-v1.0.md`, Apêndice A.

### D5.2 — `classificar_faixa` e `grupo_exigencia` tornam-se públicas em `motor/adubacao.py`

Ambas resolvem exatamente o que F2/F3 precisam (classificação por faixa contígua;
resolução de grupo de exigência de P/K por cultura) e já existiam, privadas, em
`motor/adubacao.py`. Renomeadas sem underscore e importadas por `motor/aptidao.py` em vez
de duplicadas. Consequência direta: a "armadilha conhecida" que o CCAE (Seção 3) alerta —
`grupo_p`/`grupo_k` divergentes por cultura, nunca um derivado do outro — é estruturalmente
impossível de errar aqui, porque aptidão e adubação leem o mesmo grupo pela mesma função.

### D5.3 — `INDETERMINADA` é um valor de retorno, não uma exceção

`motor/calagem.py` e `motor/adubacao.py` levantam `ErroCalagem`/`ErroAdubacao` para
cultura desconhecida ou critério não resolvido. O CCAE (Seção 3, tabela de classes; P5)
especifica `INDETERMINADA` como uma classe de saída de primeira classe — "não é classe de
aptidão, é estado de erro, mas ainda assim uma saída estruturada do motor, não uma
exceção que a camada de chamada precisa converter". `avaliar_aptidao()` segue o CCAE
literalmente: internamente, uma exceção privada (`_CulturaOuDadoIndeterminado`) é
levantada nos pontos de resolução de catálogo (pH de referência, grupo de exigência de
P/K) e capturada dentro da própria função, nunca escapando para quem chama. Divergência
deliberada do estilo dos outros dois motores — se o CCAE evoluir para não exigir mais
isso, reavaliar aqui primeiro.

Exceção à exceção: cultura explicitamente **fora de escopo** (arroz irrigado por
alagamento, único caso concreto hoje — grupo_4 de `interpretacao_p.json`) não vira
`INDETERMINADA`, e sim `ErroAptidao`, propagada. O CCAE (Seção 1.3) trata escopo excluído
como decisão de projeto, não como dado ausente/desconhecido — a distinção importa porque
silenciar em `INDETERMINADA` esconderia uma chamada indevida do sistema fora do que ele
se propõe a cobrir, em vez de um dado real de cultura não catalogada.

### D5.4 — Cenário `POTENCIAL` reaproveita `motor/calagem.py` para a exequibilidade de F1

CCAE §7.2 exige checar se a dose de calcário recomendada excede o teto operacional
(`NC_MAX_INCORPORADO_T_HA`/`NC_MAX_SUPERFICIAL_T_HA`, config_aptidao.json) antes de zerar
F1 no cenário `POTENCIAL`. Em vez de recalcular NC, `_resolver_f1_potencial()` chama
`motor.calagem.calcular_calagem_por_cultura()` e olha `modo_aplicacao` do critério
resolvido para escolher o teto certo. F2, F3, F4 e F6 (`CORRIGIVEL` no CCAE §7.1) viram
`NULO` incondicionalmente — a correção deles não depende de exequibilidade, só a de F1
depende, porque só a calagem tem teto operacional declarado no CCAE.

**Interpretação não literal no texto do CCAE:** o Caderno não cobre explicitamente o caso
em que F1 já é `NULO` ou `LIGEIRO` no cenário `ATUAL` — ou seja, o próprio Manual não
chega a recomendar calcário (critério de disparo não satisfeito, tipicamente pH ≥ 5,5).
Nesse caso, `_resolver_f1_potencial()` mantém F1 inalterado: não há recomendação real do
SIRAS ali para projetar como corrigida. O texto de `docs/CCAE-v1.0.md` §7.2 foi
atualizado com uma frase explícita cobrindo esse caso, para não deixar a lacuna na
especificação congelada.

### D5.5 — Alerta ambiental de "Muito alto" (F2/F3) usa o dado estruturado, não o texto de evidência

Primeira versão detectava a classe "muito_alto" (CCAE §4.1, decisão A-6) buscando a
substring no texto de `evidencia` — frágil e desnecessário, já que
`_avaliar_f2_fosforo`/`_avaliar_f3_potassio` já calculam a classe de teor internamente.
Ambas passaram a retornar `(AvaliacaoFator, classe_teor)`, e `avaliar_aptidao()` decide o
alerta a partir do valor estruturado.

### D5.6 — Grupo de exigência de P/K para culturas sem pH de referência: defeito de catálogo, não decisão de julgamento

Testar F1 ramo (b) (erva-mate) revelou que `interpretacao_p.json`/`interpretacao_k.json`
resolviam `INDETERMINADA` para toda cultura sem pH de referência: `grupos_exigencia`
declara `grupo_2`/`grupo_3` só como `culturas_texto` (prosa: "demais culturas:
florestais, medicinais..."), sem lista explícita, e `grupo_exigencia()` só resolve por
lista explícita ou pelo fallback de grãos.

A tentação óbvia — "ramo (b) de F1 é tolerante a Al, então cai todo em grupo_3 de P e K"
— **está errada** e foi descartada antes de virar código: a mandioca é `ph_referencia:
null` (ramo b) mas Grupo 2 em K (Tabela 6.7/6.9), não Grupo 3. Grupo de exigência
nutricional (P, K) e tolerância à acidez (F1) são eixos independentes do Manual; não há
implicação de um para o outro. Ramo (b) e "grupo_3" só coincidem por acaso nas espécies
florestais, não por regra.

A fonte correta não é o texto-resumo das Tabelas 6.2/6.7, e sim o **Anexo 2** (p.
361–366), que enumera `grupo_p`/`grupo_k` por cultura, individualmente. Adicionadas a
`interpretacao_p.json`/`interpretacao_k.json` (campo `culturas`, com `culturas_fonte`
apontando o Anexo 2) as 9 entradas que causavam o `INDETERMINADA` reportado: as 8
espécies do ramo (b) presentes na Tabela 5.1 (grupo_p=grupo_k=3) mais a mandioca
(grupo_p=3, grupo_k=2 — o caso que desmonta a heurística acima). **Isto é correção de
defeito de transcrição (vai para o Apêndice B do CCAE), não decisão de julgamento do
autor (não é Apêndice A)** — a fonte sempre existiu no Anexo 2, só não tinha sido
usada para popular o catálogo dessas 9 culturas.

`arroz-irrigado` e `mandioca` continuam fora do escopo da aptidão mesmo depois de
catalogados (CCAE §1.3) — `criterios_aptidao.json` ganhou a chave `fora_de_escopo`
(lista de cultura_id + fonte), checada logo no início de `avaliar_aptidao()`, levantando
`ErroAptidao`. Ter o grupo de exigência catalogado não os traz de volta ao escopo; a
exclusão é decisão de projeto (CCAE §1.3), independente de a Tabela existir ou não.

**Transcrição do Anexo 2 permanece parcial.** Ele tem ~150 linhas; só as 9 entradas
acima foram adicionadas a `interpretacao_p.json`/`interpretacao_k.json` até agora.
Qualquer cultura fora dessas 9, do Grupo 1 explícito, do Grupo 4 (arroz) ou do fallback
de grãos ainda resolve para `INDETERMINADA` em F2/F3 — comportamento correto (falha
fechada, CCAE P5), não um bug, mas uma lacuna de cobertura conhecida.

### D5.7 — Resolução de grupo_p/grupo_k em duas camadas

`dados/culturas/{hortalicas,tuberculos,outras,frutiferas,erva_mate}/*.json` já trazem
`grupo_exigencia.p`/`.k` transcritos do Anexo 2 por cultura (S3/S4 do ROADMAP) — uma
fonte mais completa e já conferida do que `interpretacao_p.json`/`interpretacao_k.json`
para essas ~50 culturas. `_resolver_grupo_p_ou_k()` consulta essa fonte primeiro
(`_buscar_grupo_exigencia_transcrito()`, varrendo `culturas_incluidas` de cada entrada —
a chave do dict é um agrupamento composto, ex. `abobora_abobrinha_moranga`, nunca o
`cultura_id` individual) e só cai para `grupo_exigencia()` de `motor/adubacao.py`
(catálogo de `interpretacao_p.json`/`interpretacao_k.json` + fallback de grãos) quando a
cultura não aparece em nenhum dos cinco arquivos.

`testes/unidade/test_aptidao.py::test_resolucao_bate_com_grupo_exigencia_ja_transcrito`
percorre as ~50 entradas com `grupo_exigencia` declarado e confere que a resolução do
motor bate com o valor já conferido pelo autor em cada arquivo — não fixa nenhum valor
numérico no teste, só compara o código contra o dado.

**Achado maior, não corrigido nesta sessão — nomenclatura de `cultura_id` não é
consistente no projeto.** Medindo a cobertura real (script ad-hoc contra as 115 culturas
de `ph_referencia.json`, não commitado): 62/115 resolvem grupo_p/grupo_k hoje, 53 não.
Das 53, a maioria não é falta de dado — é o **mesmo cultivo grafado de formas diferentes
em arquivos diferentes**:

- `mapa_culturas.json` usa ASCII sem acento e `_` (`feijao`, `milho_pipoca`,
  `nabo_forrageiro`, `painco`, `tremoco`);
- `ph_referencia.json` usa acento e `-` (`feijão`, `milho-pipoca`, `nabo-forrageiro`,
  `painço`, `tremoço`);
- os arquivos de adubação por grupo usam `culturas_incluidas` sem acento, geralmente sem
  hífen (`abobora`, não `abóbora`).

Isso significa que grãos como `milho-pipoca` (grafia de `ph_referencia.json`) hoje **não**
resolvem grupo_p/grupo_k mesmo já estando em `mapa_culturas.json` como `milho_pipoca` —
o fallback de `grupo_exigencia()` faz comparação de string exata. O restante das 53
falhas parece ser cultura genuinamente sem adubação transcrita ainda (grupo
medicinais/aromáticas/condimentares, ex. `cardamomo`, `citronela-de-java`, `guaco`) —
`INDETERMINADA` aí está correto, é limite de escopo, não bug.

Não tentei corrigir isso agora: normalizar `cultura_id` exigiria decidir uma grafia
canônica única e tocar `mapa_culturas.json`, `ph_referencia.json`, `interpretacao_p.json`,
`interpretacao_k.json` e os cinco arquivos de adubação por grupo — todos já conferidos e
com checksum contra o Manual (`carregador.py`). É uma decisão de arquitetura de dados que
atravessa calagem, adubação e aptidão ao mesmo tempo, não algo para decidir sozinho no
meio de uma tarefa já em andamento. Registrado aqui para o autor decidir a convenção
única e o formato de migração (renomear em massa vs. tabela de aliases).

## Consequências

- `motor/aptidao.py` não tem `motor/faixas.py` nem `catalogo_culturas.json` próprios —
  ambos descartados em favor do que já existe (D5.1, D5.2). `docs/CCAE-implementacao.md`
  recebeu notas de adaptação apontando cada divergência do layout originalmente descrito.
- O estilo de erro do motor de aptidão não é uniforme com o dos outros dois motores por
  decisão deliberada (D5.3), não por descuido — quem ler os três módulos em sequência
  deve notar a assimetria e encontrar a justificativa aqui, não presumir inconsistência.
- `testes/casos/casos_aptidao.json` segue vazio (só o caso-modelo, `conferido_por_autor_em:
  null`) — preenchê-lo com o gabarito de conformidade (CCAE §9) continua sendo trabalho
  exclusivo do autor, à mão, sem consultar `motor/aptidao.py`.
- Cobertura real de grupo_p/grupo_k medida em 62/115 culturas de `ph_referencia.json`
  (D5.7) — o resto não é falta de trabalho de hoje, é a inconsistência de grafia de
  `cultura_id` entre arquivos (pendente de decisão do autor) mais culturas genuinamente
  sem adubação transcrita. Até essa decisão, `INDETERMINADA` nesses casos é o
  comportamento correto (falha fechada, CCAE P5), não um defeito do motor de aptidão.
