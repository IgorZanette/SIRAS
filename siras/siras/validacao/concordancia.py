"""
Concordância entre as saídas do SIRAS e o oráculo calculado à mão pelo autor.

Corresponde à dimensão (i) do protocolo de validação, `trabalho_de_conclusao/validacao/protocolo.md`, e é a fonte da
tabela principal da seção de Resultados.

Um caso é **concordante** quando TODAS as saídas que a referência declara coincidem com
o que o motor produziu — necessidade de calcário e doses de N, P2O5 e K2O. Acertar três
das quatro não é acerto parcial: é discordância. A definição é do protocolo, não deste
módulo, e está aqui só implementada.

**Este módulo é usado pelo script e pelo teste.** `scripts/gera_tabela_concordancia.py`
produz a tabela da monografia, e `testes/unidade/test_casos_validados.py` roda os mesmos
casos na suíte. Fosse código separado, o número publicado viria de um caminho que nenhum
teste exercita — e é justamente o número que sustenta a H1.1.

Intervalo de confiança por **Wilson** (`trabalho_de_conclusao/validacao/protocolo.md`): com n pequeno e proporção
perto de 1, o intervalo normal produz limite superior acima de 1 e limite inferior
negativo, que não querem dizer nada.
"""

from __future__ import annotations

import csv
import json
import math
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from siras.conhecimento.carregador import (
    carregar_dados_comum,
    carregar_dados_erva_mate,
    carregar_dados_frutiferas,
    carregar_dados_graos,
    carregar_dados_hortalicas,
    carregar_dados_outras,
    carregar_dados_tuberculos,
)
from siras.dominio.analise import AnaliseSolo, Camada, Contexto
from siras.motor.adubacao import (
    calcular_adubacao_erva_mate,
    calcular_adubacao_frutiferas,
    calcular_adubacao_hortalicas,
    calcular_adubacao_outras,
    calcular_adubacao_tuberculos,
    calcular_fosforo_potassio,
    calcular_nitrogenio,
)
from siras.motor.calagem import calcular_calagem
from siras.motor.trace import Trace

RAIZ = pathlib.Path(__file__).resolve().parents[2]
CASOS = RAIZ / "testes" / "casos"

#: Critério de calagem de cada caso.
#:
#: Está aqui, e não resolvido por `resolver_criterio_id()`, pela decisão A2 do roadmap: os
#: `condicao_area` dos casos são atalhos que não batem com o texto completo guardado em
#: `criterios_calagem.json`. O que se mede é o CÁLCULO da dose, não a resolução do
#: critério — essa é exercitada pelos testes da camada web.
CRITERIO_POR_CASO = {
    "CAL-01": "graos_convencional",
    "CAL-02": "graos_pd_consolidado",
    "CAL-03": "graos_convencional",
    "CAL-04": "graos_pd_consolidado",
    "CAL-05": "graos_convencional",
    "CAL-06": "graos_convencional",
    "CAL-07": "macieira_oliveira",
    "CAL-08": "erva_mate_e_florestais",
    "CAL-09": "erva_mate_e_florestais",
    "CAL-10": "graos_pd_com_restricoes",
    "CAL-11": "graos_pd_com_restricoes",
    "CAL-12": "cana_e_tabaco",
    "ADU-01": "graos_convencional",
}

#: AnaliseSolo exige o perfil inteiro; os casos de calagem só trazem o que a calagem usa.
#: Os valores neutros abaixo não entram em nenhuma comparação — o que se compara é só o
#: que o campo `referencia` do caso declara.
_CAMPOS_ANALISE_PADRAO = dict(
    ph_agua=7.0, indice_smp=6.0, argila=0.0, mo=0.0, p=0.0, k=0.0, ctc_ph7=0.0,
    al=0.0, ca=0.0, mg=0.0, v_percent=0.0, saturacao_al=None,
)

