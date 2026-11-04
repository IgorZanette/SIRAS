"""
Estado declarado do projeto, para a tela inicial.

POR QUE ISTO EXISTE, e por que não está escrito no template: a landing passou a
mostrar em que pé o trabalho está — ideia tirada da seção de status da referência de
design, e que para uma banca vale mais do que uma lista de recursos, porque mostra
método e não só produto.

Escrito no template, isso divergiria do `trabalho_de_conclusao/processo/roadmap.md` na primeira semana:
alguém atualiza um e esquece o outro, e a página passa a afirmar um estado que o
projeto não tem. Aqui há uma fonte só, e
`testes/unidade/test_estado_do_projeto.py` confere que cada etapa daqui aparece
no roadmap — se as duas divergirem, a suíte reprova antes de alguém publicar.

HONESTIDADE É O PONTO. A página diz o que está pronto, o que está em andamento e o
que ainda não começou. Um TCC em desenvolvimento que se apresenta como produto
acabado perde mais credibilidade do que ganha, e a regra desta página (ver o
comentário no topo de `inicio.html`) já proíbe número inventado e depoimento.
"""

from __future__ import annotations

from typing import NamedTuple, Tuple


class Etapa(NamedTuple):
    """Uma etapa do trabalho, como a tela inicial a mostra."""

    #: Título curto. Precisa aparecer, com estas palavras, no roadmap.
    nome: str
    #: "concluido" | "andamento" | "proximo" — governa a etiqueta e a cor.
    situacao: str
    #: Uma frase sobre o que a etapa entregou ou vai entregar. Sem número inventado.
    descricao: str


#: Rótulo de cada situação, e o ícone que a acompanha. Os três estados são os da
#: referência: concluído, em andamento, próximo.
ROTULO_DA_SITUACAO = {
    "concluido": ("Concluído", "confere"),
    "andamento": ("Em andamento", "regua"),
    "proximo": ("Próximo", "avanca"),
}

#: As etapas, na ordem em que o trabalho as percorre. Mantido em sincronia com
#: `trabalho_de_conclusao/processo/roadmap.md` por teste.
ETAPAS: Tuple[Etapa, ...] = (
    Etapa(
        "Base de conhecimento",
        "concluido",
        "As tabelas do Manual transcritas e conferidas à mão, com a página de origem "
        "registrada para cada uma.",
    ),
    Etapa(
        "Motor de inferência",
        "concluido",
        "Calagem, adubação e aptidão edáfica para as 61 culturas do escopo, com uma "
        "trilha que liga cada número à regra e à tabela que o produziram.",
    ),
    Etapa(
        "Aplicação web",
        "concluido",
        "As três telas, a leitura ao vivo, vários talhões num laudo e a versão "
        "impressa em A4.",
    ),
    Etapa(
        "Validação e análise dos resultados",
        "andamento",
        "A concordância com o oráculo já está medida e publicada; falta a comparação "
        "com uma ferramenta existente.",
    ),
    Etapa(
        "Avaliação de usabilidade",
        "proximo",
        "Três roteiros de teste com técnicos e agrônomos, e um questionário "
        "estruturado pelas dez heurísticas de Nielsen.",
    ),
)

#: Declaração de natureza, numa etiqueta ao lado da logo em todas as telas. Era uma
#: frase no hero ("Trabalho de Conclusão de Curso · em desenvolvimento · roda local e
#: offline"); a v2 (03/11/2026) a reduziu ao que importa a quem usa, por decisão do
#: autor. "Roda local e offline" também deixou de ser verdade para quem usa a versão
#: publicada no Render. Que é TCC continua dito no rodapé e na seção do estado.
SELO_DE_NATUREZA = "Em desenvolvimento"


__all__ = ["ETAPAS", "ROTULO_DA_SITUACAO", "SELO_DE_NATUREZA", "Etapa"]
