"""
Leitura e validação do formulário de análise de solo.

Separado das rotas de propósito: transformar onze campos de texto em AnaliseSolo e
Contexto é a parte do caminho web que mais erra, e aqui ela é testável sem subir
servidor nem simular requisição.

Nenhum limiar agronômico é definido neste módulo. As faixas aceitáveis são as que
AnaliseSolo e Contexto já validam na construção (faixa física, docs/decisoes/0002 D2);
este módulo apenas coleta o que falta, converte texto em número e traduz a exceção do
domínio para uma frase que diz o que fazer. Inventar aqui um "pH aceitável de 3,5 a 9,0"
criaria um segundo conjunto de limites, divergente do do domínio e sem fonte.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from siras.dominio.analise import AnaliseSolo, Camada, Contexto
from siras.dominio.escopo import no_escopo_de_recomendacao

#: Campos da camada de referência de fertilidade (0-20 cm por padrão).
#: (id, rótulo, unidade em HTML, ajuda, obrigatório, passo, exemplo)
CAMPOS_ACIDEZ: Tuple[Tuple[Any, ...], ...] = (
    ("ph_agua", "pH em água", None, "Relação solo:água 1:1", True, "0.1", "5,2"),
    ("indice_smp", "Índice SMP", None, "Base da dose de calcário (Tabela 5.2)", True, "0.1", "5,4"),
    ("al", "Alumínio trocável", "cmol<sub>c</sub>/dm<sup>3</sup>", None, True, "0.1", "0,8"),
    ("ca", "Cálcio trocável", "cmol<sub>c</sub>/dm<sup>3</sup>", None, True, "0.1", "2,4"),
    ("mg", "Magnésio trocável", "cmol<sub>c</sub>/dm<sup>3</sup>", None, True, "0.1", "1,1"),
    ("v_percent", "Saturação por bases", "%", None, True, "0.1", "48"),
    ("saturacao_al", "Saturação por alumínio", "%",
     "Opcional. Sem ela, o sistema calcula pela CTC efetiva", False, "0.1", "12"),
)

CAMPOS_FERTILIDADE: Tuple[Tuple[Any, ...], ...] = (
    ("argila", "Argila", "%", "Define a classe de interpretação do fósforo", True, "1", "38"),
    ("mo", "Matéria orgânica", "%", "Define a faixa da dose de nitrogênio", True, "0.1", "2,8"),
    ("p", "Fósforo", "mg/dm<sup>3</sup>", "Extrator Mehlich-1", True, "0.1", "11,0"),
    ("k", "Potássio", "mg/dm<sup>3</sup>", "Extrator Mehlich-1", True, "1", "96"),
    ("ctc_ph7", "CTC a pH 7,0", "cmol<sub>c</sub>/dm<sup>3</sup>",
     "Define a faixa de interpretação do potássio", True, "0.1", "9,4"),
)

#: Camada 10-20 cm. Exigida só pelo critério de plantio direto consolidado com
#: restrições, que decide pela subsuperfície (Tab. 5.3, notas 6-7, p. 75).
CAMPOS_SUBSUPERFICIE: Tuple[Tuple[Any, ...], ...] = (
    ("sub_ph_agua", "pH em água (10-20 cm)", None, None, False, "0.1", "4,9"),
    ("sub_indice_smp", "Índice SMP (10-20 cm)", None, None, False, "0.1", "5,2"),
    ("sub_v_percent", "Saturação por bases (10-20 cm)", "%", None, False, "0.1", "38"),
    ("sub_al", "Alumínio trocável (10-20 cm)", "cmol<sub>c</sub>/dm<sup>3</sup>", None, False, "0.1", "1,4"),
    ("sub_ca", "Cálcio trocável (10-20 cm)", "cmol<sub>c</sub>/dm<sup>3</sup>", None, False, "0.1", "1,8"),
    ("sub_mg", "Magnésio trocável (10-20 cm)", "cmol<sub>c</sub>/dm<sup>3</sup>", None, False, "0.1", "0,9"),
    ("sub_k", "Potássio (10-20 cm)", "mg/dm<sup>3</sup>", None, False, "1", "72"),
)

CAMPOS_CONTEXTO: Tuple[Tuple[Any, ...], ...] = (
    ("prnt", "PRNT do corretivo", "%", "Consta na nota fiscal do calcário", True, "0.1", "75"),
    ("expectativa_rendimento", "Expectativa de rendimento", "t/ha",
     "Média das três últimas safras, não a meta", False, "0.1", "3,6"),
)

_TODOS_OS_CAMPOS = CAMPOS_ACIDEZ + CAMPOS_FERTILIDADE + CAMPOS_SUBSUPERFICIE + CAMPOS_CONTEXTO
_ROTULO_POR_CAMPO = {campo[0]: campo[1] for campo in _TODOS_OS_CAMPOS}


@dataclass
class LeituraFormulario:
    """O que o formulário produziu: ou o par (análise, contexto), ou o que impediu."""

    analise: Optional[AnaliseSolo] = None
    contexto: Optional[Contexto] = None
    #: rótulos dos campos obrigatórios em branco
    faltando: List[str] = field(default_factory=list)
    #: frases completas sobre o que está fora de faixa ou não é número
    invalidos: List[str] = field(default_factory=list)
    #: ids dos campos a marcar com .campo--erro
    campos_com_erro: List[str] = field(default_factory=list)
    #: o que veio do formulário, para devolver a tela preenchida
    valores: Dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.analise is not None and self.contexto is not None


def _para_float(texto: str) -> Optional[float]:
    """Converte aceitando vírgula decimal. Um laudo brasileiro imprime '5,4'."""
    try:
        return float(texto.strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def culturas_disponiveis(dados: Dict[str, Any], grupo: str = "graos") -> List[Tuple[str, str]]:
    """(id, nome de exibição) das culturas de um grupo, em ordem alfabética de nome.

    Estar mapeada em mapa_culturas.json não basta: a cultura precisa estar no escopo de
    recomendação da Proposta (§4.2.1). As seis espécies florestais estão mapeadas porque
    o módulo de aptidão precisa resolver o critério de calagem delas, e mesmo assim não
    são oferecidas aqui — ver siras/dominio/escopo.py e docs/decisoes/0006.
    """
    from siras.relatorio.apresentacao import nome_de_exibicao

    ids = [
        cultura_id
        for cultura_id, entrada in dados["mapa_culturas"]["culturas"].items()
        if entrada.get("grupo") == grupo and no_escopo_de_recomendacao(cultura_id)
    ]
    return sorted(
        ((cultura_id, nome_de_exibicao(cultura_id, dados)) for cultura_id in ids),
        key=lambda par: par[1].lower(),
    )


def opcoes_de_manejo(dados: Dict[str, Any], grupo: str = "graos") -> List[Tuple[str, str]]:
    """(criterio_id, rótulo) dos critérios de calagem aplicáveis ao grupo.

    Uma escolha só, em vez de dois campos independentes para sistema de manejo e condição
    da área: cada opção corresponde a exatamente um critério transcrito, então nenhuma
    combinação escolhida na tela pode deixar de resolver. Critérios que as próprias notas
    marcam fora do escopo do SIRAS (arroz irrigado) não entram na lista.
    """
    opcoes = []
    for criterio in dados["criterios_calagem"]["criterios"]:
        if criterio["grupo"] != grupo:
            continue
        if any("fora do escopo" in nota.lower() for nota in criterio.get("notas", [])):
            continue
        manejo = criterio["sistema_manejo"].replace("_", " ").capitalize()
        condicao = criterio["condicao_area"]
        rotulo = manejo if condicao in ("-", "todos os casos") else f"{manejo} — {condicao}"
        opcoes.append((criterio["id"], rotulo))
    return opcoes


def antecedentes_disponiveis(dados_graos: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Antecedentes declarados pelas culturas cujo modelo de N depende delas."""
    vistos: Dict[str, None] = {}
    for entrada in dados_graos["adubacao_n"]["culturas"].values():
        for antecedente in entrada.get("antecedentes", ()):
            vistos.setdefault(antecedente, None)
    return [(a, a.replace("_", " ").capitalize()) for a in vistos]


