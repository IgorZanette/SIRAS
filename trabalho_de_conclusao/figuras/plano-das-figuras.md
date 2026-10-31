# Figuras do SIRAS — especificação para o Figma

Cada figura do artigo nasce no Figma, é exportada em **PDF vetorial** para esta pasta e entra
no LaTeX pelo nome de arquivo abaixo (`\figura{F4-pipeline}{...}` em
`artigo_final/secoes/`). Enquanto o PDF não existe, o artigo compila com um quadro
"em produção" no lugar.

**A ideia que guia o conjunto:** cada figura responde a uma pergunta que o leitor faria, e
juntas mostram que uma interface de três telas tem um sistema de várias camadas por trás.

---

## Estado (31/10/2026)

Arquivo do Figma: **SIRAS — Figuras do artigo**, página "Figuras". Escala 2:1 (2 px = 1 pt):
quadros de página inteira com 1004 px, de coluna com 482 px; texto mínimo 14 px = 7 pt.

**As 14 figuras estão desenhadas e conferidas** (arquivo migrado para a conta educacional em
31/10/2026). Corpo: F1, F3, F4, F5, F9, F11, F13. Apêndice: F2, F6, F7, F8, F10, F12, F14.

Conferências feitas contra o código ao desenhar: a ordem dos ajustes da calagem
(`motor/calagem.py`), as dependências entre pacotes (imports), as seções e o cabeçalho do laudo
(`templates/laudo.html` e `_parciais/`), os limites de P e K (`interpretacao_p.json`,
`interpretacao_k.json`), a trilha e a formulação do caso Gleba 4 (saída do motor).
A F8 mostra doses de N, P₂O₅ e K₂O **sem referência calculada à mão**, e diz isso na própria figura.

**Exportar:** no Figma, selecionar o frame → painel direito → *Export* → **PDF** → salvar nesta
pasta com o nome do frame (`F4-pipeline.pdf`). O LaTeX ajusta a escala sozinho.

---

## Padrão visual

| Item | Valor | Por quê |
|---|---|---|
| Quadro de uma coluna | **85 mm** de largura | Coluna do modelo CC-EC_TF-TC (duas colunas, carta) |
| Quadro de página inteira | **177 mm** de largura | `figure*` |
| Fonte | **Manrope** (texto), **Sora** (títulos internos) | As fontes da interface: figura e sistema falam a mesma língua |
| Corpo mínimo no tamanho impresso | **7 pt** | O texto do artigo é 9 pt; abaixo de 7 pt a figura não se lê impressa |
| Verde do modelo | `#006400` | Cor das seções e do cabeçalho do artigo |
| Verde da marca SIRAS | `#4E9A2A` (legível sobre branco), `#8CE23F` (destaque) | `siras-theme.css` |
| Neutros | `#0A0F0C` texto, `#5A7266` secundário, `#E9F0EB` fundo de bloco | idem |
| Sinais | coral `#FF451C` deficiência severa · laranja `#D96D00` deficiência · âmbar `#B28100` atenção · aqua `#179B8A` informação | Tema claro de `siras-theme.css` |
| Fundo | Branco | O artigo é impresso |

**Regras para todas:**

1. **Legível em preto e branco.** A cor reforça; nunca é o único jeito de distinguir duas coisas.
   Use também forma, contorno tracejado, ícone ou rótulo.
2. **Nenhum número inventado.** Todo número numa figura vem da tabela "Números conferidos"
   abaixo ou de um caso com gabarito. Se precisar de outro, medir no repositório e anotar aqui.
3. **Termos do artigo**, não do código: "trilha de inferência", e não `Trace`; "aptidão
   edáfica", nunca "aptidão agrícola".
4. Cada figura tem **uma** mensagem, escrita no topo da ficha. O que não serve a ela sai.

---

## Números conferidos (medidos em 31/10/2026)

| Número | Valor | Fonte |
|---|---|---|
| Culturas e grupos com recomendação | 61 | `dados/comum/mapa_culturas.json` |
| Por grupo | grãos 21 · hortaliças 18 · tubérculos 2 · frutíferas 17 · erva-mate 1 · cana e tabaco 2 | idem |
| Espécies florestais só para aptidão (fora da recomendação) | 6 | idem, ADR 0006 |
| Arquivos JSON na base de conhecimento | 20 | `siras/dados/` |
| Esquemas JSON Schema | 20 | `siras/siras/conhecimento/esquemas/` |
| Linhas de Python no pacote `siras/` | 9.681 | contagem de linhas |
| Testes automatizados | 5.404 | `pytest --collect-only` |
| Decisões de arquitetura registradas | 13 | `siras/docs/decisoes/` |
| Fatores de limitação da aptidão | 7 | CCAE v1.3, §6 |
| Casos de validação das recomendações | 25 | `testes/casos/casos_recomendacao.json` |
| Casos de conformidade da aptidão | 92 (88 com classe, 4 indeterminados) | `testes/casos/gabarito_aptidao.csv` |
| Formulações no catálogo | 38 fórmulas e 10 fertilizantes simples | `dados/mercado/formulas_npk.json` |
| Laudo antes da reorganização | 5 folhas para 1 talhão, 27 para 6; 71% de complemento | ADR 0011 |