#: Variáveis condicionais que a função de adubação de cada grupo aceita (ADR 0004).
_EXTRAS_POR_GRUPO = {
    "hortalicas": ("expectativa_rendimento", "fase", "fase_n", "fase_pk"),
    "tuberculos": ("expectativa_rendimento",),
    "outras": ("ciclo", "tipo", "produtividade_t_ha"),
    "frutiferas": ("fase", "ano", "produtividade_estimada", "tipo_uva",
                   "analise_de_tecido", "ano_de_alternancia"),
    "erva_mate": ("fase", "momento", "manejo_galho_grosso", "massa_verde_t_ha"),
}

_ADUBACAO_POR_GRUPO = {
    "hortalicas": (calcular_adubacao_hortalicas, carregar_dados_hortalicas, "dados_hortalicas"),
    "tuberculos": (calcular_adubacao_tuberculos, carregar_dados_tuberculos, "dados_tuberculos"),
    "outras": (calcular_adubacao_outras, carregar_dados_outras, "dados_outras"),
    "frutiferas": (calcular_adubacao_frutiferas, carregar_dados_frutiferas, "dados_frutiferas"),
    "erva_mate": (calcular_adubacao_erva_mate, carregar_dados_erva_mate, "dados_erva_mate"),
}

#: Saídas comparáveis e a casa decimal da política de arredondamento (trabalho_de_conclusao/validacao/protocolo.md):
#: calcário com uma casa em t/ha, nutrientes inteiros em kg/ha.
_CASAS = {"nc_t_ha": 1, "n": 0, "p2o5": 0, "k2o": 0}


class ErroConcordancia(Exception):
    """Caso malformado, ou grupo de cultura que este apurador ainda não despacha."""


@dataclass
class Divergencia:
    campo: str
    esperado: Any
    obtido: Any


@dataclass
class ResultadoDoCaso:
    id: str
    descricao: str
    grupo: str
    cultura: str
    concordante: bool
    divergencias: List[Divergencia] = field(default_factory=list)
    #: passos do Trace, para a análise individual que o protocolo exige dos discordantes
    trace: List[str] = field(default_factory=list)
    erro: Optional[str] = None


@dataclass
class Apuracao:
    resultados: List[ResultadoDoCaso]

    @property
    def total(self) -> int:
        return len(self.resultados)

    @property
    def concordantes(self) -> int:
        return sum(1 for r in self.resultados if r.concordante)

    @property
    def discordantes(self) -> List[ResultadoDoCaso]:
        return [r for r in self.resultados if not r.concordante]

    def taxa(self) -> Optional[float]:
        return self.concordantes / self.total if self.total else None

    def intervalo(self) -> Optional[Tuple[float, float]]:
        return wilson(self.concordantes, self.total)

    def por_grupo(self) -> Dict[str, "Apuracao"]:
        grupos: Dict[str, List[ResultadoDoCaso]] = {}
        for r in self.resultados:
            grupos.setdefault(r.grupo, []).append(r)
        return {g: Apuracao(rs) for g, rs in sorted(grupos.items())}


def wilson(acertos: int, total: int, z: float = 1.959963985) -> Optional[Tuple[float, float]]:
    """Intervalo de confiança de 95% de Wilson para uma proporção.

    `z` é o quantil 0,975 da normal padrão. O método de Wilson é o indicado em
    `trabalho_de_conclusao/validacao/protocolo.md` porque, ao contrário do intervalo normal, nunca sai do [0, 1] e
    continua informativo quando a proporção é 1 — que é exatamente o caso aqui.
    """
    if total <= 0:
        return None
    p = acertos / total
    denominador = 1 + z * z / total
    centro = (p + z * z / (2 * total)) / denominador
    margem = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominador
    return max(0.0, centro - margem), min(1.0, centro + margem)


def carregar_casos() -> List[Dict[str, Any]]:
    dados = json.loads((CASOS / "casos_recomendacao.json").read_text(encoding="utf-8"))
    return dados["casos"]


def _construir_analise(entrada: Dict[str, Any]) -> AnaliseSolo:
    campos = dict(_CAMPOS_ANALISE_PADRAO)
    for chave, valor in entrada.items():
        if chave in campos:
            campos[chave] = valor
    if "subsuperficie" in entrada:
        campos["subsuperficie"] = Camada(**entrada["subsuperficie"])
    return AnaliseSolo(**campos)


