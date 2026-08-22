"""
Cálculo da necessidade de calagem (NC), pelo critério de grupo de cultura.

Cadeia (docs/ARQUITETURA.md, docs/decisoes/0002, docs/decisoes/0003):
cultura + sistema de manejo -> critério em criterios_calagem.json (Tab. 5.3/5.5/5.6/5.7)
-> condição de disparo (± exceção nao_aplicar_se) -> dose (Tabela 5.2 ou saturação por
bases) -> ajustes (baixo poder tampão, fator_30cm, teto de aplicação superficial) -> PRNT
-> arredondamento.

Escopo atual: decisao.tipo em {"ph_menor_que", "v_menor_igual"}; dose.tipo em
{"smp", "saturacao_bases"}. "ph_menor_que_e_al" e "usar_smp_medio_das_camadas" (SMP de
duas camadas) ainda não estão implementados e levantam NotImplementedError propositalmente
(ver testes/unidade/test_calagem.py::TestTodosOsCriteriosDaBaseSaoCobertos). Critérios
marcados "FORA DO ESCOPO do SIRAS" nas próprias notas (arroz irrigado) levantam
ErroCalagem, não NotImplementedError — não é falta de implementação, é exclusão de
escopo deliberada.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.trace import Trace

_CHAVE_COLUNA_POR_PH_ALVO = {
    5.5: "nc_ph_5_5",
    6.0: "nc_ph_6_0",
    6.5: "nc_ph_6_5",
}

# D2 (docs/decisoes/0002): SMP > 6,3 -> equações polinomiais em vez da Tabela 5.2.
_LIMITE_BAIXO_PODER_TAMPAO = 6.3

# Coeficientes das equações de baixo poder tampão (calagem_smp.json, ajustes.baixo_poder_tampao,
# p. 71-72): NC = intercepto + coef_mo*MO + coef_al*Al, em t/ha PRNT 100%.
_COEFICIENTES_BAIXO_PODER_TAMPAO = {
    5.5: (-0.653, 0.480, 1.937),
    6.0: (-0.516, 0.805, 2.435),
    6.5: (-0.122, 1.193, 2.713),
}

_OPERADORES = {
    ">=": lambda a, b: a >= b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
}


class ErroCalagem(Exception):
    """Erro de dado ausente ou inconsistente ao calcular a calagem."""


def _arredondar(valor: float, casas: int) -> float:
    """Arredonda meio-para-cima. round() nativo usa banker's rounding e nao serve aqui.

    D1 (docs/decisoes/0002): arredondamento ocorre só na saída final.
    """
    exp = Decimal(1).scaleb(-casas)
    return float(Decimal(str(valor)).quantize(exp, rounding=ROUND_HALF_UP))


def _buscar_criterio(criterios_calagem: Dict[str, Any], criterio_id: str) -> Dict[str, Any]:
    for criterio in criterios_calagem["criterios"]:
        if criterio["id"] == criterio_id:
            return criterio
    raise ErroCalagem(f"criterio_calagem '{criterio_id}' não encontrado em criterios_calagem.json")


def resolver_criterio_id(cultura_id: str, contexto: Contexto, dados: Optional[Dict[str, Any]] = None) -> str:
    """Resolve qual critério de criterios_calagem.json se aplica a uma cultura.

    Critérios específicos da espécie (ex.: macieira -> macieira_oliveira) são resolvidos
    diretamente por dados/comum/mapa_culturas.json. Critérios genéricos por grupo (ex.:
    grãos) são resolvidos cruzando grupo + sistema_manejo + condicao_area do Contexto
    contra criterios_calagem.json.

    Raises:
        ErroCalagem: cultura não mapeada, ou nenhum/mais de um critério compatível
    """
    dados = dados if dados is not None else carregar_dados_comum()
    mapa = dados["mapa_culturas"]["culturas"]

    entrada = mapa.get(cultura_id)
    if entrada is None:
        raise ErroCalagem(f"cultura '{cultura_id}' não encontrada em mapa_culturas.json")

    if "criterio_calagem" in entrada:
        return entrada["criterio_calagem"]

    grupo = entrada["grupo"]
    candidatos = [
        criterio
        for criterio in dados["criterios_calagem"]["criterios"]
        if criterio["grupo"] == grupo
        and criterio["sistema_manejo"] == contexto.sistema_manejo
        and criterio["condicao_area"] == contexto.condicao_area
    ]

    if not candidatos:
        raise ErroCalagem(
            f"nenhum critério para cultura '{cultura_id}' (grupo '{grupo}') com "
            f"sistema_manejo='{contexto.sistema_manejo}' e condicao_area='{contexto.condicao_area}'"
        )
    if len(candidatos) > 1:
        raise ErroCalagem(
            f"mais de um critério para cultura '{cultura_id}' (grupo '{grupo}') com "
            f"sistema_manejo='{contexto.sistema_manejo}' e condicao_area='{contexto.condicao_area}': "
            f"{[c['id'] for c in candidatos]}"
        )
    return candidatos[0]["id"]


def _linha_smp(tabela: list, indice_smp: float) -> Tuple[Optional[Dict[str, Any]], str]:
    """Localiza a linha da Tabela 5.2 correspondente ao índice SMP.

    D2 (docs/decisoes/0002): abaixo do mínimo usa a linha de limite inferior (a tabela é
    aberta à esquerda); acima do máximo não tem linha (dose 0, motivo smp_acima_da_tabela).
    O índice é arredondado a 1 casa antes da consulta, para casar com o passo da tabela.
    """
    smp_arredondado = round(indice_smp, 1)

    primeira = tabela[0]
    ultima = tabela[-1]

    if smp_arredondado < primeira["indice_smp"]:
        return primeira, "limite_inferior"

    if smp_arredondado > ultima["indice_smp"]:
        return None, "smp_acima_da_tabela"

    for linha in tabela:
        if abs(linha["indice_smp"] - smp_arredondado) < 1e-9:
            return linha, "consulta_direta"

    raise ErroCalagem(
        f"indice_smp={indice_smp} não corresponde a nenhuma linha da Tabela 5.2, "
        f"mesmo dentro da faixa [{primeira['indice_smp']}, {ultima['indice_smp']}]"
    )


def _nc_baixo_poder_tampao(ph_alvo: float, mo: float, al: float) -> float:
    """NC pelas equações polinomiais de baixo poder tampão (D2, docs/decisoes/0002)."""
    intercepto, coef_mo, coef_al = _COEFICIENTES_BAIXO_PODER_TAMPAO[ph_alvo]
    return intercepto + coef_mo * mo + coef_al * al


def _valor_campo(analise: AnaliseSolo, campo: str):
    """Lê um campo de AnaliseSolo pelo nome usado em criterios_calagem.json.

    'saturacao_al' passa por obter_saturacao_al() (direto ou derivado, D4).
    """
    if campo == "saturacao_al":
        return analise.obter_saturacao_al()
    return getattr(analise, campo)


def _avaliar_nao_aplicar_se(analise: AnaliseSolo, nao_aplicar_se: Dict[str, Any]) -> bool:
    """Avalia a exceção estruturada de um critério (criterios_calagem.json).

    Retorna True se a exceção se aplica (ou seja, a calagem NÃO deve ser aplicada).
    """
    operador = nao_aplicar_se["operador"]
    resultados = []
    for condicao in nao_aplicar_se["condicoes"]:
        valor_analise = _valor_campo(analise, condicao["campo"])
        comparar = _OPERADORES[condicao["op"]]
        resultados.append(comparar(valor_analise, condicao["valor"]))

    if operador == "E":
        return all(resultados)
    if operador == "OU":
        return any(resultados)
    raise ErroCalagem(f"operador de nao_aplicar_se desconhecido: '{operador}'")


def _testar_disparo(decisao: Dict[str, Any], analise: AnaliseSolo, criterio_id: str) -> Tuple[bool, Optional[str]]:
    """Testa a condição de disparo do critério. Retorna (disparou, motivo_se_nao)."""
    tipo = decisao["tipo"]

    if tipo == "ph_menor_que":
        if analise.ph_agua < decisao["ph"]:
            return True, None
        return False, "ph_acima_do_disparo"

    if tipo == "v_menor_igual":
        if analise.v_percent <= decisao["v"]:
            return True, None
        return False, "v_acima_do_alvo"

    raise NotImplementedError(
        f"criterio '{criterio_id}': decisao.tipo='{tipo}' ainda não implementado"
    )


def calcular_calagem(
    analise: AnaliseSolo,
    criterio_id: str,
    contexto: Contexto,
    trace: Trace,
) -> Dict[str, Any]:
    """Calcula a necessidade de calcário (NC) segundo o critério informado.

    Args:
        analise: análise de solo já validada
        criterio_id: id do critério em dados/comum/criterios_calagem.json
        contexto: contexto operacional (PRNT, manejo etc.)
        trace: acumulador de passos de inferência

    Returns:
        Dict com "nc_t_ha" e "motivo" (None quando há dose calculada).

    Raises:
        ErroCalagem: critério fora de escopo do SIRAS, ou dado inconsistente
        NotImplementedError: critério fora do escopo implementado hoje
    """
    dados = carregar_dados_comum()
    criterio = _buscar_criterio(dados["criterios_calagem"], criterio_id)

    if any("fora do escopo" in nota.lower() for nota in criterio.get("notas", [])):
        raise ErroCalagem(
            f"criterio '{criterio_id}' está fora do escopo do SIRAS "
            f"(ver 'notas' em criterios_calagem.json)"
        )

    decisao = criterio["decisao"]
    dose_cfg = criterio["dose"]

    if dose_cfg["tipo"] not in ("smp", "saturacao_bases"):
        raise NotImplementedError(
            f"criterio '{criterio_id}': dose.tipo='{dose_cfg['tipo']}' ainda não implementado"
        )
    if "usar_smp_medio_das_camadas" in dose_cfg:
        raise NotImplementedError(
            f"criterio '{criterio_id}': SMP médio de duas camadas ainda não implementado"
        )

    disparou, motivo = _testar_disparo(decisao, analise, criterio_id)

    if disparou and "nao_aplicar_se" in decisao:
        excecao = decisao["nao_aplicar_se"]
        if _avaliar_nao_aplicar_se(analise, excecao):
            disparou = False
            motivo = excecao["motivo"]

    # R-CAL-01: sem disparo (direto ou por exceção) -> sem necessidade de calagem (D3)
    if not disparou:
        return trace.registrar(
            regra=f"{criterio_id}: sem calagem ({motivo})",
            entradas={"ph_agua": analise.ph_agua, "v_percent": analise.v_percent},
            saida={"nc_t_ha": 0.0, "motivo": motivo},
            fonte=criterio["fonte"],
        )

    if dose_cfg["tipo"] == "saturacao_bases":
        v_alvo = dose_cfg["v_alvo"]
        nc_com_fator = ((v_alvo - analise.v_percent) / 100) * analise.ctc_ph7
        origem_nc = "saturacao_bases"
        motivo_linha = None
    else:
        ph_alvo = dose_cfg["ph_alvo"]
        fator = dose_cfg["fator"]
        chave_coluna = _CHAVE_COLUNA_POR_PH_ALVO[ph_alvo]

        linha, motivo_linha = _linha_smp(dados["calagem_smp"]["tabela"], analise.indice_smp)

        # R-CAL-02: SMP acima da Tabela 5.2 -> sem necessidade de calagem (D3)
        if linha is None:
            return trace.registrar(
                regra=f"{criterio_id}: SMP {analise.indice_smp} acima da Tabela 5.2",
                entradas={"indice_smp": analise.indice_smp},
                saida={"nc_t_ha": 0.0, "motivo": "smp_acima_da_tabela"},
                fonte="Manual 2016, Tab. 5.2, p. 70",
            )

        nc_tabela = linha[chave_coluna]

        # D2: SMP > 6,3 -> equações polinomiais (baixo poder tampão) em vez da tabela.
        if analise.indice_smp > _LIMITE_BAIXO_PODER_TAMPAO:
            nc_base = _nc_baixo_poder_tampao(ph_alvo, analise.mo, analise.al)
            origem_nc = "baixo_poder_tampao"
        else:
            nc_base = nc_tabela
            origem_nc = motivo_linha

        nc_com_fator = nc_base * fator

        # D5 (docs/decisoes/0003): incorporação a 30 cm, só quando o critério declarar o fator.
        if "fator_30cm" in dose_cfg and contexto.profundidade_incorporacao_cm == 30:
            nc_com_fator *= dose_cfg["fator_30cm"]

    # D9 (docs/decisoes/0003): teto de aplicação superficial, ANTES da conversão por PRNT.
    limite_t_ha = dose_cfg.get("limite_t_ha")
    truncado = False
    if criterio.get("modo_aplicacao") == "superficial" and limite_t_ha is not None:
        if nc_com_fator > limite_t_ha:
            nc_com_fator = limite_t_ha
            truncado = True

    # R-CAL-03: conversão por PRNT + arredondamento (D1)
    dose_real = nc_com_fator * 100 / contexto.prnt
    nc_t_ha = _arredondar(dose_real, 1)

    return trace.registrar(
        regra=f"{criterio_id}: disparo confirmado, dose calculada ({origem_nc})",
        entradas={
            "ph_agua": analise.ph_agua,
            "indice_smp": getattr(analise, "indice_smp", None),
            "v_percent": analise.v_percent,
            "prnt": contexto.prnt,
            "profundidade_incorporacao_cm": contexto.profundidade_incorporacao_cm,
            "truncado_pelo_teto_superficial": truncado,
        },
        saida={"nc_t_ha": nc_t_ha, "motivo": None},
        fonte=f"{criterio['fonte']} e Manual 2016, Tab. 5.2, p. 70",
    )


def calcular_calagem_por_cultura(
    analise: AnaliseSolo,
    cultura_id: str,
    contexto: Contexto,
    trace: Trace,
) -> Dict[str, Any]:
    """Resolve o critério a partir da cultura (mapa_culturas.json) e calcula a calagem.

    Atalho sobre resolver_criterio_id() + calcular_calagem(), para quando se conhece a
    cultura em vez do id do critério diretamente.
    """
    dados = carregar_dados_comum()
    criterio_id = resolver_criterio_id(cultura_id, contexto, dados)
    return calcular_calagem(analise, criterio_id, contexto, trace)
