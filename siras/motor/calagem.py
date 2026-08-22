"""
Cálculo da necessidade de calagem (NC), pelo critério de grupo de cultura.

Cadeia (docs/ARQUITETURA.md, docs/decisoes/0002):
cultura + sistema de manejo -> critério em criterios_calagem.json (Tab. 5.3/5.5/5.6/5.7)
-> condição de disparo, pH alvo e fator -> Tabela 5.2 (calagem_smp.json) -> PRNT -> arredondamento.

Escopo atual: apenas critérios com decisao.tipo == "ph_menor_que" (sem exceção
'nao_aplicar_se') e dose.tipo == "smp" sem 'limite_t_ha', 'usar_smp_medio_das_camadas' nem
'fator_30cm'. Plantio direto, aplicação superficial, SMP médio de camadas, incorporação a
30 cm, faixa de plantio e saturação por bases ainda não estão implementados e levantam
NotImplementedError propositalmente, em vez de produzir um resultado silenciosamente
incompleto (ver testes/unidade/test_calagem.py::TestCriterioInvalido).
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
        ErroCalagem: critério ou linha da Tabela 5.2 não encontrados
        NotImplementedError: critério fora do escopo implementado hoje
    """
    dados = carregar_dados_comum()
    criterio = _buscar_criterio(dados["criterios_calagem"], criterio_id)

    decisao = criterio["decisao"]
    if decisao["tipo"] != "ph_menor_que":
        raise NotImplementedError(
            f"criterio '{criterio_id}': decisao.tipo='{decisao['tipo']}' ainda não implementado"
        )
    if "nao_aplicar_se" in decisao:
        raise NotImplementedError(
            f"criterio '{criterio_id}': exceção 'nao_aplicar_se' ainda não implementada"
        )

    dose_cfg = criterio["dose"]
    if dose_cfg["tipo"] != "smp":
        raise NotImplementedError(
            f"criterio '{criterio_id}': dose.tipo='{dose_cfg['tipo']}' ainda não implementado"
        )
    if "limite_t_ha" in dose_cfg or "usar_smp_medio_das_camadas" in dose_cfg:
        raise NotImplementedError(
            f"criterio '{criterio_id}': aplicação superficial/SMP médio ainda não implementados"
        )
    if "fator_30cm" in dose_cfg:
        raise NotImplementedError(
            f"criterio '{criterio_id}': ajuste de incorporação a 30 cm (fator_30cm) "
            f"ainda não implementado"
        )

    limite_disparo = decisao["ph"]

    # R-CAL-01: pH >= limite de disparo do critério -> sem necessidade de calagem (D3)
    if analise.ph_agua >= limite_disparo:
        return trace.registrar(
            regra=f"{criterio_id}: sem disparo (pH {analise.ph_agua} >= {limite_disparo})",
            entradas={"ph_agua": analise.ph_agua, "limite_disparo": limite_disparo},
            saida={"nc_t_ha": 0.0, "motivo": "ph_acima_do_disparo"},
            fonte=criterio["fonte"],
        )

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

    # R-CAL-03: disparo confirmado -> Tab. 5.2 x fator do critério x conversão por PRNT
    nc_tabela = linha[chave_coluna]
    nc_com_fator = nc_tabela * fator
    dose_real = nc_com_fator * 100 / contexto.prnt
    nc_t_ha = _arredondar(dose_real, 1)

    return trace.registrar(
        regra=f"{criterio_id}: disparo pH<{limite_disparo}, alvo {ph_alvo}, fator {fator}",
        entradas={
            "ph_agua": analise.ph_agua,
            "indice_smp": analise.indice_smp,
            "leitura_smp": motivo_linha,
            "nc_tabela": nc_tabela,
            "fator": fator,
            "prnt": contexto.prnt,
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