def _construir_contexto(entrada: Dict[str, Any]) -> Contexto:
    return Contexto(
        cultura_id=entrada["cultura"],
        sistema_manejo=entrada["sistema_manejo"],
        condicao_area=entrada.get("condicao_area", "nao se aplica (ver CRITERIO_POR_CASO)"),
        prnt=entrada["prnt"],
        profundidade_incorporacao_cm=entrada["profundidade_incorporacao_cm"],
        cultivo=entrada.get("cultivo", 1),
        expectativa_rendimento=entrada.get("expectativa_rendimento"),
    )


#: Campos de `entrada` que o apurador lê para TODO caso, qualquer que seja o grupo:
#: identificação da cultura, perfil da análise e contexto de calagem.
_CAMPOS_COMUNS = frozenset(
    {"cultura", "cultivo", "subsuperficie", "sistema_manejo", "condicao_area",
     "prnt", "profundidade_incorporacao_cm", "expectativa_rendimento"}
    | set(_CAMPOS_ANALISE_PADRAO)
)


def campos_nao_lidos(entrada: Dict[str, Any], grupo: str) -> List[str]:
    """Campos de `entrada` que nenhum caminho do motor consome, para este grupo.

    Existe por causa do caso ADU-23 (2026-10-10): ele trazia `produtividade_estimada`,
    que é o nome do campo em FRUTÍFERAS, enquanto cana e tabaco leem
    `produtividade_t_ha`. O apurador montava os argumentos por nome e simplesmente não
    passava o valor. No ADU-23 isso derrubou o motor e ficou visível; nos casos de
    cebola, tomate e batata o rendimento caía exatamente no limiar do ajuste, o
    adicional era zero de qualquer forma, e o campo errado teria passado em silêncio —
    um caso que diz exercitar a expectativa de rendimento sem exercitar nada.

    Não entra no cálculo: é usada pelo teste de integridade dos casos, porque o que ela
    protege é o arquivo de casos, não a dose.
    """
    conhecidos = _CAMPOS_COMUNS | set(_EXTRAS_POR_GRUPO.get(grupo, ()))
    # Grãos e erva-mate não passam por `_EXTRAS_POR_GRUPO`: têm ramo próprio em
    # `_adubacao_do_caso`, e os campos que esse ramo lê entram aqui.
    if grupo == "graos":
        conhecidos = conhecidos | {"antecedente"}
    if grupo == "erva_mate":
        conhecidos = conhecidos | {"programa"}
    return sorted(set(entrada) - conhecidos)


def _grupo_da_cultura(cultura: str, dados: Dict[str, Any]) -> str:
    entrada = dados["mapa_culturas"]["culturas"].get(cultura)
    if entrada is None:
        raise ErroConcordancia(
            f"cultura '{cultura}' não está em mapa_culturas.json — sem o mapeamento não "
            f"há como saber em que grupo somar este caso"
        )
    return entrada["grupo"]


