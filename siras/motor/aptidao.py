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
from decimal import Decimal
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
from siras.dominio.nomes import normalizar_nome_cultura
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

#: Versão do CCAE que este motor implementa. Aparece em ResultadoAptidao.versao_criterios
#: e é o que o conjunto de conformidade declara ter gabaritado (CCAE §9.1).
_VERSAO_CRITERIOS = "1.2"


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
    versao_criterios: str = _VERSAO_CRITERIOS
    #: Valores intermediários que os fatores consomem (V%, m%, classe de argila, classe de
    #: CTC). Não fazem parte do contrato do CCAE-implementacao.md §6; existem porque a
    #: verificação de conformidade precisa localizar em QUAL etapa uma divergência nasceu —
    #: um V% errado erra F1 e a classe junto, e sem isto os dois casos são indistinguíveis.
    derivados: Dict[str, Any] = field(default_factory=dict)


def _atributo_geral(interpretacao_geral: Dict[str, Any], nome: str) -> Dict[str, Any]:
    for atributo in interpretacao_geral["atributos"]:
        if atributo["atributo"] == nome:
            return atributo
    raise ErroAdubacao(f"atributo '{nome}' não encontrado em interpretacao_geral.json")


def _classe_argila(argila: float, interpretacao_geral: Dict[str, Any]) -> str:
    return classificar_faixa(argila, _atributo_geral(interpretacao_geral, "argila")["faixas"])


def _classificar_faixa_fechada_no_meio(
    valor: float, faixas: List[Dict[str, Any]], contexto: str, chave_rotulo: str = "classe"
) -> str:
    """Segunda convenção de intervalo do Manual — a exceção, não a regra.

    classificar_faixa() de motor/adubacao.py implementa a convenção dominante, em que o
    limite superior é inclusivo (`de < v <= ate`): é assim que o Manual publica as tabelas
    de P (6.3-6.5), K (6.8-6.10), argila, CTC e MO, todas escritas como "<= a" / "a+1 - b".

    Duas tabelas são escritas de outro jeito e exigem esta função:

    - **Tabela 6.11 (Ca e Mg), p. 97:** "< 2,0" / "2,0 - 4,0" / "> 4,0". O valor 2,0 está
      escrito na faixa do meio, logo Ca = 2,0 é Médio, não Baixo. Idem Ca = 4,0, Mg = 0,5
      e Mg = 1,0.
    - **CCAE §F1, saturação por alumínio:** "m% < 30" / "30 <= m% <= 50" / "m% > 50".
      Logo m% = 30,0 é FORTE, não MODERADO, e m% = 50,0 é FORTE, não MUITO_FORTE.

    Nos dois casos a faixa do meio é fechada nos dois extremos, e as pontas são
    estritamente abertas. Aplicar `<=` aqui erra silenciosamente, e só nos valores de
    fronteira — os casos CONF-FR-21, CONF-FR-23, CAL-13 e ANX-G3-* existem para pegar
    isso (docs/HANDOFF-aptidao.md §4).

    Os limites em si continuam vindo dos dados transcritos; o que muda é só a comparação.
    Decimal porque a comparação é exatamente sobre o limite, onde float falha.
    """
    v = Decimal(str(valor))
    for faixa in faixas:
        de, ate = faixa["de"], faixa["ate"]
        if de is None and ate is not None and v < Decimal(str(ate)):
            return faixa[chave_rotulo]
        if de is not None and ate is not None and Decimal(str(de)) <= v <= Decimal(str(ate)):
            return faixa[chave_rotulo]
        if ate is None and de is not None and v > Decimal(str(de)):
            return faixa[chave_rotulo]
    raise ErroAdubacao(f"valor {valor} não se encaixa em nenhuma faixa de {contexto}: {faixas}")


def _grafias_do_catalogo(
    candidatos: Tuple[str, ...], dados: Dict[str, Any], eixo: str
) -> Tuple[str, ...]:
    """Acrescenta aos candidatos a grafia EXATA usada pelos catálogos consultados na
    camada 2. grupo_exigencia() compara por igualdade literal, e interpretacao_p.json
    escreve 'acácia-negra' com acento enquanto o caso de teste manda 'acacia_negra' —
    sem traduzir de volta para a grafia do catálogo, a cultura existe e mesmo assim não é
    encontrada."""
    interp = dados["interpretacao_p"] if eixo == "p" else dados["interpretacao_k"]
    indice: Dict[str, str] = {}
    for grupo in interp["grupos_exigencia"]:
        for cultura in grupo.get("culturas", ()):
            indice.setdefault(normalizar_nome_cultura(cultura), cultura)
    for cultura in dados["mapa_culturas"]["culturas"]:
        indice.setdefault(normalizar_nome_cultura(cultura), cultura)

    extras = [
        indice[normalizar_nome_cultura(nome)]
        for nome in candidatos
        if normalizar_nome_cultura(nome) in indice
    ]
    vistos: set = set()
    return tuple(
        nome for nome in (*candidatos, *extras) if not (nome in vistos or vistos.add(nome))
    )


