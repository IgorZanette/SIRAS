"""
Leitura ao vivo: interpretação do que já foi digitado, enquanto o resto está em branco.

Alimenta o painel que acompanha o formulário (PLANO-FRONTEND §9.3). Existe no motor, e
não na camada web, por uma razão só: é a mesma interpretação do laudo, e precisa
continuar sendo. A alternativa descartada na §9.4 era reimplementar a classificação em
JavaScript — duas implementações da mesma regra divergem com o tempo, e a hipótese H1.1
mede concordância de recomendação, então uma segunda implementação não testada seria
passivo direto.

Nada aqui classifica nem calcula: cada leitura é uma chamada às mesmas funções que
gerar_laudo() usa. O que este módulo decide é apenas **quando** há dado suficiente para
cada leitura — e, quando não há, não responde, em vez de completar com zero.

`testes/unidade/test_leitura.py` trava a concordância: para uma análise completa, o que a
leitura ao vivo mostra é o que o laudo emite.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto, derivar_saturacao_al
from siras.motor.adubacao import (
    classificar_fosforo,
    classificar_potassio,
    grupo_exigencia,
)
from siras.motor.calagem import ErroCalagem, calcular_calagem
from siras.motor.trace import Trace

#: Campos que AnaliseSolo exige. Sem todos eles não há calagem para estimar: completar
#: os que faltam com zero mudaria a dose dos critérios que leem V% ou saturação por Al.
_CAMPOS_DA_ANALISE = (
    "ph_agua", "indice_smp", "argila", "mo", "p", "k", "ctc_ph7", "al", "ca", "mg", "v_percent",
)


def _tem(campos: Dict[str, Optional[float]], *nomes: str) -> bool:
    return all(campos.get(nome) is not None for nome in nomes)


def _grupos_de_exigencia(
    cultura_id: str, grupo: str, dados: Dict[str, Any]
) -> Optional[Dict[str, str]]:
    """Resolve os grupos de exigência em P e K da cultura, do mesmo jeito que a adubação
    do grupo dela resolve.

    Grãos resolvem pelas listas de interpretacao_p/k.json; os demais grupos declaram o
    campo `grupo_exigencia` na própria cultura (ADR 0004). Seguir cada caminho onde ele
    já está evita criar aqui uma terceira regra de resolução.
    """
    if grupo == "graos":
        try:
            return {
                "p": grupo_exigencia(
                    cultura_id, dados["mapa_culturas"],
                    dados["interpretacao_p"]["grupos_exigencia"], "interpretacao_p.json",
                ),
                "k": grupo_exigencia(
                    cultura_id, dados["mapa_culturas"],
                    dados["interpretacao_k"]["grupos_exigencia"], "interpretacao_k.json",
                ),
            }
        except Exception:
            return None

    from siras.motor.laudo import dados_do_grupo

    entradas = dados_do_grupo(grupo)
    if entradas is None:
        return None
    declarado = entradas.get(cultura_id, {}).get("grupo_exigencia")
    if not declarado:
        return None
    return {"p": f"grupo_{declarado['p']}", "k": f"grupo_{declarado['k']}"}


def interpretar_parcial(
    campos: Dict[str, Optional[float]],
    cultura_id: str,
    grupo: str,
    criterio_id: Optional[str] = None,
    prnt: Optional[float] = None,
    profundidade_incorporacao_cm: float = 20.0,
    dados: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Interpreta o que já dá para interpretar.

    Args:
        campos: valores já convertidos para número; ausentes vêm como None
        cultura_id: cultura escolhida
        grupo: grupo da cultura em mapa_culturas.json
        criterio_id: critério de calagem escolhido, quando houver
        prnt: PRNT do corretivo, necessário só para a estimativa de calcário

    Returns:
        Dict com "fosforo", "potassio", "saturacao_al" e "calagem". Cada chave vem None
        quando falta dado — nunca com um valor de preenchimento.
    """
    dados = dados if dados is not None else carregar_dados_comum()
    grupos = _grupos_de_exigencia(cultura_id, grupo, dados) if cultura_id else None

    resultado: Dict[str, Any] = {
        "fosforo": None, "potassio": None, "saturacao_al": None, "calagem": None,
    }

    if grupos and _tem(campos, "argila", "p"):
        leitura = classificar_fosforo(grupos["p"], campos["argila"], campos["p"], dados)
        resultado["fosforo"] = {**leitura, "valor": campos["p"]}

    if grupos and _tem(campos, "ctc_ph7", "k"):
        leitura = classificar_potassio(grupos["k"], campos["ctc_ph7"], campos["k"], dados)
        resultado["potassio"] = {**leitura, "valor": campos["k"]}

    if campos.get("saturacao_al") is not None:
        resultado["saturacao_al"] = campos["saturacao_al"]
    elif _tem(campos, "al", "ca", "mg", "k"):
        resultado["saturacao_al"] = derivar_saturacao_al(
            campos["al"], campos["ca"], campos["mg"], campos["k"]
        )

    if criterio_id and prnt is not None and _tem(campos, *_CAMPOS_DA_ANALISE):
        try:
            analise = AnaliseSolo(**{nome: campos[nome] for nome in _CAMPOS_DA_ANALISE},
                                  saturacao_al=campos.get("saturacao_al"))
            criterio = next(
                c for c in dados["criterios_calagem"]["criterios"] if c["id"] == criterio_id
            )
            contexto = Contexto(
                cultura_id=cultura_id,
                sistema_manejo=criterio["sistema_manejo"],
                condicao_area=criterio["condicao_area"],
                prnt=prnt,
                profundidade_incorporacao_cm=profundidade_incorporacao_cm,
            )
            calagem = calcular_calagem(analise, criterio_id, contexto, Trace())
            resultado["calagem"] = {**calagem, "criterio": criterio}
        except (ValueError, ErroCalagem, StopIteration, NotImplementedError):
            # Valor fora de faixa física, critério que exige subsuperfície ainda em
            # branco, critério fora de escopo. A leitura ao vivo cala; quem explica o
            # motivo é a validação do formulário, no momento de gerar o laudo.
            resultado["calagem"] = None

    return resultado


__all__ = ["interpretar_parcial"]
