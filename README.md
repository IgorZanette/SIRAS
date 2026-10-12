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

A proposta completa está em [`trabalho_de_conclusao/proposta/`](trabalho_de_conclusao/proposta/).

## Executando

Requisito único: **Python 3.12 ou superior**. Um comando, em qualquer sistema:

```bash
py run.py            # Windows
python3 run.py       # Linux e macOS
```

`run.py` cria o ambiente virtual, instala as dependências, sobe o servidor em
<http://127.0.0.1:5000> e abre o navegador. Não é preciso ativar venv nem rodar `pip`.
Na segunda vez ele não reinstala nada e sobe direto.

Quem tiver `make` pode usar os mesmos atalhos pelo [`Makefile`](Makefile) — `make`,
`make testes`, `make limpar`. O Makefile apenas chama o `run.py`: a lógica mora num
lugar só porque **`make` não vem instalado no Windows**, e a máquina onde a defesa
acontece pode não ter nenhum. Python tem de estar lá de qualquer jeito, já que o sistema
é escrito nele.

| Comando | O que faz |
|---|---|
| `py run.py` | sobe o servidor e abre o navegador |
| `py run.py testes` | bancada rápida |
| `py run.py completa` | bancada completa, as duas camadas |
| `py run.py validar` | confere a base de conhecimento contra os schemas |
| `py run.py limpar` | apaga `.venv`, caches e saídas geradas |

O host é fixo em `127.0.0.1`: o SIRAS roda local e offline, sem banco de dados, sem
autenticação e sem chamada de rede.

O fluxo é de três telas — escolha da cultura, análise de solo e laudo. A análise pode cobrir
vários talhões num documento só, e o laudo sai em cores para a tela ou em folha A4 preto e
branco para impressão.

## Testes

A suíte tem duas camadas: a rápida, para rodar a cada alteração, e a completa, que acrescenta
as bancadas de 61 culturas × 10 perfis de solo.

```bash
py run.py testes      # camada rápida
py run.py completa    # tudo, incluindo as bancadas
py run.py validar     # valida dados/ contra os schemas
```

Os utilitários restantes rodam de dentro de `siras/`, com a venv já criada por `run.py`:

```bash
cd siras
../.venv/Scripts/python scripts/validar_anexo1.py           # P e K contra o Anexo 1 do Manual
../.venv/Scripts/python scripts/conferir_contraste.py       # contraste da paleta nos dois temas
../.venv/Scripts/python scripts/gera_tabela_concordancia.py # tabela de concordância da validação
../.venv/Scripts/python scripts/gerar_figuras_artigo.py     # figuras do artigo, em PNG
```

A conformidade do módulo de aptidão contra o Caderno de Critérios roda junto da camada
rápida (`testes/unidade/test_conformidade_aptidao.py`), sobre o conjunto de casos de
`testes/casos/` — as entradas e o gabarito ficam em arquivos separados, para que o gabarito
permaneça independente do código.

## Organização do repositório

A raiz tem **duas metades**, divididas em 11/10/2026 antes do congelamento. A regra é
esta: se o documento ou o arquivo descreve o **sistema**, está em `siras/`; se descreve o
**trabalho sobre o sistema**, está em `trabalho_de_conclusao/`.

```
SIRAS/
├── run.py                   # um comando põe tudo no ar
├── Makefile                 # os mesmos atalhos, para quem tem make
├── siras/                   # a implementação
│   ├── siras/               #   o pacote Python
│   ├── dados/               #   a base de conhecimento, em JSON
│   ├── testes/              #   a suíte e os casos com gabarito
│   ├── scripts/             #   utilitários de validação e de geração
│   ├── docs/                #   decisões, especificação e artes de origem
│   ├── app.py  conftest.py  requirements.txt
└── trabalho_de_conclusao/   # a proposta, o artigo, os protocolos e o roadmap
```

### Dentro de `siras/`

| Caminho | Conteúdo |
|---|---|
| `siras/dominio/` | Entidades do domínio (análise de solo, cultura, laudo) |
| `siras/conhecimento/` | Carregamento e validação da base de conhecimento |
| `siras/motor/` | Motor de inferência — as regras SE-ENTÃO |
| `siras/relatorio/` | Montagem do laudo |
| `siras/web/` | Camada web (Flask) |
| `siras/validacao/` | Apuração da concordância com o oráculo — alimenta a tabela de Resultados |
| `dados/comum/` | Tabelas gerais do Manual (SMP, pH de referência, critérios de calagem, interpretação de P/K) |
| `dados/culturas/<grupo>/` | Tabelas de adubação por grupo de cultura (grãos, hortaliças, tubérculos, outras comerciais, frutíferas, erva-mate) |
| `dados/mercado/` | **Origem mista, declarada bloco a bloco:** catálogo de fórmulas NPK e corretivos de acidez. Cada bloco traz `_fonte` e `_status` (ver `siras/docs/decisoes/0007` e `0008`) |
| `testes/casos/` | Casos de teste e valores de referência (oráculo da validação) |
| `scripts/` | Utilitários: concordância, schemas, contraste, geração dos arquivos da marca e dos fundos, consolidação do questionário |
| `docs/` | Decisões de projeto, especificação e as artes originais da marca e dos fundos — índice em [`siras/docs/README.md`](siras/docs/README.md) |

