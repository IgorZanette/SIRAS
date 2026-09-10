# CCAE — Especificação de Implementação

Companheiro técnico do `CCAE-v1.0.md`. Este arquivo é o que você entrega ao Claude Code junto com o Caderno.

**Regra de ouro:** nenhum limiar numérico no código Python. Todos vivem em JSON, versionados. O motor é um interpretador genérico das tabelas.

> **Nota de adaptação (implementação real, docs/decisoes/0005):** este documento foi escrito antes de `siras/` existir e descreve um layout genérico. A implementação efetiva do motor de aptidão reaproveita a arquitetura já construída para calagem e adubação (`siras/dominio/analise.py`, `siras/motor/trace.py`, `siras/conhecimento/carregador.py`) em vez de recriar um layout próprio do zero, e a maioria das tabelas numéricas de F2 a F6 já estava transcrita e conferida em `dados/comum/` antes deste módulo — o motor de aptidão referencia esses arquivos por nome em vez de duplicá-los. A Seção 1 (layout de arquivos) abaixo é mantida como registro do raciocínio original; o layout real está documentado em `docs/decisoes/0005-motor-de-aptidao-edafica.md`.

---

## 1. Layout de arquivos

```
siras/
├── dados/
│   ├── criterios_aptidao.json      # tabelas + mapeamentos (Seções 4, 6)
│   ├── catalogo_culturas.json      # cultura -> pH ref, grupo_p, grupo_k
│   └── config_aptidao.json         # parâmetros do Apêndice A
├── motor/
│   ├── interpretacao.py            # classes de disponibilidade (Manual Cap. 6)
│   ├── aptidao.py                  # fatores F1..F7 + composição
│   └── faixas.py                   # utilitário de intervalos
└── testes/
    ├── gabarito_conformidade.csv   # gerado À MÃO, antes do código
    └── test_conformidade.py
```

---

## 2. Tratamento canônico de intervalos

**O problema:** as tabelas do Manual publicam faixas como `Muito baixo ≤ 6,0` e `Baixo 6,1 – 12,0`. O valor 6,05 não pertence a nenhuma. Isso é artefato de arredondamento a uma casa decimal, não uma lacuna real.

**A regra:** representar cada classe apenas pelo **limite superior** e usar comparação `≤`, em ordem crescente. Elimina lacunas e sobreposições por construção.

```python
# faixas.py
from decimal import Decimal

def classificar_por_limite_superior(valor, limites):
    """
    limites: lista ordenada [(limite_superior_ou_None, classe), ...]
    O último elemento tem limite None (classe aberta superiormente).

    Ex.: [(6.0,"MUITO_BAIXO"), (12.0,"BAIXO"), (18.0,"MEDIO"),
          (36.0,"ALTO"), (None,"MUITO_ALTO")]

    Usa Decimal porque comparações de fronteira em float falham:
    0.1+0.2 > 0.3 é True em ponto flutuante binário, e os casos de
    teste de fronteira do CCAE existem justamente para bater no limite.
    """
    v = Decimal(str(valor))
    for limite, classe in limites:
        if limite is None or v <= Decimal(str(limite)):
            return classe
    raise ValueError("tabela de limites malformada: falta classe aberta")
```

Converter **todas** as tabelas das Seções 6 (F2, F3) para esse formato ao montar o JSON. A faixa `Baixo 6,1 – 12,0` vira apenas `12.0`.

> **Nota de adaptação:** `siras/conhecimento/carregador.py` e `siras/motor/adubacao.py` já implementavam essa mesma convenção antes deste módulo, com formato `{"classe": ..., "de": ..., "ate": ...}` (de exclusive, ate inclusive, `None` = infinito) em vez de tuplas `(limite, classe)`. O motor de aptidão reaproveita `classificar_faixa()` de `motor/adubacao.py` em vez de introduzir `faixas.py` como um segundo formato paralelo.

---

## 3. Estrutura de `criterios_aptidao.json`

