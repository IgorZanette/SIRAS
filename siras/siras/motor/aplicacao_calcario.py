"""
Modo de aplicação do calcário pela situação da cultura.

A Tab. 5.6 do Manual dá à erva-mate o modo "incorporado", e o próprio Manual explica que
isso é a implantação (p. 82): com o erval já plantado a aplicação é superficial (p. 84),
e na recuperação, superficial em área total (p. 243). A dose não muda -- só o modo.

Este módulo existe à parte porque dois consumidores precisam da MESMA resposta:

    motor/laudo.py    -> o que o laudo manda fazer (cartão do calcário, trilha)
    motor/aptidao.py  -> o teto de exequibilidade da correção (CCAE v1.4, §7.2)

Se cada um resolvesse por conta própria, o laudo poderia mandar aplicar em superfície e a
aptidão projetar a correção como se o calcário fosse incorporado -- a mesma incoerência
que a v1.2 do CCAE corrigiu entre calagem e F1. E não pode morar em laudo.py, que importa
aptidao.py.

As regras ficam na base (`calagem.modo_aplicacao_por_situacao` da cultura), e não aqui.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from siras.conhecimento.carregador import (
    carregar_dados_erva_mate,
    carregar_dados_frutiferas,
    carregar_dados_graos,
    carregar_dados_hortalicas,
    carregar_dados_outras,
    carregar_dados_tuberculos,
)
from siras.dominio.analise import Contexto
from siras.dominio.nomes import buscar_por_nome

#: Carregador da adubação de cada grupo.
CARREGADOR_POR_GRUPO = {
    "graos": carregar_dados_graos,
    "hortalicas": carregar_dados_hortalicas,
    "tuberculos": carregar_dados_tuberculos,
    "outras": carregar_dados_outras,
    "frutiferas": carregar_dados_frutiferas,
    "erva_mate": carregar_dados_erva_mate,
}


def dados_do_grupo(grupo: str) -> Optional[Dict[str, Any]]:
    """Culturas transcritas na adubação de um grupo, ou None quando o grupo não as
    indexa por cultura (erva-mate indexa por programa e fase)."""
    carregar = CARREGADOR_POR_GRUPO.get(grupo)
    if carregar is None:
        return None
    carregado = carregar()
    # Grãos são o único grupo com dois arquivos (N e PK) em vez de um: o de N é o que
    # lista as culturas.
    bloco = carregado.get("adubacao") or carregado.get("adubacao_n") or {}
    return bloco.get("culturas")


def regra_de_aplicacao(
    cultura_id: str, contexto: Contexto, dados: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """A regra de modo de aplicação que a cultura declara para a situação, ou None.

    None quando a cultura não declara regras ou quando nenhuma casa -- e então vale o
    modo do critério de calagem, como sempre valeu. É o que acontece na aptidão avaliada
    sem programa informado (os casos de conformidade): sem saber se o erval existe, não
    há base para trocar o modo da tabela.

    A primeira regra cujas condições `quando` casam com as variáveis do contexto vale.
    """
    mapeada = buscar_por_nome(dados["mapa_culturas"]["culturas"], cultura_id) or {}
    culturas = dados_do_grupo(mapeada.get("grupo", "")) or {}
    entrada = buscar_por_nome(culturas, cultura_id) or {}
    regras = (entrada.get("calagem") or {}).get("modo_aplicacao_por_situacao", {}).get("regras")
    for regra in regras or ():
        if all(contexto.variaveis.get(campo) == valor for campo, valor in regra["quando"].items()):
            return regra
    return None
