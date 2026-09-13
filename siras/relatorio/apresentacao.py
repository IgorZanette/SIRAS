"""
Camada de apresentação: traduz o Laudo do motor para o vocabulário da tela.

Existe para que os templates não contenham lógica. Tudo que é decisão de exibição —
vírgula decimal, 'muito_baixo' virando "Muito baixo", a posição do marcador na régua,
o texto que explica por que a calagem não foi indicada — mora aqui, num módulo que os
testes alcançam sem subir servidor.

Fronteira que este módulo NÃO cruza: não calcula, não classifica e não arredonda dose.
Classe de teor, dose e grau de limitação chegam prontos do motor. O que se faz aqui é
escolher palavras e posições para números que já existem.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

from siras.dominio.laudo import Laudo

#: Ordem canônica das cinco classes de disponibilidade do Manual. É a ordem da régua.
CLASSES_TEOR = ("muito_baixo", "baixo", "medio", "alto", "muito_alto")

_SIGLA_POR_CLASSE = {
    "muito_baixo": "mb", "baixo": "b", "medio": "m", "alto": "a", "muito_alto": "ma",
}
_ROTULO_POR_CLASSE = {
    "muito_baixo": "Muito baixo", "baixo": "Baixo", "medio": "Médio",
    "alto": "Alto", "muito_alto": "Muito alto",
}
_ROTULO_POR_CLASSE_APTIDAO = {
    "APTA": "Apta",
    "APTA_COM_RESTRICOES": "Apta com restrições",
    "RESTRITA": "Aptidão restrita",
    "INAPTA_SEM_CORRECAO": "Inapta sem correção",
    "INDETERMINADA": "Indeterminada",
}
#: Os graus do CCAE, que são os de Ramalho Filho e Beek. Só muda a caixa das letras —
#: traduzir para outra escala de palavras romperia a rastreabilidade ao caderno.
_ROTULO_POR_GRAU = {
    "NULO": "Nula", "LIGEIRO": "Ligeira", "MODERADO": "Moderada",
    "FORTE": "Forte", "MUITO_FORTE": "Muito forte",
}
#: Cor e ícone do selo de aptidão. Aqui o sinal de diagnóstico carrega significado — é
#: a gravidade da limitação —, que é a única razão pela qual o plano (§2.1) admite usar
#: coral, laranja e âmbar. O rótulo textual vai sempre junto (WCAG 1.4.1).
_SELO_POR_CLASSE_APTIDAO = {
    "APTA": ("var(--v-600)", "confere"),
    "APTA_COM_RESTRICOES": ("var(--sig-ambar)", "broto"),
    "RESTRITA": ("var(--sig-laranja)", "alerta"),
    "INAPTA_SEM_CORRECAO": ("var(--sig-coral)", "alerta"),
    "INDETERMINADA": ("var(--n-500)", "info"),
}
_NOME_POR_FATOR = {
    "composicao_aptidao": "Composição da classe",
    "aptidao_indeterminada": "Aptidão indeterminada",
    "F1_acidez": "Acidez", "F2_fosforo": "Fósforo", "F3_potassio": "Potássio",
    "F4_ca_mg": "Cálcio e magnésio", "F5_ctc": "CTC a pH 7,0",
    "F6_mo": "Matéria orgânica", "F7_textura": "Textura",
}
#: Motivos gerados pelo próprio motor (motor/calagem.py). Os motivos que vêm da base
#: trazem o campo 'texto' transcrito do Manual e são usados diretamente.
_TEXTO_POR_MOTIVO = {
    "ph_acima_do_disparo": "o pH está acima do valor que dispara a calagem para esta cultura",
    "v_acima_do_alvo": "a saturação por bases já está acima do alvo do critério",
    "condicao_ph_e_al_nao_satisfeita": "a condição de pH e alumínio do critério não foi satisfeita",
    "smp_acima_da_tabela": "o índice SMP está acima da faixa da Tabela 5.2",
}
_ROTULO_POR_FAIXA_MO = {
    "mo_ate_2_5": "MO até 2,5%",
    "mo_2_6_a_5_0": "MO de 2,6 a 5,0%",
    "mo_acima_5_0": "MO acima de 5,0%",
}


def formatar_numero(valor: Optional[float], casas: int = 1) -> str:
    """Formata um número no padrão brasileiro: vírgula decimal, sem separador de milhar.

    Sem separador de milhar de propósito: as grandezas do laudo não passam de centenas
    (kg/ha) e o ponto de milhar em '1.200' é lido como decimal por quem transcreve de um
    laudo de laboratório.
    """
    if valor is None:
        return "—"
    return f"{valor:.{casas}f}".replace(".", ",")


def formatar_dose(dose: Any, casas: int = 0) -> str:
    """Formata uma dose que pode não ser um único número.

    O Manual nem sempre publica um valor: na classe Muito alto em 2º cultivo dá um teto
    ("<= manutenção"), e a videira fica sem correspondência declarada para o K. O motor
    preserva essas formas (ADR 0004); achatá-las aqui num número inventaria precisão.
    """
    if dose is None:
        return "—"
    if isinstance(dose, dict):
        if dose.get("qualificador") == "ate":
            return f"até {formatar_numero(dose['valor'], casas)}"
        if "min" in dose and "max" in dose:
            return f"{formatar_numero(dose['min'], casas)} a {formatar_numero(dose['max'], casas)}"
        if "pendente" in dose or dose.get("valor") is None:
            return "não definido pelo Manual"
        return formatar_numero(dose.get("valor"), casas)
    return formatar_numero(dose, casas)


def formatar_enxuto(valor: Optional[float]) -> str:
    """Sem casa decimal quando o número é inteiro. Evita o "PRNT 100,0%" do laudo."""
    if valor is None:
        return "—"
    return formatar_numero(valor, 0 if float(valor).is_integer() else 1)


def humanizar_evidencia(texto: str) -> str:
    """Ajusta a pontuação das evidências que o motor monta para leitura em documento.

    O motor interpola floats de Python, então a mesma frase sai com "pH 5.1 < 5,5": ponto
    do repr e vírgula do limiar transcrito. Num laudo que vai anexado a projeto de crédito
    isso lê como erro. A troca é só de separador decimal e de seta — nenhuma evidência é
    reescrita, nenhum número muda.

    A correção de raiz seria o motor formatar os números ao montar a evidência; isso
    mexeria em strings que a verificação de conformidade do CCAE inspeciona, e é decisão
    do autor, não da camada de apresentação.
    """
    return re.sub(r"(\d)\.(\d)", r"\1,\2", texto).replace("->", "→")


def indice_da_classe(classe: str) -> int:
    return CLASSES_TEOR.index(classe)


def sigla_da_classe(classe: str) -> str:
    return _SIGLA_POR_CLASSE[classe]


def rotulo_da_classe(classe: str) -> str:
    return _ROTULO_POR_CLASSE[classe]


def posicao_na_regua(
    valor: float, faixas: Sequence[Dict[str, Any]], classe: str
) -> Optional[float]:
    """Posição do marcador, em % da largura total da régua, ou None quando indefinida.

    É esta função que faz a régua responder à pergunta que a ficha não responde: quão
    perto da borda da classe o teor está. Um P de 11,9 mg/dm³ e um de 6,2 são ambos
    "Baixo" e pedem decisões diferentes.

    Duas faixas não têm largura finita, e cada uma recebe um tratamento diferente:

    - a primeira (`de` nulo) é fechada embaixo pelo zero — teor negativo não existe e
      AnaliseSolo já o rejeita, então o piso é físico, não arbitrado;
    - a última (`ate` nulo) é aberta para cima, e não há como situar um valor dentro de
      uma faixa sem fim. Retorna None: a régua mostra a classe acesa e não afirma
      posição nenhuma, em vez de fingir uma.
    """
    faixa = next((f for f in faixas if f["classe"] == classe), None)
    if faixa is None:
        return None

    de = faixa["de"] if faixa["de"] is not None else 0.0
    ate = faixa["ate"]
    if ate is None or ate <= de:
        return None

    fracao = min(max((valor - de) / (ate - de), 0.0), 1.0)
    largura_da_faixa = 100.0 / len(CLASSES_TEOR)
    return round((indice_da_classe(classe) + fracao) * largura_da_faixa, 2)


def nome_de_exibicao(cultura_id: str, dados: Dict[str, Any]) -> str:
    """Nome da cultura como o Manual a escreve (Anexo 2, campo nome_exibicao).

    Cultura ausente do catálogo cai no identificador legibilizado. Hoje isso alcança só
    'arroz_de_sequeiro', que está em mapa_culturas.json e não no Anexo 2 — é lacuna de
    transcrição, registrada e não preenchida aqui.
    """
    entrada = dados["catalogo_anexo2"]["culturas"].get(cultura_id)
    if entrada and entrada.get("nome_exibicao"):
        return entrada["nome_exibicao"]
    return cultura_id.replace("_", " ").capitalize()


def _observacao_da_calagem(laudo: Laudo) -> str:
    criterio = laudo.calagem.criterio
    if laudo.calagem.nc_t_ha == 0.0:
        excecao = criterio.get("decisao", {}).get("nao_aplicar_se", {})
        if excecao.get("motivo") == laudo.calagem.motivo and excecao.get("texto"):
            return f"Calagem não indicada: {excecao['texto']} ({excecao.get('fonte', '')})."
        return f"Calagem não indicada — {_TEXTO_POR_MOTIVO.get(laudo.calagem.motivo, laudo.calagem.motivo)}."

    dose_cfg = criterio.get("dose", {})
    camada = criterio.get("amostragem_cm")
    partes = []
    # O PRNT informado precisa aparecer junto da dose: motor/calagem.py ja converteu
    # (NC x 100 / PRNT), entao o numero exibido e do CORRETIVO REAL, nao de PRNT 100%.
    # Rotular o cartao como "Calcario PRNT 100%" dizia o contrario e induzia o tecnico a
    # converter de novo.
    partes.append(f"Dose do corretivo com PRNT {formatar_enxuto(laudo.contexto.prnt)}%")
    if dose_cfg.get("ph_alvo"):
        partes.append(f"para elevar o pH a {formatar_numero(dose_cfg['ph_alvo'])}")
    if camada:
        partes.append(f"camada de {camada[0]}–{camada[1]} cm")
    if criterio.get("modo_aplicacao") == "superficial":
        partes.append("aplicação em superfície")
    elif criterio.get("modo_aplicacao") == "incorporado":
        partes.append("incorporar")
    texto = ", ".join(partes) + "."
    if criterio.get("notas"):
        texto += " " + " ".join(f"{nota}." for nota in criterio["notas"])
    return texto


def _observacao_do_nitrogenio(laudo: Laudo) -> str:
    if laudo.adubacao.motivo_n:
        if laudo.adubacao.motivo_n == "fixacao_biologica_de_nitrogenio":
            return "Cultura não recebe adubação nitrogenada: fixação biológica de nitrogênio."
        return f"Sem dose de nitrogênio: {laudo.adubacao.motivo_n.replace('_', ' ')}."
    faixa = _ROTULO_POR_FAIXA_MO.get(laudo.adubacao.faixa_mo, laudo.adubacao.faixa_mo)
    return f"Dose definida pela faixa de matéria orgânica da amostra ({faixa})."


def _observacao_da_classe(nutriente: str, classe: Optional[str]) -> str:
    """Nem toda recomendação passa pela classe de teor: a frutífera em crescimento dosa
    por matéria orgânica e ano após o plantio. Dizer isso é melhor que omitir a linha."""
    if classe is None:
        return (
            f"Dose publicada pelo Manual para esta fase sem passar pela classe de teor de "
            f"{nutriente} no solo."
        )
    return f"Disponibilidade de {nutriente} no solo classificada como “{rotulo_da_classe(classe)}”."


def _veredito(laudo: Laudo) -> List[Dict[str, Any]]:
    """Os quatro números que o usuário veio buscar.

    O calcário recebe o corpo tipográfico maior porque é a decisão de maior impacto
    financeiro e de prazo mais longo.

    Só P2O5 e K2O recebem cor: a delas é a cor da CLASSE que determinou a dose, e
    portanto carrega significado. Calcário e N ficam neutros — pintá-los usaria um sinal
    de diagnóstico por motivo estético, que o plano proíbe (§2.1).
    """
    return [
        {
            "nome": "Calcário",
            "valor": formatar_numero(laudo.calagem.nc_t_ha, 1),
            "unidade": "t/ha",
            "observacao": _observacao_da_calagem(laudo),
            "sigla": None,
            "destaque": True,
        },
        {
            "nome": "Nitrogênio (N)",
            "valor": formatar_dose(laudo.adubacao.n),
            "unidade": "kg/ha",
            "observacao": _observacao_do_nitrogenio(laudo),
            "sigla": None,
            "destaque": False,
        },
        {
            "nome": "Fósforo (P<sub>2</sub>O<sub>5</sub>)",
            "valor": formatar_dose(laudo.adubacao.p2o5),
            "unidade": "kg/ha",
            "observacao": _observacao_da_classe("P", laudo.adubacao.classe_p),
            "sigla": sigla_da_classe(laudo.adubacao.classe_p) if laudo.adubacao.classe_p else None,
            "destaque": False,
        },
        {
            "nome": "Potássio (K<sub>2</sub>O)",
            "valor": formatar_dose(laudo.adubacao.k2o),
            "unidade": "kg/ha",
            "observacao": _observacao_da_classe("K", laudo.adubacao.classe_k),
            "sigla": sigla_da_classe(laudo.adubacao.classe_k) if laudo.adubacao.classe_k else None,
            "destaque": False,
        },
    ]


def _teores(laudo: Laudo) -> List[Dict[str, Any]]:
    """P e K com régua. São os dois atributos que o Manual classifica nas cinco classes
    de disponibilidade — esticar a régua de cinco faixas sobre pH ou MO, que têm outras
    escalas, seria inventar uma leitura."""
    derivados = laudo.aptidao_atual.derivados or {}

    # Sem classe não há régua: há fases de adubação que não dosam pela classe de teor
    # (frutífera em crescimento, por exemplo). Omitir a linha é mais honesto do que
    # exibir uma faixa acesa que a recomendação não usou.
    if laudo.adubacao.classe_p is None and laudo.adubacao.classe_k is None:
        return []

    linhas = []
    if laudo.adubacao.classe_p is not None:
        linhas.append(
        {
            "nome": "Fósforo",
            "valor": formatar_numero(laudo.analise.p, 1),
            "unidade": "mg/dm³",
            "classe": laudo.adubacao.classe_p,
            "sigla": sigla_da_classe(laudo.adubacao.classe_p),
            "rotulo": rotulo_da_classe(laudo.adubacao.classe_p),
            "indice": indice_da_classe(laudo.adubacao.classe_p),
            "posicao": posicao_na_regua(laudo.analise.p, laudo.adubacao.faixas_p,
                                        laudo.adubacao.classe_p),
            "faixas": laudo.adubacao.faixas_p,
            "nota": f"Interpretado pela classe de argila {derivados.get('classe_argila', '—')} "
                    f"({formatar_numero(laudo.analise.argila, 0)}%), extrator Mehlich-1.",
        })

    if laudo.adubacao.classe_k is not None:
        linhas.append(
        {
            "nome": "Potássio",
            "valor": formatar_numero(laudo.analise.k, 0),
            "unidade": "mg/dm³",
            "classe": laudo.adubacao.classe_k,
            "sigla": sigla_da_classe(laudo.adubacao.classe_k),
            "rotulo": rotulo_da_classe(laudo.adubacao.classe_k),
            "indice": indice_da_classe(laudo.adubacao.classe_k),
            "posicao": posicao_na_regua(laudo.analise.k, laudo.adubacao.faixas_k,
                                        laudo.adubacao.classe_k),
            "faixas": laudo.adubacao.faixas_k,
            "nota": f"Interpretado pela CTC a pH 7,0 de "
                    f"{formatar_numero(laudo.analise.ctc_ph7, 1)} cmolc/dm³.",
        })

    return linhas


def _aptidao(laudo: Laudo) -> Dict[str, Any]:
    def cenario(resultado) -> Dict[str, Any]:
        cor, icone = _SELO_POR_CLASSE_APTIDAO.get(resultado.classe, ("var(--n-500)", "info"))
        return {
            "classe": resultado.classe,
            "rotulo": _ROTULO_POR_CLASSE_APTIDAO.get(resultado.classe, resultado.classe),
            "cor": cor,
            "icone": icone,
            "fator_determinante": _NOME_POR_FATOR.get(
                resultado.fator_determinante, resultado.fator_determinante
            ),
            "rebaixamento_aplicado": resultado.rebaixamento_aplicado,
            "alertas": list(resultado.alertas),
            "fatores": [
                {
                    "id": fator.id,
                    "nome": _NOME_POR_FATOR.get(fator.id, fator.id),
                    "grau": fator.grau,
                    "rotulo": _ROTULO_POR_GRAU.get(fator.rotulo, fator.rotulo),
                    "evidencia": humanizar_evidencia(fator.evidencia),
                    "fonte": fator.fonte,
                    # 0 a 100% da barra de peso: quatro graus acima de NULO.
                    "peso": round(fator.grau / 4 * 100),
                }
                for fator in resultado.fatores
            ],
        }

    atual, potencial = cenario(laudo.aptidao_atual), cenario(laudo.aptidao_potencial)
    return {
        "atual": atual,
        "potencial": potencial,
        # CCAE §7: a diferença entre os dois é o ganho atribuível à recomendação deste
        # laudo. Quando não há diferença, dizê-lo é tão informativo quanto o contrário.
        "houve_ganho": atual["classe"] != potencial["classe"],
        "versao_criterios": laudo.aptidao_atual.versao_criterios,
    }


def _trilha(laudo: Laudo) -> List[Dict[str, Any]]:
    """A trilha inteira, na ordem em que o motor decidiu, com módulo e fonte.

    Nada é filtrado. O passo de calagem aparece duas vezes porque a aptidão no cenário
    POTENCIAL recalcula a dose para testar a exequibilidade (CCAE §7.2) — esconder a
    segunda passagem seria esconder uma decisão que o sistema realmente tomou.
    """
    def modulo(regra: str) -> str:
        if regra.startswith("R-ADU"):
            return "Adubação"
        if regra.startswith(("F1_", "F2_", "F3_", "F4_", "F5_", "F6_", "F7_")) or "aptidao" in regra:
            return "Aptidão edáfica"
        return "Calagem"

    def rotulo(regra: str) -> str:
        """Etiqueta curta da coluna da esquerda: o identificador da regra, sem a prosa."""
        if regra in _NOME_POR_FATOR:
            return _NOME_POR_FATOR[regra]
        return regra.split(":")[0]

    # A aptidão roda duas vezes, uma por cenário, e a calagem é recalculada dentro do
    # cenário POTENCIAL para testar a exequibilidade (CCAE §7.2). Os passos repetidos
    # citam a MESMA fonte, então listá-los duas vezes não acrescenta rastreabilidade e
    # dobrava o tamanho desta seção — eram duas páginas do laudo impresso.
    #
    # A repetição não some: a coluna 'vezes' registra quantas vezes a regra foi aplicada,
    # e os dois cenários continuam visíveis na seção de aptidão.
    itens: List[Dict[str, Any]] = []
    vistos: Dict[tuple, Dict[str, Any]] = {}
    for passo in laudo.trace:
        chave = (passo.regra, passo.fonte)
        if chave in vistos:
            vistos[chave]["vezes"] += 1
            continue
        # Nos fatores de aptidão a regra É o identificador ('F1_acidez'), e repeti-lo ao
        # lado do rótulo não diz nada a quem confere. A evidência que o fator registrou
        # diz: o valor lido, o limiar e a classe que saiu.
        evidencia = passo.saida.get("evidencia")
        if passo.regra == "composicao_aptidao":
            # Este passo não registra evidência: o que ele decidiu está na saída.
            determinante = _NOME_POR_FATOR.get(
                passo.saida.get("fator_determinante"), passo.saida.get("fator_determinante")
            )
            evidencia = (
                f"classe {_ROTULO_POR_CLASSE_APTIDAO.get(passo.saida.get('classe'), '—')}"
                f", determinada por {determinante}"
            )
        item = {
            "modulo": modulo(passo.regra),
            "rotulo": rotulo(passo.regra),
            "regra": humanizar_evidencia(evidencia) if evidencia else passo.regra,
            "fonte": passo.fonte,
            "entradas": passo.entradas,
            "saida": passo.saida,
            "vezes": 1,
        }
        vistos[chave] = item
        itens.append(item)
    return itens


#: Classes das escalas de três e quatro faixas de interpretacao_geral.json (MO, CTC, Ca,
#: Mg). Reaproveitam as cores da escala diagnóstica, mas não ganham régua: a régua tem
#: cinco estratos porque são as cinco classes de disponibilidade do Manual, e esticá-la
#: sobre outra escala afirmaria uma leitura que o Manual não faz.
_SIGLA_POR_CLASSE_GERAL = {
    "baixo": "b", "medio": "m", "alto": "a",
    "baixa": "b", "media": "m", "alta": "a", "muito_alta": "ma",
}
_ROTULO_POR_CLASSE_GERAL = {
    "baixo": "Baixo", "medio": "Médio", "alto": "Alto",
    "baixa": "Baixa", "media": "Média", "alta": "Alta", "muito_alta": "Muito alta",
}

#: (chave em leitura["gerais"], nome de tela, unidade, casas decimais)
_LINHAS_GERAIS = (
    ("mo", "Matéria orgânica", "%", 1),
    ("ca", "Cálcio trocável", "cmolc/dm³", 1),
    ("mg", "Magnésio trocável", "cmolc/dm³", 1),
    ("ctc_ph7", "CTC a pH 7,0", "cmolc/dm³", 1),
)


def _linha_de_teor(chave, nome, unidade, item, casas, nota) -> Dict[str, Any]:
    """Linha com régua: só para P e K, as duas escalas de cinco classes do Manual."""
    classe = item["classe"]
    return {
        "id": chave,
        "nome": nome,
        "valor": f"{formatar_numero(item['valor'], casas)} {unidade}",
        "sigla": sigla_da_classe(classe),
        "rotulo": rotulo_da_classe(classe),
        "indice": indice_da_classe(classe),
        "posicao": posicao_na_regua(item["valor"], item["faixas"], classe),
        "nota": nota,
    }


def apresentar_leitura(leitura: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Modelo de exibição do painel de leitura ao vivo.

    Recebe o que motor/leitura.py conseguiu interpretar e devolve linhas prontas. O que
    veio vazio não vira linha: o painel mostra o que já é sabido e cala sobre o resto, em
    vez de exibir um traço para cada campo ainda em branco.

    A ordem acompanha a do formulário — acidez e corretivo primeiro, fertilidade depois —
    para que o olho encontre a leitura na mesma sequência em que digitou.
    """
    linhas: List[Dict[str, Any]] = []
    gerais = leitura.get("gerais") or {}

    acidez = leitura.get("acidez")
    if acidez:
        partes = []
        if acidez.get("ph_gatilho") is not None:
            partes.append(
                f"o critério desta cultura indica calagem com pH abaixo de "
                f"{formatar_numero(acidez['ph_gatilho'])}"
            )
        if acidez.get("ph_alvo") is not None:
            partes.append(f"dose calculada para o pH {formatar_numero(acidez['ph_alvo'])}")
        nota = "; ".join(partes)
        if acidez.get("fonte"):
            nota = f"{nota}. {acidez['fonte']}." if nota else f"{acidez['fonte']}."
        linhas.append({
            "id": "acidez",
            "nome": "Acidez",
            "valor": f"pH {formatar_numero(acidez['valor'])}",
            "nota": nota,
        })

    if leitura.get("saturacao_al") is not None:
        linhas.append({
            "id": "saturacao_al",
            "nome": "Saturação por alumínio",
            "valor": f"{formatar_numero(leitura['saturacao_al'], 1)} %",
            "nota": "Calculada pela CTC efetiva quando não informada no laudo.",
        })

    if leitura.get("v_percent") is not None:
        linhas.append({
            "id": "v_percent",
            "nome": "Saturação por bases",
            "valor": f"{formatar_numero(leitura['v_percent'], 1)} %",
            "nota": "Base do critério de calagem das culturas sem pH de referência.",
        })

    calagem = leitura.get("calagem")
    if calagem:
        criterio = calagem.get("criterio", {})
        modo = criterio.get("modo_aplicacao")
        nota = f"Critério {criterio.get('id', '—')}"
        if modo:
            nota += f", aplicação {modo}"
        linhas.append({
            "id": "calagem",
            "nome": "Calcário estimado",
            "valor": f"{formatar_numero(calagem['nc_t_ha'], 1)} t/ha",
            "nota": nota + ".",
            "destaque": True,
        })

    if "mo" in gerais:
        item = gerais["mo"]
        linhas.append({
            "id": "mo",
            "nome": "Matéria orgânica",
            "valor": f"{formatar_numero(item['valor'], 1)} %",
            "sigla": _SIGLA_POR_CLASSE_GERAL.get(item["classe"]),
            "rotulo": _ROTULO_POR_CLASSE_GERAL.get(item["classe"], item["classe"]),
            "nota": "Define a faixa da dose de nitrogênio.",
        })

    if leitura.get("fosforo"):
        item = leitura["fosforo"]
        linhas.append(_linha_de_teor(
            "fosforo", "Fósforo", "mg/dm³", item, 1,
            f"Interpretado pela classe de argila {item['classe_argila']}.",
        ))

    if leitura.get("potassio"):
        item = leitura["potassio"]
        linhas.append(_linha_de_teor(
            "potassio", "Potássio", "mg/dm³", item, 0,
            f"Interpretado pela faixa de CTC {item['faixa_ctc']}.",
        ))

    for chave, nome, unidade, casas in _LINHAS_GERAIS:
        if chave == "mo" or chave not in gerais:
            continue
        item = gerais[chave]
        linhas.append({
            "id": chave,
            "nome": nome,
            "valor": f"{formatar_numero(item['valor'], casas)} {unidade}",
            "sigla": _SIGLA_POR_CLASSE_GERAL.get(item["classe"]),
            "rotulo": _ROTULO_POR_CLASSE_GERAL.get(item["classe"], item["classe"]),
            "nota": None,
        })

    return linhas