def _adubacao_do_caso(
    caso: Dict[str, Any], entrada: Dict[str, Any], grupo: str, dados: Dict[str, Any]
) -> Dict[str, Any]:
    """Doses de N, P2O5 e K2O pelo caminho do grupo da cultura."""
    if grupo == "graos":
        resultado_n = calcular_nitrogenio(
            entrada["cultura"], mo=entrada["mo"], antecedente=entrada.get("antecedente"),
            expectativa_rendimento=entrada.get("expectativa_rendimento"),
        )
        resultado_pk = calcular_fosforo_potassio(
            cultura_id=entrada["cultura"],
            argila=entrada["argila"], p_solo=entrada["p"],
            ctc_ph7=entrada["ctc_ph7"], k_solo=entrada["k"],
            cultivo=entrada.get("cultivo", 1),
            expectativa_rendimento=entrada.get("expectativa_rendimento"),
        )
        return {
            "n": resultado_n["n"],
            "p2o5": resultado_pk["p2o5"], "k2o": resultado_pk["k2o"],
            "classe_p": resultado_pk["classe_p"], "classe_k": resultado_pk["classe_k"],
        }

    despacho = _ADUBACAO_POR_GRUPO.get(grupo)
    if despacho is None:
        raise ErroConcordancia(
            f"caso '{caso['id']}': grupo '{grupo}' não é despachado por este apurador"
        )
    calcular, carregar, chave_dados = despacho
    extras = {
        nome: entrada[nome]
        for nome in _EXTRAS_POR_GRUPO[grupo]
        if entrada.get(nome) is not None
    }
    argumentos = dict(
        mo=entrada["mo"], argila=entrada["argila"], p_solo=entrada["p"],
        k_solo=entrada["k"], ctc_ph7=entrada["ctc_ph7"],
        dados_comuns=dados, **{chave_dados: carregar()}, **extras,
    )
    # Erva-mate não recebe cultura_id: a tabela é indexada por programa e fase, e a
    # espécie é uma só (Manual, §6.6.5).
    primeiro = entrada["programa"] if grupo == "erva_mate" else entrada["cultura"]
    return calcular(primeiro, **argumentos)


def _comparar(campo: str, esperado: Any, obtido: Any) -> bool:
    """Compara uma saída com a referência, sob a política de arredondamento.

    `trabalho_de_conclusao/validacao/protocolo.md` admite apenas tolerância de arredondamento: calcário com uma casa
    decimal em t/ha, nutrientes inteiros em kg/ha. Comparar float cru faria 2,2999999
    divergir de 2,3 e inventaria uma discordância que não existe.
    """
    if campo not in _CASAS:
        return esperado == obtido
    if obtido is None or isinstance(obtido, (dict, str)):
        return esperado == obtido
    return round(float(obtido), _CASAS[campo]) == round(float(esperado), _CASAS[campo])


def apurar_caso(caso: Dict[str, Any], dados: Dict[str, Any]) -> ResultadoDoCaso:
    """Roda um caso no motor e compara com tudo o que a referência declara."""
    entrada = caso["entrada"]
    referencia = caso["referencia"]
    cultura = entrada["cultura"]

    try:
        grupo = _grupo_da_cultura(cultura, dados)
    except ErroConcordancia as erro:
        return ResultadoDoCaso(caso["id"], caso.get("descricao", ""), "?", cultura,
                               False, erro=str(erro))

    resultado: ResultadoDoCaso = ResultadoDoCaso(
        id=caso["id"], descricao=caso.get("descricao", ""), grupo=grupo,
        cultura=cultura, concordante=True,
    )
    trace = Trace()
    obtido: Dict[str, Any] = {}

    try:
        if "nc_t_ha" in referencia or "motivo_sem_calagem" in referencia:
            criterio_id = CRITERIO_POR_CASO.get(caso["id"])
            if criterio_id is None:
                raise ErroConcordancia(
                    f"caso '{caso['id']}' declara calagem na referência e não está em "
                    f"CRITERIO_POR_CASO — acrescente o critério antes de apurar"
                )
            calagem = calcular_calagem(
                _construir_analise(entrada), criterio_id, _construir_contexto(entrada), trace
            )
            obtido["nc_t_ha"] = calagem["nc_t_ha"]
            obtido["motivo_sem_calagem"] = calagem["motivo"]

        if any(c in referencia for c in ("n", "p2o5", "k2o", "classe_p", "classe_k")):
            obtido.update(_adubacao_do_caso(caso, entrada, grupo, dados))
    except Exception as erro:  # noqa: BLE001 - o apurador não pode derrubar o relatório
        resultado.concordante = False
        resultado.erro = f"{type(erro).__name__}: {erro}"
        return resultado

    for campo, esperado in referencia.items():
        if campo not in obtido:
            continue
        if not _comparar(campo, esperado, obtido[campo]):
            resultado.divergencias.append(Divergencia(campo, esperado, obtido[campo]))

    resultado.concordante = not resultado.divergencias
    if not resultado.concordante:
        # O protocolo exige analisar cada discordante com o Trace: é o que separa erro de
        # implementação de divergência de interpretação do critério.
        resultado.trace = [f"{p.regra} -> {p.saida} ({p.fonte})" for p in trace]
    return resultado


