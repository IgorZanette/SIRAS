from __future__ import annotations

import ast
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.trace import Trace


def _normalizar_numero(valor: Any) -> float:
    if isinstance(valor, str):
        valor = valor.replace(".", "").replace(",", ".")
    return float(valor)


def _obter_criterios() -> List[Dict[str, Any]]:
    dados = carregar_dados_comum("criterios_calagem.json")
    return dados.get("criterios", [])


def _obter_tabela_smp() -> Dict[str, Any]:
    return carregar_dados_comum("calagem_smp.json")


def _obter_criterio_mais_proximo(
    cultura_id: str,
    sistema_manejo: str,
    condicao_area: str,
) -> Dict[str, Any]:
    criterios = _obter_criterios()

    for criterio in criterios:
        if criterio.get("grupo") == cultura_id:
            if criterio.get("sistema_manejo") == sistema_manejo and criterio.get("condicao_area") == condicao_area:
                return criterio
            if criterio.get("sistema_manejo") == sistema_manejo or criterio.get("sistema_manejo") == "qualquer":
                return criterio

    for criterio in criterios:
        if criterio.get("sistema_manejo") == sistema_manejo and criterio.get("condicao_area") == condicao_area:
            return criterio

    for criterio in criterios:
        if criterio.get("sistema_manejo") == sistema_manejo or criterio.get("sistema_manejo") == "qualquer":
            return criterio

    raise ValueError(
        f"Não foi encontrado critério de calagem para cultura='{cultura_id}', "
        f"sistema_manejo='{sistema_manejo}', condicao_area='{condicao_area}'."
    )


def _resolver_linha_tabela_smp(tabela: List[Dict[str, Any]], indice_smp: float, ph_alvo: float) -> Optional[Dict[str, Any]]:
    for linha in tabela:
        indice = linha.get("indice_smp")
        if indice == "<=4.4":
            valor_smp = 4.4
        else:
            valor_smp = _normalizar_numero(indice)

        if abs(valor_smp - indice_smp) < 1e-9:
            return linha

    # fallback: usa a linha "<=4.4" se o valor estiver abaixo do mínimo
    if indice_smp < 4.4:
        for linha in tabela:
            if linha.get("indice_smp") == "<=4.4":
                return linha

    return None


def _avaliar_disparo(analise: AnaliseSolo, criterio: Dict[str, Any]) -> bool:
    decisao = criterio.get("decisao", {})
    tipo = decisao.get("tipo")

    if tipo == "ph_menor_que":
        ph_limite = decisao.get("ph")
        return analise.ph_agua < ph_limite

    if tipo == "ph_menor_que_e_al":
        ph_limite = decisao.get("ph")
        al_limite = decisao.get("saturacao_al_maior_igual")
        if analise.ph_agua >= ph_limite:
            return False
        return analise.al >= al_limite if al_limite is not None else True

    if tipo == "v_menor_igual":
        alvo = decisao.get("v")
        return analise.v_percent <= alvo

    raise ValueError(f"Tipo de decisão de calagem não suportado: '{tipo}'.")


def _expressao_para_valor(expressao: str, variaveis: Dict[str, float]) -> float:
    codigo = ast.parse(expressao, mode="eval")

    def _resolver(node: ast.AST):
        if isinstance(node, ast.BinOp):
            esquerda = _resolver(node.left)
            direita = _resolver(node.right)
            if isinstance(node.op, ast.Add):
                return esquerda + direita
            if isinstance(node.op, ast.Sub):
                return esquerda - direita
            if isinstance(node.op, ast.Mult):
                return esquerda * direita
            if isinstance(node.op, ast.Div):
                return esquerda / direita
            raise ValueError(f"Operador não suportado na equação: {ast.dump(node)}")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -_resolver(node.operand)
        if isinstance(node, ast.Name):
            nome = node.id
            if nome not in variaveis:
                raise ValueError(f"Variável da equação não reconhecida: '{nome}'.")
            return variaveis[nome]
        if isinstance(node, ast.Constant):
            return float(node.value)
        raise ValueError(f"Expressão não suportada: {ast.dump(node)}")

    return float(_resolver(codigo.body))