_ROTULO_DE_PARCELAMENTO = {
    "n": "Nitrogênio (N)",
    "p": "Fósforo (P₂O₅)",
    "k": "Potássio (K₂O)",
}


def _orientacoes(laudo: Laudo) -> List[Dict[str, Any]]:
    """Como aplicar: parcelamento, observações e restrições, tudo transcrito.

    Depois de "quanto", a pergunta seguinte do técnico é sempre "como" — e o Manual
    responde, com parcelamento por nutriente e restrições por cultura. Essa informação já
    estava na base e o laudo não a mostrava.
    """
    itens: List[Dict[str, Any]] = []
    orientacoes = laudo.adubacao.orientacoes or {}

    parcelamento = orientacoes.get("parcelamento") or {}
    for nutriente in ("n", "p", "k"):
        texto = parcelamento.get(nutriente)
        if texto:
            itens.append({
                "titulo": f"Parcelamento — {_ROTULO_DE_PARCELAMENTO[nutriente]}",
                "texto": texto,
                "tipo": "parcelamento",
            })

    criterio = laudo.calagem.criterio or {}
    for nota in criterio.get("notas", ()):
        itens.append({"titulo": "Calagem", "texto": nota, "tipo": "calagem"})

    if orientacoes.get("nota"):
        itens.append({"titulo": "Nota da cultura", "texto": orientacoes["nota"], "tipo": "nota"})

    for observacao in orientacoes.get("observacoes", ()):
        itens.append({"titulo": "Observação", "texto": observacao, "tipo": "nota"})

    for restricao in orientacoes.get("restricoes", ()):
        if isinstance(restricao, dict):
            nutriente = str(restricao.get("nutriente", "")).capitalize()
            itens.append({
                "titulo": f"Restrição — {nutriente}" if nutriente else "Restrição",
                "texto": restricao.get("observacao") or "",
                "tipo": "restricao",
            })
    return [item for item in itens if item["texto"]]