```json
{
  "versao": "1.0",
  "graus": {
    "NULO": 0, "LIGEIRO": 1, "MODERADO": 2,
    "FORTE": 3, "MUITO_FORTE": 4
  },

  "mapeamento_disponibilidade_grau": {
    "_fonte": "Manual RS/SC 2016, Cap. 6, p. 89-90 (rendimento relativo)",
    "MUITO_BAIXO": "MUITO_FORTE",
    "BAIXO": "FORTE",
    "MEDIO": "MODERADO",
    "ALTO": "NULO",
    "MUITO_ALTO": "NULO"
  },

  "classes_argila": {
    "_fonte": "Manual RS/SC 2016, nota das Tab. 6.3-6.5",
    "limites": [[20.0, "4"], [40.0, "3"], [60.0, "2"], [null, "1"]]
  },

  "classes_ctc": {
    "_fonte": "Manual RS/SC 2016, Tab. 6.1",
    "limites": [[7.5, "BAIXA"], [15.0, "MEDIA"],
                [30.0, "ALTA"], [null, "MUITO_ALTA"]]
  },

  "F2_fosforo": {
    "_fonte": "Manual RS/SC 2016, Tab. 6.2 a 6.5",
    "_unidade": "mg P/dm3 (Mehlich-1)",
    "grupo_1": {
      "_tabela": "6.3",
      "1": [[5.0,"MUITO_BAIXO"],[10.0,"BAIXO"],[15.0,"MEDIO"],[30.0,"ALTO"],[null,"MUITO_ALTO"]],
      "2": [[7.0,"MUITO_BAIXO"],[14.0,"BAIXO"],[21.0,"MEDIO"],[42.0,"ALTO"],[null,"MUITO_ALTO"]],
      "3": [[10.0,"MUITO_BAIXO"],[20.0,"BAIXO"],[30.0,"MEDIO"],[60.0,"ALTO"],[null,"MUITO_ALTO"]],
      "4": [[17.0,"MUITO_BAIXO"],[34.0,"BAIXO"],[51.0,"MEDIO"],[102.0,"ALTO"],[null,"MUITO_ALTO"]]
    },
    "grupo_2": {
      "_tabela": "6.4",
      "1": [[3.0,"MUITO_BAIXO"],[6.0,"BAIXO"],[9.0,"MEDIO"],[18.0,"ALTO"],[null,"MUITO_ALTO"]],
      "2": [[4.0,"MUITO_BAIXO"],[8.0,"BAIXO"],[12.0,"MEDIO"],[24.0,"ALTO"],[null,"MUITO_ALTO"]],
      "3": [[6.0,"MUITO_BAIXO"],[12.0,"BAIXO"],[18.0,"MEDIO"],[36.0,"ALTO"],[null,"MUITO_ALTO"]],
      "4": [[10.0,"MUITO_BAIXO"],[20.0,"BAIXO"],[30.0,"MEDIO"],[60.0,"ALTO"],[null,"MUITO_ALTO"]]
    },
    "grupo_3": {
      "_tabela": "6.5",
      "_pendencia": "col. 1 faixa Baixo: PDF traz 1,5-3,0; adotado 1,6-3,0 (A-10)",
      "1": [[1.5,"MUITO_BAIXO"],[3.0,"BAIXO"],[4.5,"MEDIO"],[9.0,"ALTO"],[null,"MUITO_ALTO"]],
      "2": [[2.0,"MUITO_BAIXO"],[4.0,"BAIXO"],[6.0,"MEDIO"],[12.0,"ALTO"],[null,"MUITO_ALTO"]],
      "3": [[3.0,"MUITO_BAIXO"],[6.0,"BAIXO"],[9.0,"MEDIO"],[18.0,"ALTO"],[null,"MUITO_ALTO"]],
      "4": [[5.0,"MUITO_BAIXO"],[10.0,"BAIXO"],[15.0,"MEDIO"],[30.0,"ALTO"],[null,"MUITO_ALTO"]]
    }
  },

  "F3_potassio": {
    "_fonte": "Manual RS/SC 2016, Tab. 6.7 a 6.10",
    "_unidade": "mg K/dm3 (Mehlich-1)",
    "grupo_1": {
      "_tabela": "6.8",
      "BAIXA":      [[30,"MUITO_BAIXO"],[60,"BAIXO"],[90,"MEDIO"],[180,"ALTO"],[null,"MUITO_ALTO"]],
      "MEDIA":      [[45,"MUITO_BAIXO"],[90,"BAIXO"],[135,"MEDIO"],[270,"ALTO"],[null,"MUITO_ALTO"]],
      "ALTA":       [[60,"MUITO_BAIXO"],[120,"BAIXO"],[180,"MEDIO"],[360,"ALTO"],[null,"MUITO_ALTO"]],
      "MUITO_ALTA": [[70,"MUITO_BAIXO"],[140,"BAIXO"],[210,"MEDIO"],[420,"ALTO"],[null,"MUITO_ALTO"]]
    },
    "grupo_2": {
      "_tabela": "6.9",
      "BAIXA":      [[20,"MUITO_BAIXO"],[40,"BAIXO"],[60,"MEDIO"],[120,"ALTO"],[null,"MUITO_ALTO"]],
      "MEDIA":      [[30,"MUITO_BAIXO"],[60,"BAIXO"],[90,"MEDIO"],[180,"ALTO"],[null,"MUITO_ALTO"]],
      "ALTA":       [[40,"MUITO_BAIXO"],[80,"BAIXO"],[120,"MEDIO"],[240,"ALTO"],[null,"MUITO_ALTO"]],
      "MUITO_ALTA": [[45,"MUITO_BAIXO"],[90,"BAIXO"],[135,"MEDIO"],[270,"ALTO"],[null,"MUITO_ALTO"]]
    },
    "grupo_3": {
      "_tabela": "6.10",
      "BAIXA":      [[15,"MUITO_BAIXO"],[30,"BAIXO"],[45,"MEDIO"],[90,"ALTO"],[null,"MUITO_ALTO"]],
      "MEDIA":      [[20,"MUITO_BAIXO"],[40,"BAIXO"],[60,"MEDIO"],[120,"ALTO"],[null,"MUITO_ALTO"]],
      "ALTA":       [[30,"MUITO_BAIXO"],[60,"BAIXO"],[90,"MEDIO"],[180,"ALTO"],[null,"MUITO_ALTO"]],
      "MUITO_ALTA": [[35,"MUITO_BAIXO"],[70,"BAIXO"],[105,"MEDIO"],[210,"ALTO"],[null,"MUITO_ALTO"]]
    }
  },

  "F1_acidez": {
    "_fonte": "Manual RS/SC 2016, Tab. 5.1 e texto p. 69; Sobral et al. 2015 Tab. 4",
    "com_ph_referencia": {
      "ph_acima_referencia": "NULO",
      "ph_entre_5_5_e_referencia": "LIGEIRO",
      "ph_abaixo_5_5_por_m_percent":
        [[30.0,"MODERADO"],[50.0,"FORTE"],[null,"MUITO_FORTE"]]
    },
    "sem_ph_referencia": {
      "_fonte": "Manual RS/SC 2016, Tab. 5.6 e 5.7",
      "v_minimo": 40.0,
      "excecao_ca_minimo": 4.0,
      "excecao_mg_minimo": 1.0,
      "grau_se_deficiente": "MODERADO"
    }
  },

  "F4_ca_mg": {
    "_fonte": "Manual RS/SC 2016, Tab. 6.11",
    "ca": [[2.0,"BAIXO"],[4.0,"MEDIO"],[null,"ALTO"]],
    "mg": [[0.5,"BAIXO"],[1.0,"MEDIO"],[null,"ALTO"]],
    "mapeamento": {"BAIXO":"MODERADO","MEDIO":"LIGEIRO","ALTO":"NULO"}
  },

  "F5_ctc": {
    "_fonte": "Manual RS/SC 2016, Tab. 6.1",
    "mapeamento": {"BAIXA":"MODERADO","MEDIA":"LIGEIRO",
                   "ALTA":"NULO","MUITO_ALTA":"NULO"}
  },

  "F6_mo": {
    "_fonte": "Manual RS/SC 2016, Tab. 6.1",
    "_unidade": "% (dag/kg)",
    "limites": [[2.5,"BAIXO"],[5.0,"MEDIO"],[null,"ALTO"]],
    "mapeamento": {"BAIXO":"MODERADO","MEDIO":"LIGEIRO","ALTO":"NULO"}
  },

  "F7_textura": {
    "_fonte": "Manual RS/SC 2016, Tab. 6.1 e texto p. 72",
    "mapeamento_por_classe_argila": {"4":"MODERADO","3":"LIGEIRO",
                                     "2":"NULO","1":"NULO"}
  },

  "composicao": {
    "_fonte": "Ramalho Filho e Beek 1995, apud Hofig et al. 2015 p. 357",
    "grau_para_classe": {
      "0":"APTA","1":"APTA","2":"APTA_COM_RESTRICOES",
      "3":"RESTRITA","4":"INAPTA_SEM_CORRECAO"
    },
    "ordem_classes": ["APTA","APTA_COM_RESTRICOES",
                      "RESTRITA","INAPTA_SEM_CORRECAO"]
  }
}
```

