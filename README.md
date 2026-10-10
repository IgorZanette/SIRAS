# SIRAS — Sistema de Interpretação e Recomendação Agronômica de Solo

Trabalho de Conclusão de Curso — Bacharelado em Ciência da Computação
Universidade de Passo Fundo · 2026

**Autor:** Igor Zanette · **Orientador:** Prof. Rafael Rieder

---

## Sobre

Sistema especialista baseado em regras que interpreta análises químicas e físicas de solo, gera
recomendações de calagem e adubação e estima a aptidão edáfica de culturas, segundo os critérios do
**Manual de Calagem e Adubação para os estados do Rio Grande do Sul e de Santa Catarina**
(CQFS-RS/SC, 11ª edição, 2016).

Diferencial em relação às ferramentas existentes: integra, a partir de **uma análise individual de
solo**, a recomendação de manejo e a estimativa de aptidão — combinação não encontrada nos sistemas
disponíveis para o contexto do RS.

A proposta completa está em [`docs/proposta/`](docs/proposta/).

## Executando

Requisitos: Python 3.12 ou superior.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows
# source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
python app.py
```

`python app.py` sobe a aplicação em <http://127.0.0.1:5000>, com host fixo em `127.0.0.1`:
o SIRAS roda local e offline, sem banco de dados, sem autenticação e sem chamada de rede.

O fluxo é de três telas — escolha da cultura, análise de solo e laudo. A análise pode cobrir
vários talhões num documento só, e o laudo sai em cores para a tela ou em folha A4 preto e
branco para impressão.

## Testes

A suíte tem duas camadas: a rápida, para rodar a cada alteração, e a completa, que acrescenta
as bancadas de 61 culturas × 10 perfis de solo.

```bash
pytest                            # camada rápida
pytest --completa                 # tudo, incluindo as bancadas
python scripts/valida_base.py     # valida dados/ contra os schemas
python validar_anexo1.py          # classificações de P e K contra o Anexo 1 do Manual
python scripts/conferir_contraste.py   # contraste da paleta nos dois temas
```

A conformidade do módulo de aptidão contra o Caderno de Critérios roda junto da camada
rápida (`testes/unidade/test_conformidade_aptidao.py`), sobre o conjunto de casos de
`testes/casos/` — as entradas e o gabarito ficam em arquivos separados, para que o gabarito
permaneça independente do código.

## Organização do repositório

| Caminho | Conteúdo |
|---|---|
| `siras/dominio/` | Entidades do domínio (análise de solo, cultura, laudo) |
| `siras/conhecimento/` | Carregamento e validação da base de conhecimento |
| `siras/motor/` | Motor de inferência — as regras SE-ENTÃO |
| `siras/relatorio/` | Montagem do laudo |
| `siras/web/` | Camada web (Flask) |
| `dados/comum/` | Tabelas gerais do Manual (SMP, pH de referência, critérios de calagem, interpretação de P/K) |
| `dados/culturas/<grupo>/` | Tabelas de adubação compartilhadas por grupo de cultura (grãos, hortaliças, tubérculos, outras comerciais, frutíferas, erva-mate) |
| `dados/mercado/` | **Origem mista, declarada bloco a bloco:** catálogo de fórmulas NPK e arquivo de corretivos de acidez. Cada bloco traz `_fonte` e `_status` — o que é lei vigente, o que é convenção comercial herdada e o que é ficha de fabricante (ver `docs/decisoes/0007` e `0008`) |
| `siras/validacao/` | Apuração da concordância com o oráculo — alimenta a tabela de Resultados |
| `testes/casos/` | Casos de teste e valores de referência (oráculo da validação) |
| `scripts/` | Utilitários: tabela de concordância da validação, conferência de schemas e de contraste, geração dos arquivos da marca, consolidação do questionário de usabilidade |
| `validar_anexo1.py` | Confere as classificações de P e K contra o Anexo 1 do Manual (oráculo externo) |
| `docs/` | Documentação técnica, decisões de projeto e rastreabilidade das fontes |

Documentos principais:

- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) — visão de arquitetura e fluxo de processamento
- [`docs/CCAE-v1.3.md`](docs/CCAE-v1.3.md) — Caderno de Critérios de Aptidão Edáfica, versão
  vigente, aprovada pelo orientador em 24/09/2026 (tag `criterios-v1.3`)
- [`docs/CCAE-implementacao.md`](docs/CCAE-implementacao.md) — do Caderno ao código: estruturas
  JSON, contrato do motor e ordem de trabalho
- [`docs/HANDOFF-aptidao.md`](docs/HANDOFF-aptidao.md) — resumo de retomada do módulo de aptidão
- [`docs/BASE_DE_CONHECIMENTO.md`](docs/BASE_DE_CONHECIMENTO.md) — formato dos arquivos JSON
- [`docs/VALIDACAO.md`](docs/VALIDACAO.md) — protocolo de validação e hipóteses
- [`docs/USABILIDADE.md`](docs/USABILIDADE.md) — protocolo do teste de usabilidade, com os
  [roteiros](docs/roteiros/) e o [questionário das dez heurísticas de Nielsen](docs/instrumentos/questionario-heuristicas.md)
- [`docs/mapa_manual.md`](docs/mapa_manual.md) — rastreabilidade tabela do Manual → arquivo
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — cronograma e estado de cada etapa
- [`docs/decisoes/`](docs/decisoes/) — registros de decisão de arquitetura
- [`docs/FLUXO_DE_TRABALHO.md`](docs/FLUXO_DE_TRABALHO.md) — convenções de git e como pedir tarefas ao Claude Code
- [`docs/COMO_CALCULAR_ORACULO.md`](docs/COMO_CALCULAR_ORACULO.md) — procedimento manual para calcular o oráculo de validação
- [`docs/CONFERENCIA_S3.md`](docs/CONFERENCIA_S3.md) — roteiro de conferência: hortaliças, tubérculos, cana, tabaco
- [`docs/CONFERENCIA_S4.md`](docs/CONFERENCIA_S4.md) — roteiro de conferência: frutíferas e erva-mate
- [`docs/NOTA_EXTRACAO_PDF.md`](docs/NOTA_EXTRACAO_PDF.md) — o símbolo `≤` no PDF do Manual e como foi recuperado

## Estado do projeto

Em desenvolvimento. O estado detalhado de cada etapa está em [`docs/ROADMAP.md`](docs/ROADMAP.md).

**Pronto** (10/10/2026):

- **Motor** — calagem, adubação e aptidão edáfica para as **61 culturas e grupos de culturas** do
  escopo, com `gerar_laudo()` como ponto de entrada único e uma trilha que registra cada decisão
  com a regra e a tabela do Manual que a produziram.
- **Aptidão edáfica** — implementada conforme o Caderno de Critérios ([`docs/CCAE-v1.3.md`](docs/CCAE-v1.3.md),
  versão vigente), com os cenários atual e potencial. Conformidade de **100%** sobre os casos
  gabaritados à mão pelo autor, em classe, fator determinante e grau de cada fator.
- **Aplicação web** — as três telas, leitura ao vivo da interpretação enquanto se digita, vários
  talhões num laudo, versão impressa em A4, temas claro e escuro, e calculadora que compara
  fórmulas NPK com os preços que o usuário informar.
- **Indicação de formulação** — o laudo diz qual adubo formulado comprar e em que dose, pelo
  **método do próprio Manual** (§8.3, p. 311): a dose se ancora no nutriente mais deficiente no
  solo, o que falta do outro vira complemento com fertilizante simples e o N restante vai para
  cobertura. O catálogo de fórmulas é dado de mercado, com fonte por entrada, e o laudo declara
  as duas procedências ([ADR 0008](docs/decisoes/0008-escolha-de-formula-pelo-metodo-do-manual.md)).
- **Validação** — `scripts/gera_tabela_concordancia.py` produz a tabela de concordância com IC 95%
  de Wilson, a partir de `siras/validacao/concordancia.py`, que a suíte também exercita. Medido em
  10/10/2026: recomendação **15/15 = 100%** (IC [79,6%; 100,0%]) e aptidão **88/88 = 100%**
  (IC [95,8%; 100,0%]).
- **Suíte** — 4951 testes passando (camada completa, 4 min 32 s).

**Em andamento:** validação e análise de discordâncias, comparação com ferramenta existente e
avaliação de usabilidade — sprints S5 e S6. O protocolo da usabilidade está em
[`docs/USABILIDADE.md`](docs/USABILIDADE.md): três roteiros de teste com usuários do público-alvo
e questionário pós-teste estruturado pelas dez heurísticas de Nielsen, em lugar do SUS previsto
na proposta.

**Pendente de terceiros:** recrutamento dos participantes da avaliação de usabilidade e a busca na
literatura pedida pelo orientador (P4 e P8 no roadmap). Pendente do autor: **ao menos um caso de
recomendação a mais** (P9) — com 15 casos o limite inferior do IC fica em 79,6%, abaixo dos 80% que
a H1.1 declara; com 16 passa a 80,6%.

**A implementação encerra em 12/10/2026**, por definição do orientador. Daí em diante, só testes com
usuários e redação do artigo ([`docs/artigo_final/`](docs/artigo_final/)).

## Ferramentas de desenvolvimento

A implementação do código utiliza assistência de IA (Claude Code). Os **dados agronômicos** — todas
as tabelas do Manual de Calagem e Adubação e os valores de referência dos casos de teste — foram
transcritos e conferidos manualmente pelo autor a partir da publicação original, conforme registrado
em [`docs/mapa_manual.md`](docs/mapa_manual.md).

## Aviso

O SIRAS é uma ferramenta de apoio à decisão e não substitui a responsabilidade técnica de
profissional habilitado na emissão de recomendações oficiais de correção e adubação.