def apurar_recomendacao(dados: Optional[Dict[str, Any]] = None) -> Apuracao:
    """Apura todos os casos de `testes/casos/casos_recomendacao.json`.

    Só entram casos com `conferido_por_autor_em` preenchido e com `referencia` igual a
    `verificacao_cruzada`. Caso sem conferência não é oráculo — é exemplo —, e somá-lo
    inflaria o denominador com evidência que não existe.
    """
    dados = dados if dados is not None else carregar_dados_comum()
    resultados = []
    for caso in carregar_casos():
        if not caso.get("conferido_por_autor_em"):
            continue
        if caso.get("verificacao_cruzada") not in (None, caso["referencia"]):
            resultados.append(ResultadoDoCaso(
                caso["id"], caso.get("descricao", ""), "?", caso["entrada"]["cultura"],
                False, erro="referencia diverge de verificacao_cruzada",
            ))
            continue
        resultados.append(apurar_caso(caso, dados))
    return Apuracao(resultados)


# --- conformidade da aptidão -------------------------------------------------------
#
# Dimensão separada, e deliberadamente chamada de CONFORMIDADE e não de concordância: ela
# mede se a implementação reproduz o CCAE, não se o CCAE está agronomicamente certo. O
# gabarito é lido só aqui e em testes/unidade/test_conformidade_aptidao.py; o motor nunca
# o abre.

@dataclass
class ApuracaoAptidao:
    total: int
    classe_ok: int
    fator_ok: int
    divergentes: List[str] = field(default_factory=list)

    def taxa_classe(self) -> Optional[float]:
        return self.classe_ok / self.total if self.total else None

    def taxa_fator(self) -> Optional[float]:
        return self.fator_ok / self.total if self.total else None

    def intervalo_classe(self) -> Optional[Tuple[float, float]]:
        return wilson(self.classe_ok, self.total)


def apurar_aptidao() -> ApuracaoAptidao:
    from siras.motor.aptidao import avaliar_aptidao_ccae

    entradas = {
        c["id_caso"]: c
        for c in json.loads(
            (CASOS / "entradas_aptidao.json").read_text(encoding="utf-8")
        )["casos"]
    }
    with open(CASOS / "gabarito_aptidao.csv", encoding="utf-8") as arquivo:
        gabarito = [
            linha for linha in csv.DictReader(arquivo)
            if linha["status"] in ("CONFERIDO", "CORRIGIDO_NA_CONFERENCIA")
        ]

    classe_ok = fator_ok = 0
    divergentes: List[str] = []
    for linha in gabarito:
        caso = entradas[linha["id_caso"]]
        r = avaliar_aptidao_ccae(
            analise=caso["entrada"], cultura=caso["cultura"], cenario=linha["cenario"]
        )
        acertou_classe = r.classe == linha["classe_esperada"]
        acertou_fator = r.fator_determinante == linha["fator_determinante_esperado"]
        classe_ok += int(acertou_classe)
        fator_ok += int(acertou_fator)
        if not (acertou_classe and acertou_fator):
            divergentes.append(
                f"{linha['id_caso']} [{linha['cenario']}]: esperado "
                f"{linha['classe_esperada']}/{linha['fator_determinante_esperado']}, "
                f"obtido {r.classe}/{r.fator_determinante}"
            )
    return ApuracaoAptidao(len(gabarito), classe_ok, fator_ok, divergentes)


__all__ = [
    "Apuracao",
    "ApuracaoAptidao",
    "CRITERIO_POR_CASO",
    "Divergencia",
    "ErroConcordancia",
    "ResultadoDoCaso",
    "apurar_aptidao",
    "apurar_caso",
    "apurar_recomendacao",
    "carregar_casos",
    "wilson",
]