**Note o campo `_fonte` em cada bloco.** Ele é carregado junto com os dados e propagado para o campo `fonte` da saída. É o que torna a rastreabilidade automática em vez de dependente de disciplina do programador.

> **Nota de adaptação:** o `dados/comum/criterios_aptidao.json` efetivamente criado não duplica `classes_argila`, `classes_ctc`, as tabelas de `F2_fosforo`/`F3_potassio` nem os limites numéricos de `F4_ca_mg`/`F6_mo` — essas faixas já existiam, transcritas e conferidas, em `interpretacao_geral.json`, `interpretacao_p.json` e `interpretacao_k.json` antes deste módulo. `criterios_aptidao.json` guarda só a camada que não vem do Manual: os graus de Ramalho Filho e Beek, o mapeamento disponibilidade→grau, os limiares de m% (Sobral et al.), e os mapeamentos classe→grau de F4/F5/F6/F7. Ver `docs/decisoes/0005`.

---

## 4. `config_aptidao.json` — parâmetros do Apêndice A

```json
{
  "REBAIXAMENTO_POR_ACUMULO": false,
  "REBAIXAMENTO_MIN_FATORES": 3,
  "F4_GRAU_MAXIMO": "MODERADO",
  "F5_GRAU_MAXIMO": "MODERADO",
  "F6_GRAU_MAXIMO": "MODERADO",
  "F7_ATIVO": true,
  "MUITO_ALTO_REBAIXA": false,
  "NC_MAX_INCORPORADO_T_HA": 20.0,
  "NC_MAX_SUPERFICIAL_T_HA": 5.0
}
```

