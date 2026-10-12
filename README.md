# SIRAS — Sistema de Interpretação e Recomendação Agronômica de Solo

Trabalho de Conclusão de Curso — Bacharelado em Ciência da Computação
Universidade de Passo Fundo · 2026

**Autor:** Igor Zanette · **Orientador:** Prof. Rafael Rieder

---

## Sobre

Sistema especialista baseado em regras que interpreta análises químicas e físicas de solo,
recomenda calagem e adubação e estima a aptidão edáfica de culturas, segundo o **Manual de
Calagem e Adubação para os estados do Rio Grande do Sul e de Santa Catarina** (CQFS-RS/SC,
11ª edição, 2016). Cobre 61 culturas e grupos de culturas.

Cada número do laudo vem acompanhado da regra e da tabela do Manual que o produziram.

Diferencial em relação às ferramentas existentes: integra, a partir de **uma análise individual
de solo**, a recomendação de manejo e a estimativa de aptidão — combinação não encontrada nos
sistemas disponíveis para o contexto do RS.

## Executando

Requisito único: **Python 3.12 ou superior**.

```bash
py run.py            # Windows
python3 run.py       # Linux e macOS
```

`run.py` cria o ambiente virtual, instala as dependências, sobe o servidor em
<http://127.0.0.1:5000> e abre o navegador. Não é preciso ativar venv nem rodar `pip`.

| Comando | O que faz |
|---|---|
| `py run.py` | sobe o servidor e abre o navegador |
| `py run.py testes` | bancada rápida |
| `py run.py completa` | bancada completa, as duas camadas |
| `py run.py validar` | confere a base de conhecimento contra os schemas |
| `py run.py limpar` | apaga `.venv`, caches e saídas geradas |

Quem tiver `make` pode usar os mesmos atalhos pelo [`Makefile`](Makefile), que só chama o
`run.py`. A lógica mora num lugar só porque `make` não vem instalado no Windows, e Python
tem de estar na máquina de qualquer jeito.

Para encerrar, `Ctrl+C`. No **Git Bash** o terminal às vezes não entrega esse sinal a
programas nativos do Windows; se acontecer, rode `winpty py run.py`, ou use o PowerShell.

O host é fixo em `127.0.0.1`: o SIRAS roda local e offline, sem banco de dados, sem
autenticação e sem chamada de rede. O fluxo é de três telas — cultura, análise de solo e
laudo —, a análise pode cobrir vários talhões num documento só, e o laudo sai em cores para a
tela ou em A4 preto e branco para impressão.

## Organização

A raiz tem duas metades. Se o arquivo descreve o **sistema**, está em `siras/`; se descreve o
**trabalho sobre o sistema**, está em `trabalho_de_conclusao/`.

```
SIRAS/
├── run.py  Makefile
├── siras/                   # a implementação
│   ├── siras/               #   o pacote Python
│   ├── dados/               #   a base de conhecimento, em JSON
│   ├── testes/              #   a suíte e os casos com gabarito
│   ├── scripts/             #   utilitários de validação e de geração
│   └── docs/                #   decisões, especificação e artes de origem
└── trabalho_de_conclusao/   # proposta, artigo, protocolos e roadmap
```

| Dentro de `siras/` | |
|---|---|
| `siras/dominio/` | Entidades do domínio (análise, cultura, laudo) |
| `siras/conhecimento/` | Carregamento e validação da base |
| `siras/motor/` | Motor de inferência — as regras SE-ENTÃO |
| `siras/relatorio/` | Montagem do laudo |
| `siras/web/` | Camada web (Flask) |
| `siras/validacao/` | Apuração da concordância com o oráculo |
| `dados/` | Tabelas do Manual, por grupo de cultura, mais o catálogo de mercado |
| `testes/casos/` | Casos de teste e valores de referência (o oráculo) |
| `docs/` | Índice em [`siras/docs/README.md`](siras/docs/README.md) |

| Dentro de `trabalho_de_conclusao/` | |
|---|---|
| [`proposta/`](trabalho_de_conclusao/proposta/) | A proposta aprovada |
| [`artigo_final/`](trabalho_de_conclusao/artigo_final/) | O artigo |
| [`validacao/`](trabalho_de_conclusao/validacao/) | Protocolo e procedimento do oráculo |
| [`usabilidade/`](trabalho_de_conclusao/usabilidade/) | Protocolo e questionário do teste com usuários |
| [`processo/`](trabalho_de_conclusao/processo/) | Roadmap e convenções de trabalho |

## Estado

**Implementação concluída.** Motor, aplicação web, laudo e tabelas do Manual estão prontos; o
estado de cada etapa está no
[roadmap](trabalho_de_conclusao/processo/roadmap.md), e cada decisão não óbvia tem um registro
em [`siras/docs/decisoes/`](siras/docs/decisoes/).

Medido em 11/10/2026:

| | Resultado |
|---|---|
| Concordância da recomendação | 25/25 = 100% · IC 95% de Wilson [86,7%; 100,0%] |
| Conformidade da aptidão | 88/88 = 100% em classe e em fator |
| Suíte | 5389 testes na camada completa, 2677 na rápida |

O limite inferior do intervalo passou os 80% que a hipótese H₁.₁ declara.

**Em andamento:** avaliação de usabilidade e comparação com ferramenta existente (sprints S5 e
S6). **Pendente de terceiros:** recrutamento dos participantes (P8 no roadmap).

**A implementação encerra em 12/10/2026**, por definição do orientador. Daí em diante, só
testes com usuários e redação do artigo.

## Ferramentas de desenvolvimento

A implementação do código utiliza assistência de IA (Claude Code). Os **dados agronômicos** —
todas as tabelas do Manual e os valores de referência dos casos de teste — foram transcritos e
conferidos manualmente pelo autor a partir da publicação original, conforme registrado em
[`siras/docs/especificacao/mapa-do-manual.md`](siras/docs/especificacao/mapa-do-manual.md).

## Aviso

O SIRAS é uma ferramenta de apoio à decisão e não substitui a responsabilidade técnica de
profissional habilitado na emissão de recomendações oficiais de correção e adubação.
