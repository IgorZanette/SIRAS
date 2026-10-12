"""Normalização ortográfica de identificadores de cultura.

Existe porque as duas fontes de nome do Manual não concordam na grafia: a Tabela 5.1
(pH de referência) e o Anexo 2 (grupos de exigência de P e K) escrevem a mesma cultura
com acento ou sem, com hífen ou espaço, e os conjuntos de teste chegam com underscore
("acacia_negra" para "acácia-negra"). Comparar as formas cruas faz uma cultura que existe
nas duas tabelas cair em INDETERMINADA por divergência de grafia, não por lacuna de dado.

Isto é normalização ortográfica pura: não decide nada agronômico. Equivalência entre
nomes REALMENTE distintos para a mesma cultura (mirtilo/mirtileiro, tomate/tomateiro) é
julgamento e mora em dados/comum/aliases_culturas.json, não aqui.
"""

from __future__ import annotations

import unicodedata


def buscar_por_nome(indice, nome: str):
    """Procura `nome` num dicionário indexado por identificador de cultura.

    Tenta a grafia exata e, só então, a normalizada. É necessário porque os arquivos não
    concordam: mapa_culturas.json escreve 'erva-mate' com hífen e
    erva_mate_adubacao.json escreve 'erva_mate' com underscore. Sem isto a cultura existe
    nos dois lados e mesmo assim não é encontrada — o mesmo defeito que
    aliases_culturas.json resolve para a sinonímia de nomes de verdade.
    """
    if nome in indice:
        return indice[nome]
    alvo = normalizar_nome_cultura(nome)
    for chave, valor in indice.items():
        if normalizar_nome_cultura(chave) == alvo:
            return valor
    return None


def normalizar_nome_cultura(nome: str) -> str:
    """Forma canônica de comparação: minúsculas, sem acento, separador '-'.

    >>> normalizar_nome_cultura("acacia_negra")
    'acacia-negra'
    >>> normalizar_nome_cultura("Acácia-Negra")
    'acacia-negra'
    >>> normalizar_nome_cultura("Palmeira Real Australiana")
    'palmeira-real-australiana'
    """
    decomposto = unicodedata.normalize("NFD", nome.strip().lower())
    sem_acento = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_acento.replace("_", "-").replace(" ", "-")