Cada chave corresponde a uma linha do Apêndice A. A análise de sensibilidade (CCAE §9.4) é implementada rodando o conjunto com variações deste arquivo — nada de mexer em código.

---

## 5. `catalogo_culturas.json`

```json
{
  "milho": {
    "nome_exibicao": "Milho",
    "grupo_sistema": "graos",
    "ph_referencia": 6.0,
    "grupo_p": 2,
    "grupo_k": 2,
    "fonte_ph": "Manual RS/SC 2016, Tab. 5.1"
  },
  "alho": {
    "nome_exibicao": "Alho",
    "grupo_sistema": "hortalicas",
    "ph_referencia": 6.0,
    "grupo_p": 1,
    "grupo_k": 1,
    "fonte_ph": "Manual RS/SC 2016, Tab. 5.1"
  },
  "eucalipto": {
    "nome_exibicao": "Eucalipto",
    "grupo_sistema": "florestais",
    "ph_referencia": null,
    "grupo_p": 3,
    "grupo_k": 3,
    "fonte_ph": "Manual RS/SC 2016, Tab. 5.1 (sem pH de referencia)"
  },
  "tabaco": {
    "nome_exibicao": "Tabaco",
    "grupo_sistema": "outras_comerciais",
    "ph_referencia": 6.0,
    "grupo_p": 3,
    "grupo_k": 3,
    "fonte_ph": "Manual RS/SC 2016, Tab. 5.1 e 5.7"
  }
}
```