**Caso-exemplo de todas as figuras:** Gleba 4 do Anexo 1 do Manual (Tab. A.1, p. 353), com
milho, plantio direto consolidado, sem restrições na camada 10–20 cm, PRNT 75 %.
pH 5,3 · SMP 5,4 · argila 27 % · MO 2,1 % · P 13,1 · K 44 · Ca 2,5 · Mg 1,3 · Al 1,1 ·
CTC 12,7 · V 31 % · m 22 %.
Resultado conferido: **calcário 2,3 t/ha** (6,8 → ×¼ = 1,7 → ×100/75 = 2,3) · **P Médio** ·
**K Baixo** · **aptidão Restrita, determinante F3 potássio**.
Graus: F1 moderado · F2 moderado · F3 forte · F4 ligeiro · F5 ligeiro · F6 moderado · F7 ligeiro.
Doses de N, P₂O₅ e K₂O deste caso **não têm referência calculada** — não aparecem em figura.

---

## No corpo do artigo (7)

### F1 — `F1-iceberg` · 177 mm · Seção 3.6 (abertura)

**Mensagem:** a interface é simples de propósito; o sistema não é.

- **Acima da linha d'água:** as três telas reais, em miniatura — escolher a cultura →
  informar a análise → ler o laudo. Rótulo: "o que o usuário vê".
- **Abaixo, em camadas que se aprofundam:**
  1. Interface: leitura ao vivo das classes, vários talhões, tela de espera com as etapas do motor
  2. Motor de inferência: calagem por critério de grupo, adubação em dois caminhos, formulação em três, aptidão em dois cenários
  3. Trilha de inferência: cada número com regra, entradas, saída e fonte
  4. Base de conhecimento: 20 arquivos JSON, 20 esquemas, 61 culturas
  5. Garantia: 5.404 testes, 25 casos com oráculo, 92 casos de conformidade, 13 decisões registradas, CCAE versionado
- Ícones da própria interface (`siras-icons.svg`) para cada camada.

### F3 — `F3-escopo` · 177 mm · Seção 3.2

**Mensagem:** 61 culturas em seis grupos, e cada grupo pede um tratamento diferente.

- Seis blocos, com tamanho proporcional à contagem, cada um com nome, número e a
  particularidade que o motor trata:
  - **Grãos (21):** correção + manutenção, cultivo, expectativa de rendimento; leguminosas sem N
  - **Hortaliças (18):** dose por classe de teor
  - **Tubérculos (2):** batata e batata-doce
  - **Frutíferas (17):** pré-plantio, crescimento e manutenção
  - **Erva-mate (1):** sem pH de referência; calagem por V % < 40 %; programas de plantio e recuperação
  - **Cana e tabaco (2):** cana-planta e cana-soca; tabaco Virgínia e Burley
- Faixa cinza, tracejada, "fora do escopo": arroz irrigado, mandioca, florestais (só aptidão),
  forrageiras, medicinais, ornamentais.

### F4 — `F4-pipeline` · 177 mm · Seção 3.6.2 — **a figura central**

**Mensagem:** o que acontece entre "Gerar laudo" e o laudo.

- Faixa horizontal, da esquerda para a direita:
  1. **Entrada** — análise + cultura + contexto (manejo, condição da área, PRNT, cultivo, antecedente)
  2. **Validação de domínio** — faixas, obrigatórios, SMP dentro da tabela
  3. **Interpretação** — P pela classe de argila · K pela CTC pH 7 → classes MB a MA
  4. **Calagem** — critério → disparo → dose (detalhe em F5)
  5. **Adubação** — N, P₂O₅, K₂O (grãos | demais grupos)
  6. **Formulação** — ideal · catálogo · mistura de simples
  7. **Aptidão** — cenário atual e potencial (detalhe em F9)
  8. **Laudo** — parte essencial + anexo (detalhe em F11)
- **Por baixo de tudo, uma faixa contínua: "trilha de inferência".** De cada etapa desce um
  passo. Um deles, ampliado, mostra um passo real: regra, entradas, saída e fonte (tabela e página).
- Acima da faixa, a base de conhecimento, com setas finas para as etapas que a consultam.
- Uma nota: "função única, pura e determinística — mesma entrada, mesmo laudo".

### F5 — `F5-calagem` · 85 mm, vertical · Seção 3.6.3

**Mensagem:** a dose de calcário é uma árvore de decisão, não uma consulta.