### Dentro de `trabalho_de_conclusao/`

Índice em [`trabalho_de_conclusao/README.md`](trabalho_de_conclusao/README.md).

| Pasta | Para quê |
|---|---|
| [`proposta/`](trabalho_de_conclusao/proposta/) | A proposta aprovada |
| [`artigo_final/`](trabalho_de_conclusao/artigo_final/) | O artigo do TCC |
| [`validacao/`](trabalho_de_conclusao/validacao/) | Protocolo, procedimento do oráculo e resultados medidos |
| [`usabilidade/`](trabalho_de_conclusao/usabilidade/) | Protocolo do teste com usuários, roteiros e questionário |
| [`processo/`](trabalho_de_conclusao/processo/) | Roadmap e convenções de trabalho |

As duas metades são independentes: a implementação roda sem a outra pasta. Os três
pontos em que o código a alcança — figuras do artigo, instrumento de usabilidade e a
conferência do roadmap contra a tela de estado — estão listados no índice do trabalho.

## Estado do projeto

Em desenvolvimento. O estado detalhado de cada etapa está em [`trabalho_de_conclusao/processo/roadmap.md`](trabalho_de_conclusao/processo/roadmap.md).

**Pronto** (11/10/2026):

- **Motor** — calagem, adubação e aptidão edáfica para as **61 culturas e grupos de culturas** do
  escopo, com `gerar_laudo()` como ponto de entrada único e uma trilha que registra cada decisão
  com a regra e a tabela do Manual que a produziram.
- **Aptidão edáfica** — implementada conforme o Caderno de Critérios ([`siras/docs/especificacao/ccae.md`](siras/docs/especificacao/ccae.md),
  versão vigente), com os cenários atual e potencial. Conformidade de **100%** sobre os casos
  gabaritados à mão pelo autor, em classe, fator determinante e grau de cada fator.
- **Aplicação web** — as três telas, leitura ao vivo da interpretação enquanto se digita, vários
  talhões num laudo, versão impressa em A4, temas claro e escuro, e calculadora que compara
  fórmulas NPK com os preços que o usuário informar. Dez exemplos de preenchimento cobrem os seis
  grupos de cultura e chegam com **todos** os campos preenchidos, inclusive os opcionais: dá para
  gerar um laudo sem digitar nada.
- **Laudo reorganizado** ([ADR 0011](siras/docs/decisoes/0011-laudo-reorganizado-essencial-e-anexo.md)) —
  o essencial por talhão, um quadro que põe as áreas lado a lado e os complementos uma vez por
  documento. Um laudo de seis talhões saía em 27 folhas A4; o texto caiu 53%. O documento é sempre
  claro, nos dois temas da aplicação, porque é papel branco em qualquer um deles.
- **Tabelas do Manual** — sete tabelas transcritas, consultáveis na interface, incluindo o pH de
  referência (Tab. 5.1, com o aviso de que não é ela que dispara a calagem) e os grupos de
  exigência de P e K das 141 culturas do Anexo 2.
- **Interface v2** ([ADR 0012](siras/docs/decisoes/0012-cena-3d-e-acabamento-da-interface.md) e
  [ADR 0013](siras/docs/decisoes/0013-integracao-da-cena-3d-e-fundos-mensuraveis.md)) — nova identidade
  de marca, escolha de tema em três estados (claro, escuro, seguir o sistema), revelação das
  seções ao rolar, seção que declara em que pé o trabalho está, "pular para o conteúdo" e anel de
  foco único.

  **As dez cenas 3D** da apresentação estão em uso: três nos estágios da tela inicial, uma como
  cabeçalho da leitura ao vivo — onde cada atributo preenchido acende o seu ponto e é nomeado num
  inventário —, cinco na tela de espera (uma coreografia por módulo do motor) e a décima em texto,
  dizendo o que a ilustração não é. A cena usa three.js **vendorizado** (`static/vendor/`, com
  licença e hash conferidos por teste): roda offline como o resto do sistema, não participa de
  decisão agronômica nenhuma e **não existe no laudo** — há teste para isso, em tela e impresso.
  Sem JavaScript ou sem WebGL, a página aparece inteira.

  **Os fundos de paisagem** entram onde não há texto por cima: atrás do monólito e nas calhas fora
  da coluna de conteúdo. O limite não foi de gosto, foi medido — o teto de luminância que sustenta
  o texto terciário a 4,5:1 é 0,027, e a arte em mesclagem cheia chega a 0,57. Cada tema tem a sua
  família de artes, e `scripts/gerar_fundos.py` as converte para WebP: 13 MB de PNG viram 226 KB.
