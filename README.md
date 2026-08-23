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

**Estado atual:** a camada web (Flask) ainda não foi implementada — `python app.py` hoje só
confirma que o ambiente está configurado, sem subir servidor. O motor de inferência
(calagem e adubação de grãos) já funciona e é validado por linha de comando; ver
`docs/ROADMAP.md` para o que falta.

## Testes

```bash
pytest                            # todos os testes
python scripts/valida_base.py     # valida dados/comum/ contra os schemas
```

`testes/test_validacao.py` e `scripts/gera_tabela_concordancia.py` (comparação com o
oráculo, Seção 4.4 da proposta) ainda não existem — ver `docs/ROADMAP.md`, etapas g/h.

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
| `testes/casos/` | Casos de teste e valores de referência (oráculo da validação) |
| `docs/` | Documentação técnica, decisões de projeto e rastreabilidade das fontes |

Documentos principais:

- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) — visão de arquitetura e fluxo de processamento
- [`docs/BASE_DE_CONHECIMENTO.md`](docs/BASE_DE_CONHECIMENTO.md) — formato dos arquivos JSON
- [`docs/VALIDACAO.md`](docs/VALIDACAO.md) — protocolo de validação e hipóteses
- [`docs/mapa_manual.md`](docs/mapa_manual.md) — rastreabilidade tabela do Manual → arquivo
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — cronograma e estado de cada etapa
- [`docs/decisoes/`](docs/decisoes/) — registros de decisão de arquitetura
- [`docs/FLUXO_DE_TRABALHO.md`](docs/FLUXO_DE_TRABALHO.md) — convenções de git e como pedir tarefas ao Claude Code
- [`docs/COMO_CALCULAR_ORACULO.md`](docs/COMO_CALCULAR_ORACULO.md) — procedimento manual para calcular o oráculo de validação
- [`docs/CONFERENCIA_S3.md`](docs/CONFERENCIA_S3.md) — roteiro de conferência: hortaliças, tubérculos, cana, tabaco
- [`docs/CONFERENCIA_S4.md`](docs/CONFERENCIA_S4.md) — roteiro de conferência: frutíferas e erva-mate
- [`docs/NOTA_EXTRACAO_PDF.md`](docs/NOTA_EXTRACAO_PDF.md) — o símbolo `≤` no PDF do Manual e como foi recuperado

## Estado do projeto

Em desenvolvimento. Consulte [`docs/ROADMAP.md`](docs/ROADMAP.md) para o estado atual de cada etapa.

## Ferramentas de desenvolvimento

A implementação do código utiliza assistência de IA (Claude Code). Os **dados agronômicos** — todas
as tabelas do Manual de Calagem e Adubação e os valores de referência dos casos de teste — foram
transcritos e conferidos manualmente pelo autor a partir da publicação original, conforme registrado
em [`docs/mapa_manual.md`](docs/mapa_manual.md).

## Aviso

O SIRAS é uma ferramenta de apoio à decisão e não substitui a responsabilidade técnica de
profissional habilitado na emissão de recomendações oficiais de correção e adubação.
