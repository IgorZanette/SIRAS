# Arquitetura do SIRAS

## Princípio central

**Núcleo em Python puro; Flask é apenas uma casca.**

`siras/motor/` e `siras/dominio/` não importam Flask e não fazem I/O de rede. Consequências:

- o motor pode ser executado e testado por linha de comando, isolado da interface;
- a validação do TCC roda como teste automatizado, sem subir servidor;
- se a interface falhar no dia da apresentação, o motor ainda pode ser demonstrado.

Essa separação entre **base de conhecimento** (`dados/`) e **mecanismo de inferência**
(`siras/motor/`) é o próprio paradigma de sistemas especialistas descrito no Capítulo 3 da proposta,
materializado na estrutura de diretórios.

## Fluxo de processamento

```
Formulário web (siras/web/)
        v
AnaliseSolo + cultura_id + Contexto        (siras/dominio/)
        v
gerar_laudo()                              (siras/motor/) <- ponto de entrada único
        |
        +-- interpretacao.py   teor + contexto -> classe de disponibilidade
        |                      (P por classe de argila, K por CTC pH7)
        +-- calagem.py         cultura -> critério de grupo (Tab. 5.3-5.7)
        |                      -> índice SMP (Tab. 5.2) -> ajuste por PRNT
        +-- adubacao.py        classe + expectativa de rendimento -> N, P2O5, K2O
        +-- aptidao.py         atributos do solo -> classe de aptidão edáfica
        |
        +-- trace.py           registra cada passo aplicado, com a fonte
        v
Laudo                                       (siras/dominio/)
        v
Renderização HTML / impressão / PDF         (siras/relatorio/, siras/web/)
```

## Contrato do motor

```python
def gerar_laudo(analise: AnaliseSolo, cultura_id: str, contexto: Contexto) -> Laudo:
    # Ponto de entrada único. Puro, determinístico, sem I/O.
    ...
```

Uma única porta de entrada, usada pela camada web, pelos testes e pelos scripts de validação.

## Rastreabilidade — o Trace

Todo valor calculado registra **como** foi obtido:

```python
@dataclass
class PassoInferencia:
    regra: str        # "R-CAL-03: PD consolidado, 1/4 SMP para pH 6,0"
    entradas: dict    # {"indice_smp": 5.4, "ph_alvo": 6.0, "sistema": "plantio_direto"}
    saida: dict       # {"nc_t_ha": 1.7}
    fonte: str        # "Manual 2016, Tab. 5.3, p. 75 e Tab. 5.2, p. 70"
```

Três ganhos: laudo explicável ao usuário, depuração dirigida quando um caso de teste discorda, e
demonstração do raciocínio do sistema na apresentação.

## Camada de calagem — atenção

O módulo de calagem **não** é uma consulta direta à Tabela 5.2. A cadeia é:

1. `cultura_id` + sistema de manejo + condição da área → **critério** em
   `dados/comum/criterios_calagem.json` (Tabelas 5.3, 5.5, 5.6 e 5.7 do Manual);
2. o critério define a condição de disparo (ex.: `pH < 5,5`), o **pH alvo** da dose e o **fator**
   aplicado (1, 1/2, 1/4);
3. só então a Tabela 5.2 (`calagem_smp.json`) é consultada com o índice SMP e o pH alvo;
4. ajustes finais: PRNT do corretivo, profundidade de 30 cm (fator 1,5), faixa de plantio, limite de
   5 t/ha em aplicação superficial;
5. exceção: solos de baixo poder tampão (SMP > 6,3) usam equações polinomiais com MO e Al;
6. exceção: culturas sem pH de referência (erva-mate, florestais) usam saturação por bases para
   atingir V = 40%.

## Decisões registradas

Ver `docs/decisoes/`.