def _calcular_ajuste_baixo_poder_tampao(analise: AnaliseSolo, ph_alvo: float) -> float:
    tabela = _obter_tabela_smp()
    ajustes = tabela.get("ajustes", {}).get("baixo_poder_tampao", {})
    equacoes = ajustes.get("equacoes_t_ha_prnt100", {})
    chave = {
        5.5: "ph_5_5",
        6.0: "ph_6_0",
        6.5: "ph_6_5",
    }.get(ph_alvo)
    if chave is None:
        raise ValueError(f"pH alvo não suportado para ajuste de baixo poder tampão: '{ph_alvo}'.")

    expressao = equacoes[chave]
    valor = _expressao_para_valor(expressao, {"MO": analise.mo, "Al": analise.al})
    return max(0.0, valor)


def _calcular_nc_por_saturacao_bases(analise: AnaliseSolo, v_alvo: float) -> float:
    diferenca = v_alvo - analise.v_percent
    if diferenca <= 0:
        return 0.0
    return ((diferenca / 100.0) * analise.ctc_ph7)


def calcular_necessidade_calagem(
    analise: AnaliseSolo,
    cultura_id: str,
    contexto: Contexto,
    trace: Optional[Trace] = None,
) -> float:
    """Calcula a dose de calcário necessária para a cultura e contexto fornecidos.

    Retorna a dose em t/ha, considerando a cadeia do Manual CQFS-RS/SC e registrando
    cada passo no Trace para rastreabilidade.
    """

    trace = trace or Trace()

    criterio = _obter_criterio_mais_proximo(cultura_id, contexto.sistema_manejo, contexto.condicao_area)
    trace.registrar(
        regra="R-CAL-01: seleção do critério de calagem",
        entradas={
            "cultura_id": cultura_id,
            "sistema_manejo": contexto.sistema_manejo,
            "condicao_area": contexto.condicao_area,
        },
        saida={"criterio": criterio.get("id"), "grupo": criterio.get("grupo")},
        fonte="Manual 2016, Tab. 5.3-5.7, p. 75-86; dados/comum/criterios_calagem.json",
    )

    decisao = criterio.get("decisao", {})
    tipo_decisao = decisao.get("tipo")
    if not _avaliar_disparo(analise, criterio):
        trace.registrar(
            regra="R-CAL-00: sem necessidade de calagem",
            entradas={
                "ph_agua": analise.ph_agua,
                "tipo_decisao": tipo_decisao,
                "condicao": decisao,
            },
            saida={"nc_t_ha": 0.0},
            fonte="Manual 2016, Tabela 5.3-5.7, p. 75-86",
        )
        return 0.0

    dose_criterio = criterio.get("dose", {})
    tipo_dose = dose_criterio.get("tipo")
    fator = float(dose_criterio.get("fator", 1.0))
    ph_alvo = float(dose_criterio.get("ph_alvo", 6.0))

    if tipo_dose == "saturacao_bases":
        nc = _calcular_nc_por_saturacao_bases(analise, float(dose_criterio.get("v_alvo", analise.v_percent)))
        trace.registrar(
            regra="R-CAL-02: saturação por bases",
            entradas={
                "v_alvo": dose_criterio.get("v_alvo"),
                "v_percent": analise.v_percent,
                "ctc_ph7": analise.ctc_ph7,
            },
            saida={"nc_t_ha": nc},
            fonte="Manual 2016, Tabela 5.6, p. 83 e Tabela 5.7, p. 86",
        )
        return nc

    tabela_smp = _obter_tabela_smp()
    linha = _resolver_linha_tabela_smp(tabela_smp.get("tabela", []), analise.indice_smp, ph_alvo)
    if linha is None:
        raise ValueError(
            f"Índice SMP '{analise.indice_smp}' fora da faixa da tabela de calagem "
            f"(faixa esperada: {tabela_smp.get('limites', {}).get('smp_minimo')} a {tabela_smp.get('limites', {}).get('smp_maximo')})."
        )

    if analise.indice_smp > 6.3:
        nc_tabela = _calcular_ajuste_baixo_poder_tampao(analise, ph_alvo)
        trace.registrar(
            regra="R-CAL-03: baixo poder tampão -> equação polinomial",
            entradas={
                "indice_smp": analise.indice_smp,
                "ph_alvo": ph_alvo,
                "mo": analise.mo,
                "al": analise.al,
            },
            saida={"nc_t_ha": nc_tabela},
            fonte="Manual 2016, p. 71-72; dados/comum/calagem_smp.json, ajustes.baixo_poder_tampao",
        )
    else:
        campo = {
            5.5: "nc_ph_5_5",
            6.0: "nc_ph_6_0",
            6.5: "nc_ph_6_5",
        }.get(ph_alvo)
        if campo is None:
            raise ValueError(f"pH alvo não suportado para Tabela 5.2: '{ph_alvo}'.")

        nc_tabela = float(linha.get(campo, 0.0))
        trace.registrar(
            regra="R-CAL-04: consulta à Tabela 5.2 do SMP",
            entradas={
                "indice_smp": analise.indice_smp,
                "ph_alvo": ph_alvo,
                "linha_tabela": linha.get("indice_smp"),
            },
            saida={"nc_t_ha": nc_tabela},
            fonte="Manual 2016, Tabela 5.2, p. 70",
        )

    nc_ajustado_fator = nc_tabela * fator
    trace.registrar(
        regra="R-CAL-05: ajuste pelo fator do critério de cultura",
        entradas={
            "nc_tabela": nc_tabela,
            "fator": fator,
            "tipo_dose": tipo_dose,
        },
        saida={"nc_t_ha": nc_ajustado_fator},
        fonte=f"Manual 2016, {criterio.get('fonte')}",
    )

    prnt = float(contexto.prnt)
    if prnt <= 0:
        raise ValueError("'contexto.prnt' deve ser maior que zero para correção pela PRNT.")
    nc_correto_prnt = (nc_ajustado_fator * 100.0) / prnt
    trace.registrar(
        regra="R-CAL-06: correção pelo corretivo real (PRNT)",
        entradas={"nc_t_ha_ajustado": nc_ajustado_fator, "prnt": prnt},
        saida={"nc_t_ha": nc_correto_prnt},
        fonte="Manual 2016, Cap. 8, p. 298; dados/comum/calagem_smp.json, ajustes.prnt",
    )

    if contexto.profundidade_cm >= 30:
        nc_prof = nc_correto_prnt * 1.5
        trace.registrar(
            regra="R-CAL-07: profundidade 30 cm -> fator 1,5",
            entradas={"profundidade_cm": contexto.profundidade_cm, "nc_t_ha": nc_correto_prnt},
            saida={"nc_t_ha": nc_prof},
            fonte="Manual 2016, Cap. 8, p. 298; dados/comum/calagem_smp.json, ajustes.profundidade_30cm",
        )
        nc_final = nc_prof
    else:
        nc_final = nc_correto_prnt

    if criterio.get("modo_aplicacao") == "superficial":
        limite = float(dose_criterio.get("limite_t_ha", 5.0))
        if nc_final > limite:
            trace.registrar(
                regra="R-CAL-08: limite de aplicação superficial",
                entradas={"nc_t_ha": nc_final, "limite_t_ha": limite},
                saida={"nc_t_ha": limite},
                fonte="Manual 2016, Tabela 5.3, p. 75; plantio direto consolidado, limite de 5 t/ha",
            )
            nc_final = limite

    trace.registrar(
        regra="R-CAL-09: dose final de calcário",
        entradas={
            "cultura_id": cultura_id,
            "sistema_manejo": contexto.sistema_manejo,
            "condicao_area": contexto.condicao_area,
        },
        saida={"nc_t_ha": nc_final},
        fonte="Manual 2016 e base de conhecimento do SIRAS",
    )

    return nc_final


__all__ = ["calcular_necessidade_calagem"]