def culturas_que_exigem_antecedente(dados_graos: Dict[str, Any], dados: Dict[str, Any]) -> List[str]:
    from siras.relatorio.apresentacao import nome_de_exibicao

    return sorted(
        nome_de_exibicao(cultura_id, dados)
        for cultura_id, entrada in dados_graos["adubacao_n"]["culturas"].items()
        if entrada["modelo"] == "mo_x_antecedente"
    )


def _montar_subsuperficie(numeros: Dict[str, Optional[float]]) -> Optional[Camada]:
    informados = {
        chave[4:]: valor for chave, valor in numeros.items()
        if chave.startswith("sub_") and valor is not None
    }
    if not informados:
        return None
    return Camada(de_cm=10, ate_cm=20, **informados)


def ler(
    form: Mapping[str, str], dados: Dict[str, Any], grupo: str = "graos"
) -> LeituraFormulario:
    """Lê o formulário e devolve AnaliseSolo + Contexto, ou o que impediu.

    Coleta TODOS os campos em branco antes de desistir, em vez de parar no primeiro: o
    técnico corrige uma vez, não onze.
    """
    leitura = LeituraFormulario(valores={chave: form.get(chave, "") for chave in form})

    numeros: Dict[str, Optional[float]] = {}
    for campo_id, rotulo, _unidade, _ajuda, obrigatorio, _passo, _exemplo in _TODOS_OS_CAMPOS:
        bruto = (form.get(campo_id) or "").strip()
        if not bruto:
            if obrigatorio:
                leitura.faltando.append(rotulo)
                leitura.campos_com_erro.append(campo_id)
            numeros[campo_id] = None
            continue
        valor = _para_float(bruto)
        if valor is None:
            leitura.invalidos.append(f"{rotulo}: “{bruto}” não é um número")
            leitura.campos_com_erro.append(campo_id)
        numeros[campo_id] = valor

    cultura_id = (form.get("cultura_id") or "").strip()
    validas = {identificador for identificador, _ in culturas_disponiveis(dados, grupo)}
    if not cultura_id:
        leitura.faltando.append("Cultura")
        leitura.campos_com_erro.append("cultura_id")
    elif cultura_id not in validas:
        leitura.invalidos.append(f"Cultura: “{cultura_id}” não está no catálogo de {grupo}")
        leitura.campos_com_erro.append("cultura_id")

    criterio_id = (form.get("criterio_id") or "").strip()
    criterios = {identificador: rotulo for identificador, rotulo in opcoes_de_manejo(dados, grupo)}
    if not criterio_id:
        leitura.faltando.append("Sistema de manejo")
        leitura.campos_com_erro.append("criterio_id")
    elif criterio_id not in criterios:
        leitura.invalidos.append(f"Sistema de manejo: “{criterio_id}” não corresponde a nenhum critério")
        leitura.campos_com_erro.append("criterio_id")

    if leitura.faltando or leitura.invalidos:
        return leitura

    criterio = next(c for c in dados["criterios_calagem"]["criterios"] if c["id"] == criterio_id)

    try:
        leitura.analise = AnaliseSolo(
            ph_agua=numeros["ph_agua"],
            indice_smp=numeros["indice_smp"],
            argila=numeros["argila"],
            mo=numeros["mo"],
            p=numeros["p"],
            k=numeros["k"],
            ctc_ph7=numeros["ctc_ph7"],
            al=numeros["al"],
            ca=numeros["ca"],
            mg=numeros["mg"],
            v_percent=numeros["v_percent"],
            saturacao_al=numeros["saturacao_al"],
            subsuperficie=_montar_subsuperficie(numeros),
        )
    except ValueError as erro:
        # A mensagem vem do próprio domínio e já nomeia o campo e a faixa física.
        leitura.invalidos.append(str(erro))
        return leitura

    try:
        leitura.contexto = Contexto(
            cultura_id=cultura_id,
            sistema_manejo=criterio["sistema_manejo"],
            condicao_area=criterio["condicao_area"],
            prnt=numeros["prnt"],
            profundidade_incorporacao_cm=float(form.get("profundidade_incorporacao_cm") or 20),
            expectativa_rendimento=numeros["expectativa_rendimento"],
            cultivo=int(form.get("cultivo") or 1),
            antecedente=(form.get("antecedente") or "").strip() or None,
        )
    except ValueError as erro:
        leitura.analise = None
        leitura.invalidos.append(str(erro))

    return leitura


__all__ = [
    "CAMPOS_ACIDEZ",
    "CAMPOS_CONTEXTO",
    "CAMPOS_FERTILIDADE",
    "CAMPOS_SUBSUPERFICIE",
    "LeituraFormulario",
    "antecedentes_disponiveis",
    "culturas_disponiveis",
    "culturas_que_exigem_antecedente",
    "ler",
    "opcoes_de_manejo",
]
