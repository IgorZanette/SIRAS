"""
Preenchimento de exemplo do formulário, por cultura.

Serve à demonstração e ao teste de usabilidade: transcrever dezessete campos antes de
ver qualquer resultado é barreira alta para quem só quer conhecer o sistema, e no
roteiro do SUS essa transcrição consome o tempo da tarefa sem medir nada.

Onde os números vêm:

- a ANÁLISE DE SOLO é um laudo de demonstração, não do Manual. São ENTRADAS plausíveis
  de um laboratório do RS, escolhidas para o exemplo exercitar o sistema: pH que dispara
  a calagem, fósforo baixo, potássio alto, argila de classe intermediária. Nenhuma delas
  é valor de recomendação, e nenhuma sai de tabela;
- a PRODUTIVIDADE sai da própria base, sempre que ela a transcreve: o rendimento de
  referência da cultura em grãos, ou o piso da primeira faixa de produtividade nos
  grupos que a publicam. Inventar uma produtividade típica por cultura seria afirmação
  agronômica, e essa não é decisão da interface;
- as VARIÁVEIS CONDICIONAIS recebem a primeira opção declarada na base.

O exemplo é ponto de partida editável, e não um caso de validação: os casos com oráculo
vivem em testes/casos/ e continuam sendo o que mede a concordância do sistema.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from siras.dominio.nomes import buscar_por_nome

#: Três laudos de laboratório de DEMONSTRAÇÃO. São entradas plausíveis de um laboratório
#: do RS, e nenhum número aqui sai de tabela do Manual nem vale como referência
#: agronômica — são valores de entrada, do tipo que o técnico transcreve.
#:
#: Os três existem porque exercitam caminhos diferentes do motor, e é isso que faz um
#: exemplo valer mais que um formulário preenchido ao acaso:
#:
#: - ARGILOSO ácido dispara a calagem e cai nas classes baixas de P;
#: - ARENOSO tem CTC baixa, o que muda a faixa de interpretação do potássio e a leitura
#:   da aptidão, sem disparar a mesma dose de calcário;
#: - CORRIGIDO tem pH acima do gatilho: mostra o laudo em que a calagem NÃO é indicada,
#:   que é o caminho que um exemplo só nunca exercita.
#:
#: A camada de subsuperfície fica de fora de propósito: só um critério de calagem a lê
#: (plantio direto consolidado com restrições), e preenchê-la sempre sugeriria que toda
#: análise precisa de duas amostragens.
CENARIOS = (
    {
        "id": "argiloso",
        "nome": "Solo argiloso ácido",
        "resumo": "Dispara a calagem e cai nas classes baixas de fósforo.",
        "valores": {
            "ph_agua": "5,0", "indice_smp": "5,3", "al": "1,4", "ca": "2,6", "mg": "1,1",
            "v_percent": "42", "saturacao_al": "", "argila": "58", "mo": "3,4",
            "p": "6,2", "k": "88", "ctc_ph7": "11,2", "prnt": "75",
        },
    },
    {
        "id": "arenoso",
        "nome": "Solo arenoso",
        "resumo": "CTC baixa muda a faixa de interpretação do potássio.",
        "valores": {
            "ph_agua": "5,4", "indice_smp": "5,9", "al": "0,5", "ca": "1,6", "mg": "0,7",
            "v_percent": "52", "saturacao_al": "", "argila": "14", "mo": "1,8",
            "p": "12,5", "k": "44", "ctc_ph7": "5,6", "prnt": "75",
        },
    },
    {
        "id": "corrigido",
        "nome": "Solo já corrigido",
        "resumo": "pH acima do gatilho: mostra o laudo sem indicação de calagem.",
        "valores": {
            "ph_agua": "6,2", "indice_smp": "6,4", "al": "0,1", "ca": "4,2", "mg": "1,8",
            "v_percent": "72", "saturacao_al": "", "argila": "38", "mo": "3,1",
            "p": "24,0", "k": "140", "ctc_ph7": "9,8", "prnt": "100",
        },
    },
)

_POR_ID = {cenario["id"]: cenario for cenario in CENARIOS}

#: Mantido para quem chama sem escolher: o primeiro cenário.
ANALISE_DE_DEMONSTRACAO: Dict[str, str] = CENARIOS[0]["valores"]


def _numero_para_campo(valor: Any) -> str:
    if valor is None:
        return ""
    texto = f"{float(valor):g}"
    return texto.replace(".", ",")


def _primeira_faixa_de_produtividade(no: Any) -> Optional[float]:
    """Piso da primeira faixa de produtividade transcrita, varrendo a cultura.

    A cana e algumas frutíferas publicam a dose por faixa de produtividade em vez de por
    um rendimento de referência. Usar o piso da primeira faixa mantém o exemplo dentro
    do que o Manual tabula, sem escolher um valor por conta própria.
    """
    if isinstance(no, dict):
        faixas = no.get("faixas_produtividade")
        if isinstance(faixas, list) and faixas:
            primeira = faixas[0]
            limite = primeira.get("ate") if primeira.get("de") is None else primeira.get("de")
            if limite is not None:
                return float(limite)
        for valor in no.values():
            achado = _primeira_faixa_de_produtividade(valor)
            if achado is not None:
                return achado
    elif isinstance(no, list):
        for item in no:
            achado = _primeira_faixa_de_produtividade(item)
            if achado is not None:
                return achado
    return None


def _produtividade_transcrita(
    cultura_id: str, grupo: str, dados: Dict[str, Any], entradas: Optional[Dict[str, Any]]
) -> Optional[float]:
    if grupo == "graos":
        from siras.conhecimento.carregador import carregar_dados_graos

        manutencao = (
            carregar_dados_graos()["adubacao_pk"]["manutencao_por_cultura"]["culturas"]
            .get(cultura_id, {})
        )
        return manutencao.get("rendimento_referencia_t_ha")

    entrada = buscar_por_nome(entradas, cultura_id) if entradas else None
    if not entrada:
        return None
    ajuste = entrada.get("ajuste_expectativa_rendimento")
    if isinstance(ajuste, dict) and ajuste.get("acima_de_t_ha") is not None:
        return float(ajuste["acima_de_t_ha"])
    return _primeira_faixa_de_produtividade(entrada)


def montar(
    cultura_id: str,
    grupo: str,
    dados: Dict[str, Any],
    manejos: List[Any],
    variaveis: List[Dict[str, Any]],
    entradas_do_grupo: Optional[Dict[str, Any]] = None,
    cenario: Optional[str] = None,
) -> Dict[str, str]:
    """Valores de exemplo para o formulário desta cultura, no cenário pedido."""
    escolhido = _POR_ID.get(cenario or "", CENARIOS[0])
    valores: Dict[str, str] = dict(escolhido["valores"])
    valores["cultura_id"] = cultura_id
    valores["profundidade_incorporacao_cm"] = "20"
    if grupo == "graos":
        valores["cultivo"] = "1"

    if manejos:
        valores["criterio_id"] = manejos[0][0]

    # Sete culturas de grãos dosam N por matéria orgânica CRUZADA com a antecedente, e
    # sem ela o motor recusa. A lista de antecedentes válidas é declarada na própria
    # cultura, então o exemplo pega a primeira em vez de escolher uma por fora.
    if grupo == "graos":
        from siras.conhecimento.carregador import carregar_dados_graos

        entrada_n = carregar_dados_graos()["adubacao_n"]["culturas"].get(cultura_id, {})
        antecedentes = entrada_n.get("antecedentes") or ()
        if antecedentes:
            valores["antecedente"] = antecedentes[0]

    produtividade = _produtividade_transcrita(cultura_id, grupo, dados, entradas_do_grupo)
    if produtividade is not None:
        valores["expectativa_rendimento"] = _numero_para_campo(produtividade)

    for variavel in variaveis:
        campo = variavel["campo"]
        if variavel["tipo"] == "escolha" and variavel.get("valores"):
            valores[campo] = variavel["valores"][0][0]
        elif variavel["tipo"] == "numero" and produtividade is not None:
            # ano do pomar é o único numérico que não é produtividade.
            valores[campo] = "3" if campo == "ano" else _numero_para_campo(produtividade)

    return valores


__all__ = ["ANALISE_DE_DEMONSTRACAO", "CENARIOS", "montar"]