> **Armadilha conhecida:** `grupo_p` e `grupo_k` divergem em várias culturas. A mandioquinha-salsa e o tomateiro são Grupo 1 em K e não em P; a mandioca é Grupo 2 em K e Grupo 3 em P. Nunca derive um do outro. Escreva um teste que percorre o catálogo e confere cada entrada contra as Tabelas 6.2 e 6.7 — a lista completa está no Anexo 2 do Manual.

> **Nota de adaptação:** não existe `catalogo_culturas.json` na implementação real. `grupo_p`/`grupo_k` já eram resolvidos dinamicamente por `motor/adubacao.py` (função `grupo_exigencia`, hoje pública) a partir das listas `grupos_exigencia[].culturas` de `interpretacao_p.json`/`interpretacao_k.json`, cruzadas com `mapa_culturas.json` como *fallback* para grãos. O motor de aptidão reaproveita essa mesma função em vez de duplicar o catálogo — elimina exatamente a armadilha descrita acima, porque há uma única fonte para cada grupo.

---

## 6. Contrato do motor

```python
# aptidao.py
from dataclasses import dataclass, field

@dataclass(frozen=True)
class AvaliacaoFator:
    id: str                 # "F2_fosforo"
    grau: int               # 0..4
    rotulo: str             # "FORTE"
    evidencia: str          # texto legível com os valores que levaram ao grau
    fonte: str              # propagado do campo _fonte do JSON

@dataclass(frozen=True)
class ResultadoAptidao:
    cenario: str            # "ATUAL" | "POTENCIAL"
    classe: str
    grau_final: int
    fator_determinante: str
    fatores: list           # list[AvaliacaoFator]
    alertas: list = field(default_factory=list)
    rebaixamento_aplicado: bool = False
    versao_criterios: str = "1.0"


def avaliar_aptidao(analise, cultura, cenario, criterios, config):
    """
    Retorna ResultadoAptidao. Função PURA: sem I/O, sem estado global,
    sem data/hora. Mesma entrada -> mesma saída, sempre. Isso é o que
    torna o conjunto de conformidade reprodutível e o gabarito comparável.
    """
```

**Ordem de execução obrigatória:**

1. Validar entrada — se inválida, `INDETERMINADA` e retorna.
2. Converter Mehlich-3 → Mehlich-1, se aplicável.
3. Derivar `V%`, `m%`, `K_cmolc` se ausentes.
4. Resolver `classe_argila` e `classe_ctc`.
5. Avaliar F1..F7, aplicando os tetos de `config`.
6. Se `cenario == "POTENCIAL"`, zerar os fatores `CORRIGIVEL` conforme CCAE §7, respeitando o critério de exequibilidade da calagem.
7. `grau_final = max(...)`; identificar `fator_determinante` (o de maior grau; empate resolve pela ordem F1<F2<...<F7, determinística).
8. Mapear para classe.
9. Se `config["REBAIXAMENTO_POR_ACUMULO"]`, aplicar §8.2.

> **Nota de adaptação:** a assinatura real é `avaliar_aptidao(analise: AnaliseSolo, cultura_id: str, cenario: str, contexto: Contexto, trace: Trace, dados=None) -> ResultadoAptidao` — reaproveita `AnaliseSolo`/`Contexto`/`Trace` de `siras/dominio/` e `siras/motor/trace.py`, e carrega `criterios`/`config` internamente via `carregar_dados_comum()` (como `calagem.py` e `adubacao.py` já fazem) em vez de recebê-los como parâmetros separados. A validação de faixa física de entrada (item 1) já é feita por `AnaliseSolo.__post_init__` antes do motor ser chamado; `avaliar_aptidao` cobre apenas o caso de cultura não encontrada nos catálogos, retornando `INDETERMINADA` em vez de lançar exceção (decisão registrada em `docs/decisoes/0005`, diferente do estilo de exceção de `calagem.py`/`adubacao.py`, e deliberada: o CCAE especifica `INDETERMINADA` como valor de retorno de primeira classe, não como erro de programação). Para o passo 6, a exequibilidade da calagem é resolvida chamando `motor.calagem.calcular_calagem_por_cultura()` em vez de reimplementar o cálculo de NC.

---

## 7. Testes