- **Indicação de formulação** — o laudo diz qual adubo formulado comprar e em que dose, pelo
  **método do próprio Manual** (§8.3, p. 311): a dose se ancora no nutriente mais deficiente no
  solo, o que falta do outro vira complemento com fertilizante simples e o N restante vai para
  cobertura. O catálogo de fórmulas é dado de mercado, com fonte por entrada, e o laudo declara
  as duas procedências ([ADR 0008](siras/docs/decisoes/0008-escolha-de-formula-pelo-metodo-do-manual.md)).
- **Validação** — `scripts/gera_tabela_concordancia.py` produz a tabela de concordância com IC 95%
  de Wilson, a partir de `siras/validacao/concordancia.py`, que a suíte também exercita. Medido em
  11/10/2026: recomendação **25/25 = 100%** (IC [86,7%; 100,0%]) e aptidão **88/88 = 100%**
  (IC [95,8%; 100,0%]). O limite inferior do intervalo passou os 80% que a H₁.₁ declara — a
  hipótese se sustenta pelo critério declarado, e a pendência de tamanho de amostra está fechada.

  Dos 10 casos acrescentados em 11/10, **dois reprovaram o motor** e geraram a
  [ADR 0010](siras/docs/decisoes/0010-adicional-de-n-por-rendimento-e-reposicao-em-muito-alto.md): a dose
  de nitrogênio não reagia à expectativa de rendimento, e a classe *Muito alto* em 2º cultivo
  aplicava manutenção onde o Manual prevê reposição. Os dois defeitos atravessaram a suíte inteira
  sem falhar, porque nenhum teste pedia a combinação de entradas que os revela — é o achado mais
  forte da seção de Resultados.
- **Suíte** — **5389** testes passando na camada completa, **2677** na rápida.
  O único pulado é a conferência da página da defesa, que vive fora do repositório. A contagem não
  inclui o kit 3D entregue na raiz nem `_local/`: o primeiro é material de origem com testes
  próprios (e está no `.gitignore`), o segundo não está no repositório.

**Em andamento:** validação e análise de discordâncias, comparação com ferramenta existente e
avaliação de usabilidade — sprints S5 e S6. O protocolo da usabilidade está em
[`trabalho_de_conclusao/usabilidade/protocolo.md`](trabalho_de_conclusao/usabilidade/protocolo.md): três roteiros de teste com usuários do público-alvo
e questionário pós-teste estruturado pelas dez heurísticas de Nielsen, em lugar do SUS previsto
na proposta.

**Pendente de terceiros:** recrutamento dos participantes da avaliação de usabilidade e a busca na
literatura pedida pelo orientador (P4 e P8 no roadmap).

**Pendente do autor, antes do congelamento:** conferir num navegador a paginação do laudo impresso
e a interface v2 nos dois temas. Nenhuma das duas é verificável por teste automatizado, e as três
rodadas de correção da interface registradas na ADR 0013 começaram todas por alguém olhar a tela —
o padrão está anotado lá, porque ele vale para a seção de Resultados.

**A implementação encerra em 12/10/2026**, por definição do orientador. Daí em diante, só testes com
usuários e redação do artigo ([`trabalho_de_conclusao/artigo_final/`](trabalho_de_conclusao/artigo_final/)).

## Ferramentas de desenvolvimento

A implementação do código utiliza assistência de IA (Claude Code). Os **dados agronômicos** — todas
as tabelas do Manual de Calagem e Adubação e os valores de referência dos casos de teste — foram
transcritos e conferidos manualmente pelo autor a partir da publicação original, conforme registrado
em [`siras/docs/especificacao/mapa-do-manual.md`](siras/docs/especificacao/mapa-do-manual.md).

## Aviso

O SIRAS é uma ferramenta de apoio à decisão e não substitui a responsabilidade técnica de
profissional habilitado na emissão de recomendações oficiais de correção e adubação.