- Cultura + manejo + condição → **critério** (Tab. 5.3–5.7) → **dispara?** (pH < limite)
  - não → "sem calcário" (e por quê)
  - sim → SMP ≤ 6,3? → **Tab. 5.2** | SMP > 6,3 → **equações com MO e Al** | erva-mate → **V % até 40**
- → **fator** (1, ½ ou ¼) → **PRNT** (×100/PRNT) → **profundidade** → **limite de 5 t/ha em superfície**
- Caminho do caso-exemplo destacado em verde, com os valores: 6,8 → 1,7 → **2,3 t/ha**.

### F9 — `F9-aptidao` · 177 mm · Seção 3.6.5

**Mensagem:** a aptidão sai do fator mais limitante, antes e depois da correção.

- **Esquerda:** os sete fatores como linhas, cada uma com uma régua de cinco graus
  (nulo → muito forte), preenchida com o caso-exemplo.
- **Centro:** "fator mais limitante" → classe. A regra de rebaixamento por acúmulo (≥ 3 fatores
  moderados) existe no CCAE mas está **desativada** (`config_aptidao.json`,
  `REBAIXAMENTO_POR_ACUMULO: false`) — só análise de sensibilidade. Se aparecer, como nota.
- **Direita:** os dois cenários lado a lado. Fatores corrigíveis (F1, F2, F3, F4, F6) caem para
  nulo no potencial se a correção for exequível; os permanentes (F5, F7) ficam iguais.
- Escala das classes: Apta · Apta com restrições · Restrita · Inapta sem correção prévia ·
  Indeterminada (estado de erro, fora da escala).
- Atual do caso-exemplo: **Restrita, F3 potássio** (gabarito do autor). Potencial: **Apta,
  determinante F5 CTC** — lido do sistema em 31/10/2026; não tem gabarito à mão, mas decorre
  diretamente do CCAE §7.1 (corrigíveis a nulo; F5 e F7 permanecem ligeiros).

### F11 — `F11-laudo` · 177 mm · Seção 3.6.6

**Mensagem:** o que o laudo entrega, e por que está nessa ordem.

- Captura real do laudo impresso (dois talhões), com chamadas numeradas:
  cabeçalho · quadro comparativo dos talhões · as quatro doses · interpretação com a régua ·
  aptidão atual → potencial · total a comprar · ANEXO: qual adubo comprar · como aplicar ·
  de onde vem cada número.
- Barra lateral: "parte essencial" × "anexo".

### F13 — `F13-oraculo` · 85 mm · Seção 3.4

**Mensagem:** o oráculo não conhece o código.

- O Manual no topo, abrindo dois ramos que não se tocam:
  - à esquerda, **cálculo à mão** pelo autor → valores de referência
  - à direita, **transcrição → base JSON → motor** → saída do SIRAS
- Os dois se encontram só embaixo, na **comparação** (todas as saídas iguais, com tolerância
  de arredondamento).
- Ao lado, o mesmo desenho para a aptidão: CCAE congelado → gabarito à mão × implementação →
  conformidade.

---

## No apêndice (7)

| # | Arquivo | Largura | Mensagem |
|---|---|---|---|
| F2 | `F2-arquitetura` | 85 | As camadas: web (Flask, só a casca) → domínio → motor (ponto de entrada único) → conhecimento → dados; relatório e validação ao lado. O núcleo não depende do Flask |
| F6 | `F6-interpretacao` | 85 | Réguas de P (por classe de argila) e de K (por CTC), com as classes ligadas ao rendimento relativo (Manual, p. 89–90). **Limites lidos de `interpretacao_p.json` e `interpretacao_k.json`, nunca digitados** |
| F7 | `F7-adubacao` | 177 | Dois caminhos: grãos (correção, manutenção, cultivo, expectativa, N por MO e antecedente) e os demais grupos (dose por classe + variáveis próprias) |
| F8 | `F8-formulacao` | 177 | Os três caminhos e os pontos de quebra: a dose de uma fórmula avaliada nos dois pontos em que ela atende exatamente P₂O₅ ou K₂O, e o de menor custo vence |
| F10 | `F10-trilha` | 85 | Anatomia de um passo da trilha e como ele aparece em "de onde vem cada número" |
| F12 | `F12-fluxo-de-uso` | 177 | As telas reais em sequência: início → cultura → dados → espera → laudo → imprimir ou editar |
| F14 | `F14-usabilidade` | 85 | R1 (pesquisador opera, ~10 min) → R2 (participante sozinho, ~15 min) → R3 (livre, ~10 min) → questionário (depois, sozinho) |

Gráficos de resultado (concordância por grupo, severidade por heurística) entram **depois** da
coleta, com os dados reais, no mesmo padrão.

---

## Exportação

1. Um *frame* por figura, com o nome do arquivo (`F4-pipeline`) e a largura exata.
2. Exportar como **PDF**, para esta pasta.
3. Texto convertido em contorno só se a fonte não embutir.
