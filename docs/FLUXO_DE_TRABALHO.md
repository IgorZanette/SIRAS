# Fluxo de trabalho

## Git

Branch única `main` (projeto individual; branches de feature são desnecessárias e atrapalham a
leitura do histórico pelo orientador).

**Commits pequenos e frequentes. Push todo dia.** O histórico do repositório é evidência de processo
na avaliação — um repositório com três commits gigantes conta uma história pior do que um com
oitenta commits pequenos ao longo do semestre.

Formato: `tipo: descrição no imperativo`

| Tipo | Uso |
|---|---|
| `feat` | nova funcionalidade |
| `fix` | correção de defeito |
| `dados` | transcrição ou correção da base de conhecimento |
| `test` | casos de teste e testes automatizados |
| `docs` | documentação e monografia |
| `refactor` | reorganização sem mudança de comportamento |
| `chore` | configuração, dependências |

Exemplos: `dados: transcrever tabela SMP (Tab. 5.2)`,
`feat: implementar calculo de calagem por indice SMP`, `test: adicionar 8 casos de calagem em PD`.

## O que fica fora do repositório

`.gitignore` exclui `_local/`, `.venv/`, `__pycache__/` e `.claude/settings.local.json`.

`_local/` é a pasta de trabalho pessoal: rascunhos, anotações, planejamento, laudos reais antes da
anonimização. Nada ali é versionado nem visível no GitHub.

**Laudos reais de análise de solo nunca entram no repositório sem anonimização** — nome de produtor,
propriedade e coordenadas removidos antes de virarem caso de teste.

## Claude Code

### Regra que não pode ser quebrada

Nunca peça ao Claude Code para preencher valores das tabelas do Manual. Ele gera números plausíveis
e errados. Aplicado a doses de fertilizante isso significa validação sem sentido, risco agronômico
real e, num TCC, fabricação de dados. Ver `CLAUDE.md`.

### Como pedir

1. Peça o plano antes do código: "descreva o que vai fazer e quais arquivos vai alterar".
2. Uma tarefa por sessão. "Implemente `motor/calagem.py`" funciona; "implemente o sistema" não.
3. Quando possível, escreva primeiro o caso de teste com o valor que **você** calculou à mão, e peça
   que ele faça passar.
4. Peça explicação de qualquer trecho que não estiver claro. Na banca, "o Claude escreveu" não é
   resposta.

### Atribuição nos commits

`.claude/settings.json` define `attribution` com `commit` e `pr` vazios e `sessionUrl: false`, o que
remove as linhas automáticas das mensagens de commit. O uso de IA está declarado no `README.md` —
mensagem de commit limpa, uso declarado no lugar certo.