def _nomes_candidatos(cultura_id: str, dados: Dict[str, Any]) -> Tuple[str, ...]:
    """Grafias sob as quais procurar a cultura, em ordem de precedência.

    A Tabela 5.1 e o Anexo 2 nomeiam a mesma cultura de formas diferentes, e os conjuntos
    de teste chegam numa terceira grafia. A ordem importa e é deliberada: o nome como veio
    primeiro, depois sua forma normalizada, e só então os sinônimos declarados em
    aliases_culturas.json. Assim acrescentar um grupo de sinônimos nunca muda a resolução
    de uma cultura que já resolvia sozinha (aliases_culturas.json, nota_precedencia).
    """
    canonico = normalizar_nome_cultura(cultura_id)
    nomes = [cultura_id, canonico]

    for grupo in dados["aliases_culturas"]["grupos_de_sinonimos"]:
        normalizados = [normalizar_nome_cultura(nome) for nome in grupo["nomes"]]
        if canonico in normalizados:
            nomes.extend(nome for nome in normalizados if nome != canonico)

    vistos: set = set()
    return tuple(nome for nome in nomes if not (nome in vistos or vistos.add(nome)))


def _resolver_ph_referencia(
    cultura_id: str, dados_ph_ref: Dict[str, Any], candidatos: Tuple[str, ...] = ()
) -> Optional[float]:
    """None é um valor válido (ramo b, culturas tolerantes a Al) — distinto de cultura
    não encontrada em nenhum grupo, que levanta _CulturaOuDadoIndeterminado. Por isso o
    índice é consultado com `in`, nunca por valor-verdade do .get()."""
    indice: Dict[str, Optional[float]] = {}
    for grupo in dados_ph_ref["grupos"]:
        for cultura in grupo["culturas"]:
            indice.setdefault(normalizar_nome_cultura(cultura), grupo["ph_referencia"])

    for nome in candidatos or (cultura_id,):
        chave = normalizar_nome_cultura(nome)
        if chave in indice:
            return indice[chave]

    raise _CulturaOuDadoIndeterminado(
        f"cultura '{cultura_id}' não encontrada em ph_referencia.json"
    )


def _buscar_grupo_exigencia_transcrito(candidatos: Tuple[str, ...]) -> Optional[Dict[str, int]]:
    """Procura grupo_exigencia.p/.k já transcrito do Anexo 2 (p. 361-366) nos arquivos de
    adubação por grupo. A chave do dict "culturas" de cada arquivo é um agrupamento
    composto (ex.: "abobora_abobrinha_moranga"), não o cultura_id individual — a busca é
    sempre pela lista "culturas_incluidas" de cada entrada, nunca pela chave do dict."""
    procurados = {normalizar_nome_cultura(nome) for nome in candidatos}
    for carregar in _CARREGADORES_GRUPO_EXIGENCIA:
        for entrada in carregar()["adubacao"]["culturas"].values():
            if "grupo_exigencia" not in entrada:
                continue
            incluidas = {normalizar_nome_cultura(c) for c in entrada.get("culturas_incluidas", ())}
            if procurados & incluidas:
                return entrada["grupo_exigencia"]
    return None


