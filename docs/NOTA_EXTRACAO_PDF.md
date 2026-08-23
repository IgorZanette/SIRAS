# Nota de extração — o símbolo `≤` não existe na camada de texto do Manual

Registro metodológico da transcrição da base de conhecimento do SIRAS. Vale para S3 e para
todas as etapas seguintes (frutíferas, erva-mate).

## O problema

O PDF do Manual (11. ed., 2016, produzido no PageMaker 6.5) **não tem o caractere `≤` na
camada de texto**. Ele é desenhado como uma **imagem embutida de ~6 × 6 pt** posicionada à
esquerda do número. Consequência: nenhuma ferramenta de extração de texto o recupera —
`pdftotext`, `pdftotext -layout`, `pdfplumber` e `pypdf` produzem o mesmo resultado.

Pior: o comportamento é **inconsistente entre páginas**.

| Célula real | `pdftotext` devolve | Página |
|---|---|---|
| `≤ 80` (batata, N, MO > 5,0) | `80` | 184 |
| `90` (tomate, N, MO > 5,0) | `90` | 180 |
| `≤ 40` (abóbora, P, Muito alto) | `=40` | 161 |
| `≤ 40` (cana-planta, N, MO > 5,0) | `40` | 281 |

Ou seja: às vezes o `≤` some, às vezes vira `=`, e **um valor exato é indistinguível de um
valor com qualificador** só pelo texto. Transcrever a partir do texto extraído, sem
conferência, produz erro silencioso — o número fica certo e o qualificador se perde.

## A detecção usada

O glifo aparece como objeto `image` no PDF. Isso dá um detector programático e auditável:

```python
import pdfplumber
with pdfplumber.open("manual.pdf") as pdf:
    p = pdf.pages[183]                      # página 184 (índice 0)
    for im in p.images:
        if (im["x1"] - im["x0"]) < 14 and (im["bottom"] - im["top"]) < 14:
            print(im["x0"], im["top"])      # posição de um "≤"
```

Filtrar por tamanho (< 14 pt nos dois eixos) separa os glifos das figuras reais. Recortando
cada ocorrência e agrupando por hash MD5, as páginas 155–186 e 279–286 produziram **24
grupos distintos** — todos, na inspeção visual, o mesmo `≤` (a variação é só de
antialiasing/subpixel). **Nenhum `≥` ocorre nesse intervalo.**

Reinserindo os glifos na posição correta e reordenando por `(top, x0)`, obtém-se um texto
fiel ao impresso, que foi a base da transcrição.

## Procedimento adotado (repetir em S4)

1. Extrair o texto com `pdftotext -layout` para ter a estrutura das tabelas.
2. Rodar o detector de glifos-imagem nas páginas do grupo e reinseri-los.
3. **Rasterizar e conferir visualmente** ao menos uma página por padrão de tabela novo
   (`pdftoppm -jpeg -r 150 -f N -l N`), e todas as células cujo qualificador for duvidoso.
4. Rodar `valida_s3.py`: a monotonicidade das doses por classe de teor pega erro de dígito
   sem precisar reler o Manual.

Páginas conferidas visualmente nesta etapa: **161, 180, 184, 281, 282**.

## Por que isso importa para a monografia

Esta é uma ameaça concreta à validade da transcrição, e o trabalho tem um controle explícito
para ela. Vale uma frase na Seção 4.3, etapa (a) — hoje o texto diz apenas "com conferência
manual dos valores transcritos", o que não descreve o problema nem o controle. Sugestão de
redação: a transcrição combinou extração automática, reinserção programática de glifos
ausentes na camada de texto do PDF, conferência visual por amostragem de páginas e testes
automatizados de invariantes sobre as tabelas resultantes.
