"""
Aptidão edáfica: classificação determinística por fator mínimo (Ramalho Filho e Beek,
1995, conforme descrito por Höfig, Moura e Giasson, 2015), aplicada aos sete fatores
químicos e texturais definidos em docs/CCAE-v1.0.md (F1 acidez, F2 fósforo, F3 potássio,
F4 cálcio/magnésio, F5 CTC, F6 matéria orgânica, F7 textura).

Reaproveita a base de conhecimento e os motores já existentes em vez de duplicá-los:
- classes de argila/CTC/Ca/Mg/MO vêm de interpretacao_geral.json;
- classes de disponibilidade de P e K vêm de interpretacao_p.json/interpretacao_k.json,
  via classificar_faixa() de motor/adubacao.py;
- o grupo de exigência de P/K (F2/F3) é resolvido em duas camadas (docs/decisoes/0005,
  D5.6/D5.7): primeiro tenta `grupo_exigencia.p`/`.k`, já transcrito do Anexo 2 por
  cultura nos arquivos de adubação por grupo (hortaliças, tubérculos, outras, frutíferas,
  erva-mate — S3/S4 do ROADMAP, ~50 culturas); só cai para grupo_exigencia() de
  motor/adubacao.py (catálogo de interpretacao_p.json/interpretacao_k.json + fallback de
  grãos) quando a cultura não aparece em nenhum dos cinco arquivos — é o caso de grãos e
  das poucas culturas sem adubação implementada mas com grupo P/K conhecido (ramo b de F1);
- a exequibilidade da calagem no cenário POTENCIAL (CCAE §7.2) chama
  motor.calagem.calcular_calagem_por_cultura() em vez de recalcular a dose.
Só a camada de grau/classe que não vem do Manual (Ramalho Filho e Beek, Sobral et al.,
e as decisões do autor no Apêndice A do CCAE) mora em dados/comum/criterios_aptidao.json
e config_aptidao.json.

Cultura fora dos catálogos (ph_referencia.json, interpretacao_p.json/interpretacao_k.json
+ mapa_culturas.json) não levanta exceção: retorna ResultadoAptidao com
classe="INDETERMINADA" (CCAE P5, Seção 3) — decisão registrada em docs/decisoes/0005,
deliberadamente diferente do estilo de exceção de motor/calagem.py e motor/adubacao.py,
porque o CCAE especifica INDETERMINADA como saída de primeira classe, não como erro de
programação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from siras.conhecimento.carregador import (
    carregar_dados_comum,
    carregar_dados_erva_mate,
    carregar_dados_frutiferas,
    carregar_dados_hortalicas,
    carregar_dados_outras,
    carregar_dados_tuberculos,
)
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.adubacao import ErroAdubacao, classificar_faixa, grupo_exigencia
from siras.motor.calagem import ErroCalagem, calcular_calagem_por_cultura, resolver_criterio_id
from siras.motor.trace import Trace

# Arquivos de adubação por grupo cujas culturas já trazem grupo_exigencia.p/.k
# transcrito do Anexo 2 (S3/S4 do ROADMAP) — consultados antes do catálogo genérico de
# interpretacao_p.json/interpretacao_k.json (docs/decisoes/0005, D5.7).
_CARREGADORES_GRUPO_EXIGENCIA = (
    carregar_dados_hortalicas,
    carregar_dados_tuberculos,
    carregar_dados_outras,
    carregar_dados_frutiferas,
    carregar_dados_erva_mate,
)


class _CulturaOuDadoIndeterminado(Exception):
    """Interno: sinaliza que a avaliação não pode prosseguir (cultura fora dos
    catálogos). Capturado em avaliar_aptidao() e convertido em classe INDETERMINADA —
    nunca escapa da função pública."""


class ErroAptidao(Exception):
    """Cultura explicitamente fora do escopo do SIRAS (arroz irrigado por alagamento,
    CCAE Sec. 1.3) — distinto de cultura desconhecida (essa vira INDETERMINADA). Escopo
    excluído deliberadamente não é erro de dado, então não é silenciado: propaga ao
    chamador, no mesmo espírito de ErroCalagem para os mesmos critérios."""


@dataclass(frozen=True)
class AvaliacaoFator:
    """Grau de limitação de um fator, com a evidência e a fonte que o justificam."""

    id: str
    grau: int
    rotulo: str
    evidencia: str
    fonte: str


@dataclass(frozen=True)
class ResultadoAptidao:
    """Saída de avaliar_aptidao() para um cenário (ATUAL ou POTENCIAL)."""

    cenario: str
    classe: str
    grau_final: Optional[int]
    fator_determinante: Optional[str]
    fatores: List[AvaliacaoFator] = field(default_factory=list)
    alertas: List[str] = field(default_factory=list)
    rebaixamento_aplicado: bool = False
    versao_criterios: str = "1.0"


def _atributo_geral(interpretacao_geral: Dict[str, Any], nome: str) -> Dict[str, Any]:
    for atributo in interpretacao_geral["atributos"]:
        if atributo["atributo"] == nome:
            return atributo
    raise ErroAdubacao(f"atributo '{nome}' não encontrado em interpretacao_geral.json")


def _classe_argila(argila: float, interpretacao_geral: Dict[str, Any]) -> str:
    return classificar_faixa(argila, _atributo_geral(interpretacao_geral, "argila")["faixas"])


def _resolver_ph_referencia(cultura_id: str, dados_ph_ref: Dict[str, Any]) -> Optional[float]:
    """None é um valor válido (ramo b, culturas tolerantes a Al) — distinto de cultura
    não encontrada em nenhum grupo, que levanta _CulturaOuDadoIndeterminado."""
    for grupo in dados_ph_ref["grupos"]:
        if cultura_id in grupo["culturas"]:
            return grupo["ph_referencia"]
    raise _CulturaOuDadoIndeterminado(
        f"cultura '{cultura_id}' não encontrada em ph_referencia.json"
    )


def _buscar_grupo_exigencia_transcrito(cultura_id: str) -> Optional[Dict[str, int]]:
    """Procura grupo_exigencia.p/.k já transcrito do Anexo 2 (p. 361-366) nos arquivos de
    adubação por grupo. A chave do dict "culturas" de cada arquivo é um agrupamento
    composto (ex.: "abobora_abobrinha_moranga"), não o cultura_id individual — a busca é
    sempre pela lista "culturas_incluidas" de cada entrada, nunca pela chave do dict."""
    for carregar in _CARREGADORES_GRUPO_EXIGENCIA:
        for entrada in carregar()["adubacao"]["culturas"].values():
            if cultura_id in entrada.get("culturas_incluidas", ()) and "grupo_exigencia" in entrada:
                return entrada["grupo_exigencia"]
    return None


def _resolver_grupo_p_ou_k(cultura_id: str, eixo: str, dados: Dict[str, Any]) -> str:
    """Resolve o grupo de exigência (P ou K) em duas camadas (docs/decisoes/0005, D5.7):
    1) grupo_exigencia.p/.k já transcrito por cultura nos arquivos de adubação por grupo;
    2) grupo_exigencia() de motor/adubacao.py (catálogo de interpretacao_p.json/
       interpretacao_k.json + fallback de grãos), só quando (1) não encontra a cultura.
    """
    transcrito = _buscar_grupo_exigencia_transcrito(cultura_id)
    if transcrito is not None:
        return f"grupo_{transcrito[eixo]}"

    nome_arquivo = "interpretacao_p.json" if eixo == "p" else "interpretacao_k.json"
    interp = dados["interpretacao_p"] if eixo == "p" else dados["interpretacao_k"]
    try:
        return grupo_exigencia(cultura_id, dados["mapa_culturas"], interp["grupos_exigencia"], nome_arquivo)
    except ErroAdubacao as e:
        raise _CulturaOuDadoIndeterminado(str(e)) from e


def _aplicar_teto(grau: int, rotulo: str, teto_nome: str, graus: Dict[str, int]) -> Tuple[int, str]:
    teto_grau = graus[teto_nome]
    if grau > teto_grau:
        return teto_grau, teto_nome
    return grau, rotulo


def _avaliar_f1_acidez(
    analise: AnaliseSolo, cultura_id: str, dados: Dict[str, Any]
) -> AvaliacaoFator:
    criterios = dados["criterios_aptidao"]
    graus = criterios["graus"]
    crit_f1 = criterios["F1_acidez"]

    ph_referencia = _resolver_ph_referencia(cultura_id, dados["ph_referencia"])

    if ph_referencia is not None:
        fonte = crit_f1["com_ph_referencia"]["_fonte"]
        if analise.ph_agua >= ph_referencia:
            grau, rotulo = graus["NULO"], "NULO"
            evidencia = f"pH {analise.ph_agua} >= pH de referência {ph_referencia}"
        elif analise.ph_agua >= 5.5:
            grau, rotulo = graus["LIGEIRO"], "LIGEIRO"
            evidencia = (
                f"pH {analise.ph_agua} entre 5,5 e a referência {ph_referencia} "
                f"(acidez limita pouco a produtividade nessa faixa)"
            )
        else:
            m_percent = analise.obter_saturacao_al()
            rotulo = classificar_faixa(m_percent, crit_f1["com_ph_referencia"]["m_percent_faixas"])
            grau = graus[rotulo]
            evidencia = f"pH {analise.ph_agua} < 5,5; m% = {m_percent:.1f} -> {rotulo}"
    else:
        sem = crit_f1["sem_ph_referencia"]
        fonte = sem["_fonte"]
        excecao = analise.ca >= sem["excecao_ca_minimo"] and analise.mg >= sem["excecao_mg_minimo"]
        if analise.v_percent >= sem["v_minimo"] or excecao:
            grau, rotulo = graus["NULO"], "NULO"
            evidencia = (
                f"cultura sem pH de referência; V% {analise.v_percent} >= {sem['v_minimo']} "
                f"ou Ca/Mg suficientes (Ca={analise.ca}, Mg={analise.mg})"
            )
        else:
            rotulo = sem["grau_se_deficiente"]
            grau = graus[rotulo]
            evidencia = (
                f"cultura sem pH de referência; V% {analise.v_percent} < {sem['v_minimo']} "
                f"e Ca/Mg insuficientes (Ca={analise.ca}, Mg={analise.mg})"
            )

    return AvaliacaoFator("F1_acidez", grau, rotulo, evidencia, fonte)


def _avaliar_f2_fosforo(
    analise: AnaliseSolo, cultura_id: str, dados: Dict[str, Any]
) -> Tuple[AvaliacaoFator, str]:
    interp_p = dados["interpretacao_p"]
    criterios = dados["criterios_aptidao"]
    graus = criterios["graus"]

    grupo = _resolver_grupo_p_ou_k(cultura_id, "p", dados)

    tabela_grupo = next(t for t in interp_p["tabelas"] if t["grupo"] == grupo)
    if "fora do escopo" in str(tabela_grupo.get("nota", "")).lower():
        raise ErroAptidao(
            f"cultura '{cultura_id}' resolve para {grupo} de interpretacao_p.json, que está "
            f"fora do escopo do SIRAS (CCAE Sec. 1.3): {tabela_grupo['nota']}"
        )

    classe_argila = _classe_argila(analise.argila, dados["interpretacao_geral"])
    bloco = next(b for b in tabela_grupo["por_classe_argila"] if b["classe_argila"] == classe_argila)
    classe_teor = classificar_faixa(analise.p, bloco["faixas"])

    rotulo = criterios["mapeamento_disponibilidade_grau"][classe_teor]
    grau = graus[rotulo]
    evidencia = (
        f"P {analise.p} mg/dm3, argila classe {classe_argila}, {grupo} -> {classe_teor}"
    )
    fonte = f"{tabela_grupo['fonte']}; {criterios['mapeamento_disponibilidade_grau']['_fonte']}"

    return AvaliacaoFator("F2_fosforo", grau, rotulo, evidencia, fonte), classe_teor


def _avaliar_f3_potassio(
    analise: AnaliseSolo, cultura_id: str, dados: Dict[str, Any]
) -> Tuple[AvaliacaoFator, str]:
    interp_k = dados["interpretacao_k"]
    criterios = dados["criterios_aptidao"]
    graus = criterios["graus"]

    grupo = _resolver_grupo_p_ou_k(cultura_id, "k", dados)

    faixa_ctc = classificar_faixa(analise.ctc_ph7, interp_k["faixas_ctc"], chave_rotulo="faixa")
    tabela_grupo = next(t for t in interp_k["tabelas"] if t["grupo"] == grupo)
    bloco = next(b for b in tabela_grupo["por_faixa_ctc"] if b["faixa_ctc"] == faixa_ctc)
    classe_teor = classificar_faixa(analise.k, bloco["faixas"])

    rotulo = criterios["mapeamento_disponibilidade_grau"][classe_teor]
    grau = graus[rotulo]
    evidencia = (
        f"K {analise.k} mg/dm3, CTC pH7 {analise.ctc_ph7} (faixa {faixa_ctc}), "
        f"{grupo} -> {classe_teor}"
    )
    fonte = f"{tabela_grupo['fonte']}; {criterios['mapeamento_disponibilidade_grau']['_fonte']}"

    return AvaliacaoFator("F3_potassio", grau, rotulo, evidencia, fonte), classe_teor


def _avaliar_f4_ca_mg(analise: AnaliseSolo, dados: Dict[str, Any], config: Dict[str, Any]) -> AvaliacaoFator:
    criterios = dados["criterios_aptidao"]
    graus = criterios["graus"]
    geral = dados["interpretacao_geral"]
    mapa = criterios["F4_ca_mg"]["mapeamento"]

    classe_ca = classificar_faixa(analise.ca, _atributo_geral(geral, "calcio")["faixas"])
    classe_mg = classificar_faixa(analise.mg, _atributo_geral(geral, "magnesio")["faixas"])
    rotulo_ca, rotulo_mg = mapa[classe_ca], mapa[classe_mg]
    grau_ca, grau_mg = graus[rotulo_ca], graus[rotulo_mg]

    if grau_ca >= grau_mg:
        grau, rotulo = grau_ca, rotulo_ca
    else:
        grau, rotulo = grau_mg, rotulo_mg

    grau, rotulo = _aplicar_teto(grau, rotulo, config["F4_GRAU_MAXIMO"], graus)
    evidencia = f"Ca {analise.ca} cmolc/dm3 ({classe_ca}), Mg {analise.mg} cmolc/dm3 ({classe_mg})"

    return AvaliacaoFator("F4_ca_mg", grau, rotulo, evidencia, criterios["F4_ca_mg"]["_fonte"])


def _avaliar_f5_ctc(analise: AnaliseSolo, dados: Dict[str, Any], config: Dict[str, Any]) -> AvaliacaoFator:
    criterios = dados["criterios_aptidao"]
    graus = criterios["graus"]
    mapa = criterios["F5_ctc"]["mapeamento"]

    classe = classificar_faixa(analise.ctc_ph7, _atributo_geral(dados["interpretacao_geral"], "ctc_ph7")["faixas"])
    rotulo = mapa[classe]
    grau = graus[rotulo]
    grau, rotulo = _aplicar_teto(grau, rotulo, config["F5_GRAU_MAXIMO"], graus)
    evidencia = f"CTC pH7 {analise.ctc_ph7} cmolc/dm3 -> classe {classe}"

    return AvaliacaoFator("F5_ctc", grau, rotulo, evidencia, criterios["F5_ctc"]["_fonte"])


def _avaliar_f6_mo(analise: AnaliseSolo, dados: Dict[str, Any], config: Dict[str, Any]) -> AvaliacaoFator:
    criterios = dados["criterios_aptidao"]
    graus = criterios["graus"]
    mapa = criterios["F6_mo"]["mapeamento"]

    classe = classificar_faixa(
        analise.mo, _atributo_geral(dados["interpretacao_geral"], "materia_organica")["faixas"]
    )
    rotulo = mapa[classe]
    grau = graus[rotulo]
    grau, rotulo = _aplicar_teto(grau, rotulo, config["F6_GRAU_MAXIMO"], graus)
    evidencia = f"MO {analise.mo}% -> classe {classe}"

    return AvaliacaoFator("F6_mo", grau, rotulo, evidencia, criterios["F6_mo"]["_fonte"])


def _avaliar_f7_textura(
    analise: AnaliseSolo, dados: Dict[str, Any], config: Dict[str, Any]
) -> AvaliacaoFator:
    criterios = dados["criterios_aptidao"]
    graus = criterios["graus"]
    fonte = criterios["F7_textura"]["_fonte"]

    if not config["F7_ATIVO"]:
        return AvaliacaoFator("F7_textura", graus["NULO"], "NULO", "F7 desativado por config_aptidao.json", fonte)

    classe_argila = _classe_argila(analise.argila, dados["interpretacao_geral"])
    rotulo = criterios["F7_textura"]["mapeamento_por_classe_argila"][classe_argila]
    grau = graus[rotulo]
    evidencia = f"argila {analise.argila}% -> classe {classe_argila}"

    return AvaliacaoFator("F7_textura", grau, rotulo, evidencia, fonte)


def _forcar_nulo(fator: AvaliacaoFator, motivo: str, graus: Dict[str, int]) -> AvaliacaoFator:
    return AvaliacaoFator(
        fator.id, graus["NULO"], "NULO", f"{fator.evidencia} -> corrigido no cenário POTENCIAL: {motivo}",
        fator.fonte,
    )


def _resolver_f1_potencial(
    f1_atual: AvaliacaoFator,
    analise: AnaliseSolo,
    cultura_id: str,
    contexto: Contexto,
    dados: Dict[str, Any],
    trace: Trace,
) -> Tuple[AvaliacaoFator, List[str]]:
    """CCAE §7.2: F1 no cenário POTENCIAL vira NULO se a calagem recomendada for
    exequível; permanece um grau acima de NULO (LIGEIRO) se a dose exceder o teto
    operacional; permanece inalterado se a calagem nem chega a ser disparada (F1 já era
    NULO/LIGEIRO no cenário ATUAL — o Manual não recomenda calcário nesse caso, então não
    há correção real a projetar)."""
    graus = dados["criterios_aptidao"]["graus"]

    if f1_atual.grau == graus["NULO"]:
        return f1_atual, []

    try:
        resultado_calagem = calcular_calagem_por_cultura(analise, cultura_id, contexto, trace)
    except ErroCalagem:
        return f1_atual, [
            "não foi possível calcular a dose de calagem para verificar a exequibilidade "
            "da correção de F1 no cenário POTENCIAL; grau de F1 mantido"
        ]

    nc_t_ha = resultado_calagem["nc_t_ha"]
    if not nc_t_ha:
        return f1_atual, []

    criterio_id = resolver_criterio_id(cultura_id, contexto, dados)
    criterio = next(c for c in dados["criterios_calagem"]["criterios"] if c["id"] == criterio_id)
    modo = criterio["modo_aplicacao"]
    config = dados["config_aptidao"]
    teto = config["NC_MAX_INCORPORADO_T_HA"] if modo == "incorporado" else config["NC_MAX_SUPERFICIAL_T_HA"]

    if nc_t_ha <= teto:
        fator = AvaliacaoFator(
            "F1_acidez", graus["NULO"], "NULO",
            f"{f1_atual.evidencia} -> corrigido: NC {nc_t_ha} t/ha ({modo}) <= teto {teto} t/ha",
            f1_atual.fonte,
        )
        return fator, []

    fator = AvaliacaoFator(
        "F1_acidez", graus["LIGEIRO"], "LIGEIRO",
        f"{f1_atual.evidencia} -> NC {nc_t_ha} t/ha ({modo}) excede o teto {teto} t/ha; "
        f"correção plurianual necessária (CCAE §7.2)",
        f1_atual.fonte,
    )
    return fator, ["correcao_parcelada"]


def _rebaixar(classe: str, ordem_classes: List[str]) -> str:
    indice = ordem_classes.index(classe)
    return ordem_classes[min(indice + 1, len(ordem_classes) - 1)]


def avaliar_aptidao(
    analise: AnaliseSolo,
    cultura_id: str,
    cenario: str,
    contexto: Contexto,
    trace: Trace,
    dados: Optional[Dict[str, Any]] = None,
) -> ResultadoAptidao:
    """Avalia a aptidão edáfica de uma análise de solo para uma cultura, num cenário.

    Args:
        analise: análise de solo já validada (AnaliseSolo valida faixa física na
            construção — esta função não repete essa validação)
        cultura_id: identificador da cultura (mesmo catálogo de calagem/adubação)
        cenario: "ATUAL" ou "POTENCIAL" (CCAE §7)
        contexto: contexto operacional, necessário só no cenário POTENCIAL (exequibilidade
            da calagem, CCAE §7.2)
        trace: acumulador de passos de inferência
        dados: base de conhecimento pré-carregada (facilita testes); default carrega via
            carregar_dados_comum()

    Returns:
        ResultadoAptidao. Cultura fora dos catálogos -> classe "INDETERMINADA" (CCAE P5),
        nunca uma exceção.

    Raises:
        ValueError: cenario diferente de "ATUAL"/"POTENCIAL"
    """
    if cenario not in ("ATUAL", "POTENCIAL"):
        raise ValueError(f"cenario deve ser 'ATUAL' ou 'POTENCIAL', recebido '{cenario}'")

    dados = dados if dados is not None else carregar_dados_comum()
    criterios = dados["criterios_aptidao"]
    config = dados["config_aptidao"]
    graus = criterios["graus"]

    fora_de_escopo = criterios.get("fora_de_escopo", {})
    if cultura_id in fora_de_escopo.get("culturas", []):
        raise ErroAptidao(
            f"cultura '{cultura_id}' está fora do escopo do módulo de aptidão edáfica na "
            f"v1.0 ({fora_de_escopo.get('_fonte', 'CCAE-v1.0.md Sec. 1.3')})"
        )

    try:
        f1 = _avaliar_f1_acidez(analise, cultura_id, dados)
        f2, classe_teor_p = _avaliar_f2_fosforo(analise, cultura_id, dados)
        f3, classe_teor_k = _avaliar_f3_potassio(analise, cultura_id, dados)
    except _CulturaOuDadoIndeterminado as e:
        trace.registrar(
            "aptidao_indeterminada", {"cultura_id": cultura_id}, {"motivo": str(e)},
            "CCAE-v1.0.md Sec. 3, P5",
        )
        return ResultadoAptidao(
            cenario=cenario, classe="INDETERMINADA", grau_final=None, fator_determinante=None,
            alertas=[str(e)],
        )

    f4 = _avaliar_f4_ca_mg(analise, dados, config)
    f5 = _avaliar_f5_ctc(analise, dados, config)
    f6 = _avaliar_f6_mo(analise, dados, config)
    f7 = _avaliar_f7_textura(analise, dados, config)

    alertas: List[str] = []
    for fator, classe_teor in ((f2, classe_teor_p), (f3, classe_teor_k)):
        if classe_teor == "muito_alto":
            alertas.append(
                f"{fator.id}: teor classificado Muito alto — risco ambiental (LCA), sem "
                f"impacto na classe de aptidão (CCAE A-6, Manual Cap. 10, p. 332-333)"
            )

    if cenario == "POTENCIAL":
        f2 = _forcar_nulo(f2, "adubação fosfatada corretiva recomendada (CCAE §7.1)", graus)
        f3 = _forcar_nulo(f3, "adubação potássica corretiva recomendada (CCAE §7.1)", graus)
        f4 = _forcar_nulo(f4, "calcário dolomítico aplicado na mesma operação da calagem (CCAE §7.1)", graus)
        f6 = _forcar_nulo(f6, "nitrogênio suprido por adubação na safra (CCAE §7.1)", graus)
        f1, alertas_f1 = _resolver_f1_potencial(f1, analise, cultura_id, contexto, dados, trace)
        alertas.extend(alertas_f1)
        # F5 e F7 são PERMANENTE (CCAE §7.1): inalterados.

    fatores = [f1, f2, f3, f4, f5, f6, f7]
    for fator in fatores:
        trace.registrar(
            fator.id, {"cultura_id": cultura_id, "cenario": cenario},
            {"grau": fator.grau, "rotulo": fator.rotulo, "evidencia": fator.evidencia}, fator.fonte,
        )

    grau_final = max(fator.grau for fator in fatores)
    fator_determinante = next(fator.id for fator in fatores if fator.grau == grau_final)
    classe = criterios["composicao"]["grau_para_classe"][str(grau_final)]

    rebaixamento_aplicado = False
    if config["REBAIXAMENTO_POR_ACUMULO"]:
        contagem_moderados_ou_mais = sum(1 for fator in fatores if fator.grau >= graus["MODERADO"])
        if contagem_moderados_ou_mais >= config["REBAIXAMENTO_MIN_FATORES"] and classe != "INAPTA_SEM_CORRECAO":
            classe = _rebaixar(classe, criterios["composicao"]["ordem_classes"])
            rebaixamento_aplicado = True

    trace.registrar(
        "composicao_aptidao", {"cenario": cenario, "grau_final": grau_final},
        {"classe": classe, "fator_determinante": fator_determinante, "rebaixamento_aplicado": rebaixamento_aplicado},
        criterios["composicao"]["_fonte"],
    )

    return ResultadoAptidao(
        cenario=cenario,
        classe=classe,
        grau_final=grau_final,
        fator_determinante=fator_determinante,
        fatores=fatores,
        alertas=alertas,
        rebaixamento_aplicado=rebaixamento_aplicado,
    )