```python
# test_conformidade.py
import csv, pytest
from motor.aptidao import avaliar_aptidao

def carregar_gabarito():
    """
    Lê testes/gabarito_conformidade.csv — planilha preenchida À MÃO
    a partir do CCAE, antes da implementação. Colunas mínimas:
    id_caso, [atributos da análise], cultura, cenario,
    classe_esperada, fator_determinante_esperado, data_gabarito, autor_gabarito
    """
    with open("testes/gabarito_conformidade.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))

@pytest.mark.parametrize("caso", carregar_gabarito(), ids=lambda c: c["id_caso"])
def test_conformidade(caso, criterios, config_baseline):
    r = avaliar_aptidao(montar_analise(caso), caso["cultura"],
                        caso["cenario"], criterios, config_baseline)
    assert r.classe == caso["classe_esperada"], (
        f"{caso['id_caso']}: esperado {caso['classe_esperada']}, "
        f"obtido {r.classe} (determinante: {r.fator_determinante})"
    )
    # O fator determinante também é verificado: acertar a classe pelo
    # motivo errado é defeito que a classe sozinha esconderia.
    assert r.fator_determinante == caso["fator_determinante_esperado"]
```

Testes obrigatórios adicionais:

- **Fronteiras:** um teste por limiar publicado, no valor exato e a ±0,1.
- **Monotonicidade:** para P e K, aumentar o teor mantendo o resto constante nunca deve piorar o grau. Property-based com Hypothesis pega inversões de tabela de imediato.
- **Determinismo:** mesma entrada 100 vezes → mesma saída.
- **Integridade do catálogo:** todo `grupo_p` e `grupo_k` confere com as Tabelas 6.2 e 6.7.
- **Cobertura:** `coverage.py` sobre `motor/aptidao.py`, meta 100% de ramos.

> **Nota de adaptação:** a implementação real usa `testes/casos/casos_aptidao.json` (mesmo formato dos demais conjuntos de casos do SIRAS, ver `testes/casos/casos_recomendacao.json`) em vez de um CSV próprio, lido por `testes/unidade/test_casos_aptidao.py`. O `referencia` de cada caso continua sendo preenchido exclusivamente pelo autor, sem consultar o código (CLAUDE.md, regra absoluta de dados agronômicos) — o arquivo já existe como esqueleto (`testes/casos/casos_aptidao.json`) com um caso de exemplo a remover.

---

## 8. Ordem de trabalho recomendada

| # | Etapa | Saída |
|---|---|---|
| 1 | Conferir a pendência A-10 no Manual impresso | Apêndice A atualizado |
| 2 | Aprovar o CCAE com o orientador | E-mail datado — **concluído:** e-mail do Prof. Dr. Rafael Rieder em 10/09/2026, 14:04, transcrito no Apêndice D do `CCAE-v1.1.md` |
| 3 | `git tag criterios-v1.0` | Tag no repositório — **pendente:** a aprovação recaiu sobre a v1.1; a tag a criar é `criterios-v1.1` |
| 4 | Transcrever tabelas para JSON + conferência manual | `criterios_aptidao.json` |
| 5 | Preencher `gabarito_conformidade.csv` à mão | 60 casos com data e autor |
| 6 | Implementar `faixas.py`, `interpretacao.py`, `aptidao.py` | Módulos |
| 7 | Rodar conformidade; corrigir defeitos; registrar no Apêndice B | 100% |
| 8 | Análise de sensibilidade (4 configurações) | Tabela para a monografia |
| 9 | Gerar 10 laudos e o formulário de auditoria | Pacote para o agrônomo |

As etapas 1 a 3 acontecem **antes** de qualquer linha de código. É a ordem que sustenta a alegação de não-circularidade.

> **Nota de adaptação:** etapa 1 (A-10) foi resolvida sem necessidade de conferência do impresso — ver a nota na Seção 3 acima e o Apêndice A do CCAE-v1.0.md. Etapas 4-6 foram adaptadas à arquitetura existente conforme as notas desta seção e `docs/decisoes/0005`. Etapa 5 (`gabarito_conformidade.csv`) permanece pendente e é do autor, não do Claude Code — `testes/casos/casos_aptidao.json` está pronto para recebê-la.
