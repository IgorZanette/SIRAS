"""
As tabelas do Manual como o SIRAS as transcreveu, prontas para exibição.

Existe por dois motivos práticos. O primeiro é conferência: o técnico que desconfiar de
uma dose pode abrir a tabela que a produziu sem sair do sistema e sem abrir o PDF de 376
páginas. O segundo é didático — o mesmo que justifica a leitura ao vivo (PLANO-FRONTEND
§9.3): para o estudante de agronomia, ver a estrutura das tabelas converte a ferramenta
de caixa-preta em material de estudo.

Nada aqui calcula nem interpreta. Cada função converte um arquivo de `dados/comum/` num
modelo genérico de tabela — cabeçalho, linhas e a fonte transcrita — e o template
renderiza qualquer um deles. Nenhum valor é reescrito, arredondado ou completado: o que
aparece na tela é o que está no JSON, e o que está no JSON é transcrição conferida do
Manual.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from siras.relatorio.apresentacao import formatar_enxuto, formatar_numero


@dataclass(frozen=True)
class Tabela:
    """Uma tabela pronta para o template: cabeçalho, linhas e de onde ela veio."""

    titulo: str
    fonte: str
    colunas: List[str]
    linhas: List[List[str]]
    descricao: str = ""
    notas: List[str] = field(default_factory=list)
    #: destacado acima da tabela quando a leitura depende de saber disto
    aviso: Optional[str] = None


def _faixa_legivel(faixa: Dict[str, Any], unidade: str = "") -> str:
    """'de'/'ate' viram a notação de intervalo que o Manual usa.

    A convenção é a de classificar_faixa() em motor/adubacao.py — limite inferior aberto,
    superior fechado —, e está escrita assim para que quem conferir a tabela veja a mesma
    regra que o motor aplica, e não uma aproximação dela.
    """
    de, ate = faixa.get("de"), faixa.get("ate")
    sufixo = f" {unidade}" if unidade else ""
    if de is None and ate is None:
        return "—"
    if de is None:
        return f"≤ {formatar_enxuto(ate)}{sufixo}"
    if ate is None:
        return f"> {formatar_enxuto(de)}{sufixo}"
    return f"> {formatar_enxuto(de)} a {formatar_enxuto(ate)}{sufixo}"


def _rotulo_de_classe(classe: str) -> str:
    return classe.replace("_", " ").capitalize()


def tabela_smp(dados: Dict[str, Any]) -> Tabela:
    bloco = dados["calagem_smp"]
    linhas = []
    for linha in bloco["tabela"]:
        indice = formatar_numero(linha["indice_smp"], 1)
        if linha.get("limite_inferior"):
            indice = f"≤ {indice}"
        linhas.append([
            indice,
            formatar_numero(linha["nc_ph_5_5"], 1),
            formatar_numero(linha["nc_ph_6_0"], 1),
            formatar_numero(linha["nc_ph_6_5"], 1),
        ])
    return Tabela(
        titulo="Necessidade de calcário pelo índice SMP",
        fonte=_fonte(bloco),
        descricao=bloco.get("descricao", ""),
        colunas=["Índice SMP", "pH 5,5", "pH 6,0", "pH 6,5"],
        linhas=linhas,
        aviso=(
            f"Doses em {bloco.get('unidade', 't/ha')} de calcário PRNT 100%, para a camada "
            f"de 0–{bloco.get('profundidade_cm', 20)} cm. A dose do corretivo real sai de "
            f"NC × 100 ÷ PRNT."
        ),
        notas=[
            "Índice SMP acima do último valor da tabela não gera necessidade de calcário.",
            "Solos de baixo poder tampão (SMP acima de 6,3) usam as equações com matéria "
            "orgânica e alumínio, e não esta tabela.",
        ],
    )


def tabela_criterios_calagem(dados: Dict[str, Any]) -> Tabela:
    linhas = []
    for criterio in dados["criterios_calagem"]["criterios"]:
        decisao = criterio.get("decisao", {})
        dose = criterio.get("dose", {})
        gatilho = {
            "ph_menor_que": lambda: f"pH < {formatar_enxuto(decisao.get('ph'))}",
            "v_menor_igual": lambda: f"V ≤ {formatar_enxuto(decisao.get('v'))}%",
            "ph_menor_que_e_al": lambda: (
                f"pH < {formatar_enxuto(decisao.get('ph'))} e saturação por Al alta"
            ),
        }.get(decisao.get("tipo"), lambda: decisao.get("tipo", "—"))()

        if dose.get("tipo") == "saturacao_bases":
            alvo = f"V = {formatar_enxuto(dose.get('v_alvo'))}%"
        else:
            alvo = f"pH {formatar_enxuto(dose.get('ph_alvo'))}"

        fator = dose.get("fator")
        linhas.append([
            criterio["id"].replace("_", " "),
            criterio.get("sistema_manejo", "—").replace("_", " "),
            criterio.get("condicao_area", "—"),
            gatilho,
            alvo,
            formatar_enxuto(fator) if fator is not None else "—",
            criterio.get("modo_aplicacao", "—"),
            criterio.get("fonte", "—"),
        ])
    return Tabela(
        titulo="Critérios de calagem por grupo de cultura",
        fonte="Manual 2016, Tabelas 5.3 a 5.7",
        descricao=dados["criterios_calagem"].get("descricao", ""),
        colunas=["Critério", "Manejo", "Condição da área", "Dispara quando",
                 "Alvo", "Fator", "Aplicação", "Fonte"],
        linhas=linhas,
        aviso=(
            "É esta tabela que dispara a calagem, e não o pH de referência da Tabela 5.1. "
            "Os dois divergem com frequência: grãos têm pH de referência 6,0 e só recebem "
            "calcário abaixo de pH 5,5, com a dose calculada para 6,0."
        ),
    )


def tabela_interpretacao_p(dados: Dict[str, Any]) -> Tabela:
    bloco = dados["interpretacao_p"]
    classes = ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]
    linhas = []
    for tabela in bloco["tabelas"]:
        for por_argila in tabela.get("por_classe_argila", []):
            faixas = {f["classe"]: f for f in por_argila["faixas"]}
            linhas.append(
                [tabela["grupo"].replace("_", " "), f"Classe {por_argila['classe_argila']}"]
                + [_faixa_legivel(faixas[c]) if c in faixas else "—" for c in classes]
                + [tabela.get("fonte", "—")]
            )
    return Tabela(
        titulo="Interpretação do teor de fósforo",
        fonte=_fonte(bloco),
        descricao=bloco.get("descricao", ""),
        colunas=["Grupo de exigência", "Classe de argila"]
                + [_rotulo_de_classe(c) for c in classes] + ["Fonte"],
        linhas=linhas,
        aviso=(
            f"Teores em {bloco.get('unidade', 'mg/dm³')}, extrator {bloco.get('metodo', '—')}. "
            "A classe de argila da amostra é quem escolhe a linha."
        ),
    )


def tabela_interpretacao_k(dados: Dict[str, Any]) -> Tabela:
    bloco = dados["interpretacao_k"]
    classes = ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]
    ctc = {f["faixa"]: _faixa_legivel(f) for f in bloco.get("faixas_ctc", [])}
    linhas = []
    for tabela in bloco["tabelas"]:
        for por_ctc in tabela.get("por_faixa_ctc", []):
            faixas = {f["classe"]: f for f in por_ctc["faixas"]}
            rotulo_ctc = f"{por_ctc['faixa_ctc']} ({ctc.get(por_ctc['faixa_ctc'], '—')})"
            linhas.append(
                [tabela["grupo"].replace("_", " "), rotulo_ctc]
                + [_faixa_legivel(faixas[c]) if c in faixas else "—" for c in classes]
                + [tabela.get("fonte", "—")]
            )
    return Tabela(
        titulo="Interpretação do teor de potássio",
        fonte=_fonte(bloco),
        descricao=bloco.get("descricao", ""),
        colunas=["Grupo de exigência", "Faixa de CTC a pH 7,0"]
                + [_rotulo_de_classe(c) for c in classes] + ["Fonte"],
        linhas=linhas,
        aviso=(
            f"Teores em {bloco.get('unidade', 'mg/dm³')}, extrator {bloco.get('metodo', '—')}. "
            "Diferente do fósforo, quem escolhe a linha é a CTC a pH 7,0, e não a argila."
        ),
    )


def tabela_interpretacao_geral(dados: Dict[str, Any]) -> Tabela:
    bloco = dados["interpretacao_geral"]
    linhas = []
    for atributo in bloco["atributos"]:
        for faixa in atributo["faixas"]:
            linhas.append([
                atributo["atributo"].replace("_", " ").capitalize(),
                _rotulo_de_classe(str(faixa["classe"])),
                _faixa_legivel(faixa, atributo.get("unidade", "")),
                atributo.get("fonte", "—"),
            ])
    return Tabela(
        titulo="Classes de interpretação dos demais atributos",
        fonte=_fonte(bloco),
        descricao=bloco.get("descricao", ""),
        colunas=["Atributo", "Classe", "Faixa", "Fonte"],
        linhas=linhas,
        aviso=(
            "Argila, matéria orgânica, CTC, cálcio, magnésio e micronutrientes. São escalas "
            "próprias, com três ou quatro classes — não a de cinco classes da "
            "disponibilidade de fósforo e potássio."
        ),
    )


def _fonte(bloco: Dict[str, Any]) -> str:
    fonte = bloco.get("fonte")
    if isinstance(fonte, str):
        return fonte
    if not isinstance(fonte, dict):
        return "—"
    tabelas = fonte.get("tabelas") or []
    paginas = fonte.get("paginas") or []
    partes = ["Manual 2016"]
    if tabelas:
        partes.append("Tab. " + "; ".join(str(t) for t in tabelas))
    if paginas:
        menor, maior = min(paginas), max(paginas)
        partes.append(f"p. {menor}" if menor == maior else f"p. {menor}-{maior}")
    return ", ".join(partes)


#: (id na rota, título curto do índice, ícone, o que a tabela responde, construtor)
CATALOGO: List[Dict[str, Any]] = [
    {
        "id": "calagem-smp",
        "titulo": "Necessidade de calcário (índice SMP)",
        "icone": "calagem",
        "resumo": "Quanto de calcário para levar o pH a 5,5, 6,0 ou 6,5.",
        "construtor": tabela_smp,
    },
    {
        "id": "criterios-calagem",
        "titulo": "Critérios de calagem por grupo",
        "icone": "alvo",
        "resumo": "Quando a calagem é indicada, para qual pH e com que fator.",
        "construtor": tabela_criterios_calagem,
    },
    {
        "id": "interpretacao-p",
        "titulo": "Interpretação do fósforo",
        "icone": "analise",
        "resumo": "Em que classe cai o teor de P, por classe de argila.",
        "construtor": tabela_interpretacao_p,
    },
    {
        "id": "interpretacao-k",
        "titulo": "Interpretação do potássio",
        "icone": "analise",
        "resumo": "Em que classe cai o teor de K, por faixa de CTC.",
        "construtor": tabela_interpretacao_k,
    },
    {
        "id": "interpretacao-geral",
        "titulo": "Demais atributos",
        "icone": "perfil",
        "resumo": "Argila, matéria orgânica, CTC, cálcio, magnésio e micronutrientes.",
        "construtor": tabela_interpretacao_geral,
    },
]

_POR_ID: Dict[str, Dict[str, Any]] = {item["id"]: item for item in CATALOGO}


def construir(identificador: str, dados: Dict[str, Any]) -> Optional[Tabela]:
    """A tabela pedida, ou None quando o identificador não existe."""
    item = _POR_ID.get(identificador)
    return item["construtor"](dados) if item else None


__all__ = ["CATALOGO", "Tabela", "construir"]