def _resolver_grupo_p_ou_k(cultura_id: str, eixo: str, dados: Dict[str, Any]) -> str:
    """Resolve o grupo de exigência (P ou K) em duas camadas (docs/decisoes/0005, D5.7):
    1) grupo_exigencia.p/.k já transcrito por cultura nos arquivos de adubação por grupo;
    2) grupo_exigencia() de motor/adubacao.py (catálogo de interpretacao_p.json/
       interpretacao_k.json + fallback de grãos), só quando (1) não encontra a cultura.
    Cada camada é tentada com todas as grafias de _nomes_candidatos().
    """
    candidatos = _nomes_candidatos(cultura_id, dados)

    transcrito = _buscar_grupo_exigencia_transcrito(candidatos)
    if transcrito is not None:
        return f"grupo_{transcrito[eixo]}"

    nome_arquivo = "interpretacao_p.json" if eixo == "p" else "interpretacao_k.json"
    interp = dados["interpretacao_p"] if eixo == "p" else dados["interpretacao_k"]
    ultimo_erro: Optional[ErroAdubacao] = None
    for nome in _grafias_do_catalogo(candidatos, dados, eixo):
        try:
            return grupo_exigencia(nome, dados["mapa_culturas"], interp["grupos_exigencia"], nome_arquivo)
        except ErroAdubacao as e:
            ultimo_erro = e
    raise _CulturaOuDadoIndeterminado(str(ultimo_erro)) from ultimo_erro


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

    ph_referencia = _resolver_ph_referencia(
        cultura_id, dados["ph_referencia"], _nomes_candidatos(cultura_id, dados)
    )

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
            # CCAE §F1: "m% < 30" / "30 <= m% <= 50" / "m% > 50" — faixa do meio fechada
            # nos dois extremos, ao contrário das tabelas de P/K (HANDOFF §4).
            rotulo = _classificar_faixa_fechada_no_meio(
                m_percent, crit_f1["com_ph_referencia"]["m_percent_faixas"],
                "saturação por alumínio (CCAE §F1)",
            )
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

    # Tabela 6.11 (p. 97) é escrita "< 2,0" / "2,0 - 4,0" / "> 4,0": o limite pertence à
    # faixa do meio, então Ca = 2,0 e Ca = 4,0 são Médio (HANDOFF §4).
    classe_ca = _classificar_faixa_fechada_no_meio(
        analise.ca, _atributo_geral(geral, "calcio")["faixas"], "cálcio (Tab. 6.11)"
    )
    classe_mg = _classificar_faixa_fechada_no_meio(
        analise.mg, _atributo_geral(geral, "magnesio")["faixas"], "magnésio (Tab. 6.11)"
    )
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


#: Manejo do laudo -> (sistema_manejo, condicao_area) de criterios_calagem.json. O CCAE
#: descreve o cenário POTENCIAL em termos de "aplicação incorporada" e "aplicação
#: superficial" (§7.2); quem sabe qual dos dois vale é o critério de calagem, e ele é
#: selecionado por esse par. Só os dois manejos que o conjunto de casos usa.
_MANEJO_PARA_CONTEXTO = {
    "convencional": ("convencional", "todos os casos"),
    "plantio_direto_consolidado": ("plantio_direto", "consolidado, sem restricoes na camada 10-20 cm"),
}


def _validar_faixas_de_entrada(entrada: Dict[str, Any], criterios: Dict[str, Any]) -> List[str]:
    """CCAE §5.4: valor fora da faixa válida REJEITA a entrada, nunca trunca. Devolve a
    lista de problemas (vazia = entrada aceita) em vez de levantar, porque o CCAE quer
    todos os campos faltantes ou inválidos listados de uma vez, não o primeiro."""
    faixas = criterios.get("faixas_entrada", {})
    problemas: List[str] = []

    for campo, limites in faixas.items():
        if campo.startswith("_"):
            continue
        valor = entrada.get(campo)
        if valor is None:
            problemas.append(f"campo obrigatório ausente: '{campo}'")
        elif not limites["minimo"] <= valor <= limites["maximo"]:
            problemas.append(
                f"'{campo}' = {valor} fora da faixa válida "
                f"[{limites['minimo']}; {limites['maximo']}] (CCAE §5.1)"
            )

    return problemas


