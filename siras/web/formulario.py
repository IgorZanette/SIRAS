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
from siras.dominio.nomes import buscar_por_nome

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


def para_numero(texto) -> Optional[float]:
    """Converte aceitando vírgula decimal. Um laudo brasileiro imprime '5,4'.

    Pública porque a leitura ao vivo recebe os mesmos textos por JSON e precisa
    convertê-los do mesmo jeito — inclusive aceitando a vírgula.
    """
    if texto is None:
        return None
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


#: Os seis grupos do escopo, na ordem em que as seções aparecem no Capítulo 6 do Manual.
#: (chave em mapa_culturas.json, ícone do sprite, nome de tela, o que caracteriza o grupo)
GRUPOS = (
    ("graos", "graos", "Culturas de grãos",
     "Seção 6.1. Dose de N pela matéria orgânica; P e K por correção mais manutenção."),
    ("hortalicas", "hortalicas", "Hortaliças",
     "Seção 6.3. Dose publicada por classe de teor. Só o aspargo tem pH de referência próprio."),
    ("tuberculos", "tuberculos", "Tubérculos",
     "Seção 6.3. Batata e batata-doce, com tabela completa de N, P e K."),
    ("frutiferas", "frutiferas", "Frutíferas",
     "Seção 6.5. A recomendação muda com a fase do pomar, que o sistema pergunta adiante."),
    ("erva_mate", "erva", "Erva-mate",
     "Seção 6.6.5. Sem pH de referência: a calagem só supre cálcio e magnésio."),
    ("outras", "comerciais", "Outras comerciais",
     "Seções 6.6.1 e 6.6.2. Cana-de-açúcar e tabaco, com calagem indicada abaixo de pH 5,5."),
)