def apresentar_laudo(laudo: Laudo, dados: Dict[str, Any]) -> Dict[str, Any]:
    """Monta o modelo de exibição do laudo. O template só itera sobre o que sai daqui."""
    return {
        "cultura": nome_de_exibicao(laudo.cultura_id, dados),
        "cultura_id": laudo.cultura_id,
        "grupo": laudo.grupo,
        "contexto": laudo.contexto,
        # PRNT 75 é "75%", PRNT 87,5 é "87,5%": a casa decimal só aparece quando existe.
        "prnt": formatar_enxuto(laudo.contexto.prnt),
        "profundidade": formatar_enxuto(laudo.contexto.profundidade_incorporacao_cm),
        "analise": laudo.analise,
        "veredito": _veredito(laudo),
        "teores": _teores(laudo),
        "aptidao": _aptidao(laudo),
        "trilha": _trilha(laudo),
        "orientacoes": _orientacoes(laudo),
        "criterio_calagem": laudo.calagem.criterio,
    }


__all__ = [
    "CLASSES_TEOR",
    "apresentar_laudo",
    "formatar_dose",
    "formatar_enxuto",
    "formatar_numero",
    "humanizar_evidencia",
    "indice_da_classe",
    "nome_de_exibicao",
    "posicao_na_regua",
    "rotulo_da_classe",
    "sigla_da_classe",
]