def avaliar_aptidao_ccae(
    analise: Dict[str, Any], cultura: str, cenario: str
) -> ResultadoAptidao:
    """Contrato de verificação de conformidade do CCAE (HANDOFF §5): dict de entrada,
    nome de cultura, cenário — e nada mais.

    Existe separado de avaliar_aptidao() porque os dois têm donos diferentes.
    avaliar_aptidao() é a função do sistema: recebe AnaliseSolo já validada, Contexto e
    Trace, porque o laudo precisa da trilha de inferência (CLAUDE.md) e o técnico escolhe
    PRNT e profundidade. O CCAE descreve a assinatura mínima que a verificação de
    conformidade exercita. Adaptar aqui evita duas coisas ruins: mutilar o contrato do
    sistema para caber no do caderno, e reimplementar a lógica no runner de teste.

    O que este adaptador decide, e que o CCAE deixa implícito:

    - **V%** não vem no laudo dos casos; é derivado por `V% = 100 x S / CTC_pH7` com
      `S = Ca + Mg + K/391` (CCAE §5.2). m% e a saturação por Al ficam com AnaliseSolo,
      que já aplica a mesma fórmula do §5.2.
    - **Contexto** usa PRNT 100% e incorporação a 20 cm — a condição em que a Tabela 5.2
      publica a dose (CCAE §7.2), não uma escolha de campo.
    - **Falha explícita** (CCAE P5, §5.4): campo ausente, valor fora de faixa, cultura
      desconhecida ou fora de escopo devolvem INDETERMINADA com o motivo em `alertas`.
      Nenhum valor é imputado, e a exceção nunca escapa.

    Returns:
        ResultadoAptidao. Nunca levanta por dado de entrada; só por `cenario` inválido,
        que é erro de programação do chamador.
    """
    if cenario not in ("ATUAL", "POTENCIAL"):
        raise ValueError(f"cenario deve ser 'ATUAL' ou 'POTENCIAL', recebido '{cenario}'")

    dados = carregar_dados_comum()

    problemas = _validar_faixas_de_entrada(analise, dados["criterios_aptidao"])
    if problemas:
        return ResultadoAptidao(
            cenario=cenario, classe="INDETERMINADA", grau_final=None,
            fator_determinante=None, alertas=problemas,
        )

    k_cmolc = analise["k_mehlich1"] / 391.0
    soma_bases = analise["ca"] + analise["mg"] + k_cmolc
    if analise["ctc_ph7"] <= 0:
        return ResultadoAptidao(
            cenario=cenario, classe="INDETERMINADA", grau_final=None,
            fator_determinante=None,
            alertas=["CTC a pH 7,0 igual a zero: V% indefinido (CCAE §5.2)"],
        )
    v_percent = 100.0 * soma_bases / analise["ctc_ph7"]

    manejo = analise.get("sistema_manejo", "convencional")
    if manejo not in _MANEJO_PARA_CONTEXTO:
        return ResultadoAptidao(
            cenario=cenario, classe="INDETERMINADA", grau_final=None, fator_determinante=None,
            alertas=[f"sistema de manejo '{manejo}' não mapeado para um critério de calagem"],
        )
    sistema_manejo, condicao_area = _MANEJO_PARA_CONTEXTO[manejo]

    try:
        analise_solo = AnaliseSolo(
            ph_agua=analise["ph_agua"],
            indice_smp=analise["indice_smp"],
            argila=analise["argila"],
            mo=analise["mo"],
            p=analise["p_mehlich1"],
            k=analise["k_mehlich1"],
            ctc_ph7=analise["ctc_ph7"],
            al=analise["al"],
            ca=analise["ca"],
            mg=analise["mg"],
            v_percent=v_percent,
        )
        contexto = Contexto(
            cultura_id=cultura,
            sistema_manejo=sistema_manejo,
            condicao_area=condicao_area,
            prnt=100.0,
            profundidade_incorporacao_cm=20.0,
        )
    except ValueError as e:
        # V% > 100 cai aqui: é o sintoma de CTC menor que a soma de bases, isto é, de um
        # laudo internamente incoerente. Rejeitar por essa via mantém a coerência química
        # como invariante de AnaliseSolo, sem criar regra nova no motor de aptidão.
        return ResultadoAptidao(
            cenario=cenario, classe="INDETERMINADA", grau_final=None,
            fator_determinante=None, alertas=[str(e)],
        )

    try:
        return avaliar_aptidao(analise_solo, cultura, cenario, contexto, Trace())
    except ErroAptidao as e:
        return ResultadoAptidao(
            cenario=cenario, classe="INDETERMINADA", grau_final=None,
            fator_determinante=None, alertas=[str(e)],
        )


def _derivados(analise: AnaliseSolo, dados: Dict[str, Any]) -> Dict[str, Any]:
    """Valores intermediários que os fatores já consumiram, reunidos para inspeção.

    Recalcular aqui divergiria dos fatores; então cada valor vem exatamente da mesma
    chamada que F1/F2/F3/F5 usam. `classe_ctc` sai de interpretacao_geral.json (baixa/
    media/alta/muito_alta), não das faixas_ctc de interpretacao_k.json (a/b/c/d): são duas
    grades com o mesmo corte numérico e rótulos diferentes, e é a primeira que nomeia a
    classe no laudo.
    """
    return {
        "v_percent": analise.v_percent,
        "m_percent": analise.obter_saturacao_al(),
        "classe_argila": _classe_argila(analise.argila, dados["interpretacao_geral"]),
        "classe_ctc": classificar_faixa(
            analise.ctc_ph7, _atributo_geral(dados["interpretacao_geral"], "ctc_ph7")["faixas"]
        ).upper(),
    }


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
    excluidas = {normalizar_nome_cultura(c) for c in fora_de_escopo.get("culturas", [])}
    if {normalizar_nome_cultura(n) for n in _nomes_candidatos(cultura_id, dados)} & excluidas:
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

    derivados = _derivados(analise, dados)

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
        derivados=derivados,
    )