def grupos_com_culturas(dados: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Os seis grupos com as culturas de cada um, para a tela de escolha."""
    return [
        {
            "id": identificador,
            "icone": icone,
            "nome": nome,
            "descricao": descricao,
            "culturas": culturas_disponiveis(dados, identificador),
        }
        for identificador, icone, nome, descricao in GRUPOS
    ]


#: Fases de adubação das frutíferas (Seção 6.5 do Manual). São nomes de seção, não
#: valores agronômicos; quais delas existem para cada espécie sai do próprio arquivo.
_FASES_DE_FRUTIFERA = ("pre_plantio", "crescimento", "manutencao")

#: Rótulo de tela dos identificadores das variáveis condicionais.
_ROTULO_DE_VARIAVEL = {
    "fase": "Fase do pomar",
    "programa": "Programa de adubação",
    "momento": "Momento da aplicação",
    "manejo_galho_grosso": "Manejo do galho grosso",
    "tipo_uva": "Tipo de uva",
    "ciclo": "Ciclo da cana",
    "tipo": "Tipo cultivado",
    "ano": "Ano após o plantio",
    "produtividade_estimada": "Produtividade estimada",
    "produtividade_t_ha": "Produtividade estimada",
    "massa_verde_t_ha": "Massa verde colhida",
}

#: Variáveis numéricas que as funções de adubação aceitam além das declaradas em
#: `variavel_adicional`. São nomes de parâmetro, e a obrigatoriedade de cada uma depende
#: da fase — quem sabe disso é a função do grupo, que já nomeia a que faltar.
_NUMERICAS_POR_GRUPO = {
    "frutiferas": (("ano", None), ("produtividade_estimada", "t/ha")),
    "outras": (("produtividade_t_ha", "t/ha"),),
    "erva_mate": (("massa_verde_t_ha", "t/ha"),),
}

#: Rótulo de tela dos valores das variáveis condicionais. São traduções do próprio
#: identificador transcrito ('manejo_1_retido' -> "galho grosso retido"), nunca afirmação
#: agronômica acrescentada: o que cada manejo faz com a dose está na base, não aqui.
_ROTULO_DE_VALOR = {
    "desde_o_plantio": "Desde o plantio",
    "recuperacao": "Recuperação de erval",
    "plantio_e_crescimento": "Plantio e crescimento",
    "formacao_da_copa": "Formação da copa",
    "producao": "Produção",
    "manejo_1_retido": "Manejo 1 — galho grosso retido",
    "manejo_2_retirado": "Manejo 2 — galho grosso retirado",
    "pre_plantio": "Pré-plantio",
    "crescimento": "Crescimento",
    "manutencao": "Manutenção",
    "cana_planta": "Cana-planta",
    "cana_soca": "Cana-soca",
    "virginia": "Virgínia",
    "burley": "Burley",
    "vinho": "Uva para vinho",
    "mesa": "Uva de mesa",
    "leguminosa": "Leguminosa",
    "graminea": "Gramínea",
    "consorciacao_ou_pousio": "Consorciação ou pousio",
}

_UNIDADE_DE_VARIAVEL = {
    "massa_verde_t_ha": "t/ha",
    "produtividade_t_ha": "t/ha",
    "produtividade_estimada": "t/ha",
}

#: Ajuda das variáveis que a base não descreve. Cada frase diz de onde o número vem —
#: nenhuma delas está no laudo do laboratório, e sem isso o técnico precisa adivinhar
#: se informa histórico, meta ou média.
_AJUDA_DE_VARIAVEL = {
    "fase": "Etapa do pomar: o Manual publica tabela própria para cada uma",
    "programa": "Erval novo segue o programa desde o plantio; erval degradado, o de recuperação",
    "momento": "Momento da aplicação dentro da fase",
    "manejo_galho_grosso": "O galho grosso retirado da área exporta nutrientes e eleva a dose",
    "tipo_uva": "A correspondência entre solo e tecido difere entre uva de vinho e de mesa",
    "ciclo": "Cana-planta é o primeiro ciclo; cana-soca, a rebrota",
    "tipo": "Virgínia e Burley têm tabelas de adubação distintas",
    "ano": "Anos completos desde o plantio do pomar",
    "produtividade_estimada": "Média das últimas safras da área, não a meta",
    "produtividade_t_ha": "Média das últimas safras da área, não a meta",
    "massa_verde_t_ha": "Massa verde comercial colhida por hectare",
}


def _rotular(identificador: str) -> str:
    """Rótulo de tela de um identificador, seja campo ou valor."""
    if identificador in _ROTULO_DE_VARIAVEL:
        return _ROTULO_DE_VARIAVEL[identificador]
    if identificador in _ROTULO_DE_VALOR:
        return _ROTULO_DE_VALOR[identificador]
    return identificador.replace("_", " ").capitalize()


def variaveis_condicionais(
    cultura_id: str, grupo: str, entradas: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Campos que existem só para certas culturas (PLANO-FRONTEND §9.2).

    Quem planta soja nunca vê "fase do pomar", e a macieira sempre vê — não por uma lista
    escrita no template, mas porque a base declara, em `variavel_adicional`, qual campo
    cada cultura exige e com que valores. Videira declara `tipo_uva`, cana declara
    `ciclo`, tabaco declara `tipo`, erva-mate declara quatro. Acrescentar uma cultura com
    variável nova na base faz a tela ganhar o campo sem uma linha de código.

    As fases das frutíferas são a exceção: não vêm declaradas, e saem das chaves de fase
    presentes na própria cultura.
    """
    entrada = buscar_por_nome(entradas, cultura_id) if entradas else None
    if not entrada:
        return []

    variaveis: List[Dict[str, Any]] = []

    if grupo == "frutiferas":
        fases = [fase for fase in _FASES_DE_FRUTIFERA if fase in entrada]
        if fases:
            variaveis.append({
                "campo": "fase",
                "rotulo": _rotular("fase"),
                "tipo": "escolha",
                "obrigatorio": True,
                "valores": [(fase, _rotular(fase)) for fase in fases],
                "ajuda": _AJUDA_DE_VARIAVEL.get("fase"),
            })

    declaradas = entrada.get("variavel_adicional") or []
    if isinstance(declaradas, dict):
        declaradas = [declaradas]
    for declarada in declaradas:
        valores = declarada.get("valores") or ()
        # O tipo vem da base quando ela o declara, e só então se presume escolha pela
        # presença de valores. Forçar tudo a escolha transformava a massa verde da
        # erva-mate — que a base declara como número — numa lista sem nenhuma opção:
        # obrigatória, vazia e impossível de preencher.
        tipo = declarada.get("tipo") or ("escolha" if valores else "numero")
        variaveis.append({
            "campo": declarada["campo"],
            "rotulo": _rotular(declarada["campo"]),
            "tipo": tipo,
            "obrigatorio": bool(declarada.get("obrigatorio")),
            "valores": [(valor, _rotular(valor)) for valor in valores],
            "condicao": declarada.get("condicao"),
            # A base já explica o que a variável significa. Essa frase é transcrição, e
            # é melhor ajuda do que qualquer texto que a interface inventasse.
            "ajuda": declarada.get("descricao") or _AJUDA_DE_VARIAVEL.get(declarada["campo"]),
            "unidade": _UNIDADE_DE_VARIAVEL.get(declarada["campo"]),
        })

    ja_declaradas = {variavel["campo"] for variavel in variaveis}
    for campo, unidade in _NUMERICAS_POR_GRUPO.get(grupo, ()):
        # Sem esta guarda o campo aparecia duas vezes lado a lado quando a base já o
        # declarava — foi o que aconteceu com a massa verde da erva-mate.
        if campo in ja_declaradas:
            continue
        variaveis.append({
            "campo": campo,
            "rotulo": _rotular(campo),
            "tipo": "numero",
            "obrigatorio": False,
            "unidade": unidade,
            "ajuda": _AJUDA_DE_VARIAVEL.get(campo),
        })

    return variaveis


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


def grupo_da_cultura(cultura_id: str, dados: Dict[str, Any]) -> str:
    """Grupo da cultura em mapa_culturas.json, ou string vazia se não houver."""
    return dados["mapa_culturas"]["culturas"].get(cultura_id, {}).get("grupo", "")


def _ler_variaveis(
    form: Mapping[str, str],
    cultura_id: str,
    grupo: str,
    entradas_do_grupo: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Recolhe do formulário só as variáveis condicionais que esta cultura declara.

    Filtrar pelo que a cultura declara, em vez de aceitar qualquer campo que venha no
    POST, impede que um valor colado de outra cultura (um 'ciclo' sobrando de uma escolha
    anterior) chegue à função de adubação e mude a dose sem aparecer na tela.
    """
    recolhidas: Dict[str, Any] = {}
    for variavel in variaveis_condicionais(cultura_id, grupo, entradas_do_grupo):
        bruto = (form.get(variavel["campo"]) or "").strip()
        if not bruto:
            continue
        if variavel["tipo"] == "numero":
            numero = para_numero(bruto)
            if numero is not None:
                recolhidas[variavel["campo"]] = (
                    int(numero) if variavel["campo"] == "ano" else numero
                )
        else:
            recolhidas[variavel["campo"]] = bruto
    return recolhidas


def ler(
    form: Mapping[str, str],
    dados: Dict[str, Any],
    entradas_do_grupo: Optional[Dict[str, Any]] = None,
) -> LeituraFormulario:
    """Lê o formulário e devolve AnaliseSolo + Contexto, ou o que impediu.

    Coleta TODOS os campos em branco antes de desistir, em vez de parar no primeiro: o
    técnico corrige uma vez, não onze.

    `entradas_do_grupo` são as culturas transcritas na adubação do grupo, usadas para
    saber quais variáveis condicionais esta cultura exige.
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
        valor = para_numero(bruto)
        if valor is None:
            leitura.invalidos.append(f"{rotulo}: “{bruto}” não é um número")
            leitura.campos_com_erro.append(campo_id)
        numeros[campo_id] = valor

    cultura_id = (form.get("cultura_id") or "").strip()
    grupo = grupo_da_cultura(cultura_id, dados)
    validas = {identificador for identificador, _ in culturas_disponiveis(dados, grupo)}
    if not cultura_id:
        leitura.faltando.append("Cultura")
        leitura.campos_com_erro.append("cultura_id")
    elif cultura_id not in validas:
        leitura.invalidos.append(
            f"Cultura: “{cultura_id}” não está no catálogo de culturas do escopo"
        )
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
            variaveis=_ler_variaveis(form, cultura_id, grupo, entradas_do_grupo),
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
    "para_numero",
    "culturas_disponiveis",
    "culturas_que_exigem_antecedente",
    "grupo_da_cultura",
    "variaveis_condicionais",
    "ler",
    "opcoes_de_manejo",
]
