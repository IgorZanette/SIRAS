# Documentação do SIRAS

Índice da pasta. Cada subpasta responde a uma pergunta diferente, e é por isso que elas
existem: até 10/10/2026 eram dezessete arquivos soltos aqui na raiz, e achar o que se
procurava dependia de lembrar o nome.

| Se você quer... | Vá para |
|---|---|
| entender o que o sistema faz e por quê | [`artigo_final/`](artigo_final/) |
| saber o que foi prometido no início | [`proposta/`](proposta/) |
| conhecer os critérios e a arquitetura | [`especificacao/`](especificacao/) |
| saber se o sistema acerta, e como isso foi medido | [`validacao/`](validacao/) |
| conduzir ou analisar o teste com usuários | [`usabilidade/`](usabilidade/) |
| entender por que uma decisão foi tomada assim | [`decisoes/`](decisoes/) |
| ver em que pé está o trabalho | [`processo/roadmap.md`](processo/roadmap.md) |

## Especificação

| Arquivo | Conteúdo |
|---|---|
| [`ccae.md`](especificacao/ccae.md) | **Caderno de Critérios de Aptidão Edáfica**, versão vigente (v1.3, aprovada em 24/09/2026, tag `criterios-v1.3`). É a especificação normativa do módulo de aptidão |
| [`ccae-implementacao.md`](especificacao/ccae-implementacao.md) | Do Caderno ao código: estruturas JSON, contrato do motor, convenções de intervalo |
| [`arquitetura.md`](especificacao/arquitetura.md) | Camadas e fluxo de processamento |
| [`base-de-conhecimento.md`](especificacao/base-de-conhecimento.md) | Formato dos arquivos JSON de `dados/` |
| [`mapa-do-manual.md`](especificacao/mapa-do-manual.md) | Rastreabilidade: cada tabela do Manual e o arquivo que a transcreve |
| [`nota-extracao-pdf.md`](especificacao/nota-extracao-pdf.md) | O símbolo `≤` que não existe na camada de texto do PDF do Manual, e o controle adotado |

### Versões anteriores do Caderno

As versões 1.0, 1.1 e 1.2 foram removidas desta pasta em 10/10/2026 — eram 148 KB de
especificação superada, e o Apêndice C da versão vigente já traz o histórico do que mudou
entre elas.

O conteúdo exato de cada versão congelada continua recuperável, e de forma mais
confiável do que um arquivo solto na pasta, porque está amarrado a um commit:

```bash
git show criterios-v1.1:docs/CCAE-v1.1.md > ccae-v1.1.md
git show criterios-v1.2:docs/CCAE-v1.2.md > ccae-v1.2.md
```

Isso importa para a banca: o trabalho afirma que o conjunto de conformidade foi executado
sob a v1.1 e que a v1.2 não alterou a função de mapeamento. As duas tags são a evidência
dessas afirmações, e uma tag prova a data e o conteúdo — um arquivo na pasta não prova
nenhum dos dois.

## Validação

| Arquivo | Conteúdo |
|---|---|
| [`protocolo.md`](validacao/protocolo.md) | Hipóteses, definições operacionais, risco de circularidade e análise |
| [`como-calcular-oraculo.md`](validacao/como-calcular-oraculo.md) | Procedimento manual para calcular a referência de um caso |
| [`resultados/`](validacao/resultados/) | Saída de `scripts/gera_tabela_concordancia.py`, regerável a qualquer momento |

## Usabilidade

| Arquivo | Conteúdo |
|---|---|
| [`protocolo.md`](usabilidade/protocolo.md) | Desenho do teste, participantes, ameaças à validade, análise |
| [`questionario.md`](usabilidade/questionario.md) | O instrumento, pronto para montar no Google Forms |
| [`roteiros/`](usabilidade/roteiros/) | R1 demonstração, R2 cenário guiado, R3 uso livre |

## Processo

| Arquivo | Conteúdo |
|---|---|
| [`roadmap.md`](processo/roadmap.md) | Estado de cada etapa, pendências e plano de finalização |
| [`fluxo-de-trabalho.md`](processo/fluxo-de-trabalho.md) | Convenções de git e como pedir tarefas ao Claude Code |

## Decisões de arquitetura

[`decisoes/`](decisoes/) guarda um registro por decisão não óbvia, com o contexto, as
alternativas consideradas e o motivo da escolha. Numeradas em ordem cronológica; quando
uma revoga outra, as duas ficam, e a revogada diz quem a substituiu — o percurso é parte
do argumento.
