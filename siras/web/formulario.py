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

import re
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

#: Faixa física de cada campo, para validação imediata no navegador.
#:
#: Os números NÃO são escolha da interface: são exatamente os que AnaliseSolo e Contexto
#: já recusam na construção (siras/dominio/analise.py, e a decisão D2 de
#: docs/decisoes/0002 para o índice SMP). Declará-los aqui adianta o erro para o momento
#: da digitação, em vez de esperar o envio — e continua sendo o domínio quem decide,
#: porque a validação do servidor segue sendo a que vale.
FAIXA_DO_CAMPO = {
    "ph_agua": (0, 14), "sub_ph_agua": (0, 14),
    "indice_smp": (3, 8), "sub_indice_smp": (3, 8),
    "v_percent": (0, 100), "sub_v_percent": (0, 100),
    "saturacao_al": (0, 100),
    "prnt": (0, 100),
    "argila": (0, 100),
    "mo": (0, None), "p": (0, None), "k": (0, None), "ctc_ph7": (0, None),
    "al": (0, None), "ca": (0, None), "mg": (0, None),
    "sub_al": (0, None), "sub_ca": (0, None), "sub_mg": (0, None), "sub_k": (0, None),
    "expectativa_rendimento": (0, None),
    "area_ha": (0, None),
}

#: Identificação da ÁREA analisada. Fica visível no formulário, e não recolhida junto
#: dos dados do profissional: propriedade, talhão e área descrevem o que está sendo
#: analisado, e a área tem consequência direta no que o laudo entrega.
CAMPOS_DA_AREA: Tuple[Tuple[Any, ...], ...] = (
    ("propriedade", "Propriedade", None,
     "Nome da fazenda ou do estabelecimento", False, "", "Ex.: Fazenda Santa Rita"),
    # Talhão tem campo próprio, e não dividindo um com a propriedade: são dois níveis
    # diferentes da mesma identificação, e é o talhão que passa a repetir quando a
    # análise cobre mais de uma área.
    ("talhao", "Talhão", None,
     "A área amostrada dentro da propriedade", False, "", "Ex.: A1"),
)

#: Identificação do responsável técnico. NÃO entra em AnaliseSolo nem em Contexto: não
#: é dado da análise nem do cálculo, é metadado do documento. O motor não a conhece, e
#: gerar_laudo() continua sendo função pura de análise, cultura e contexto.
#:
#: Tudo opcional: quem só quer ver a recomendação na tela não precisa se identificar.
#: O último elemento da tupla é o PLACEHOLDER do campo, e não um exemplo a copiar: aqui
#: ele diz que preencher é opcional. Num bloco em que todo campo é dispensável, o rótulo
#: sozinho não informa isso, e o asterisco marca o obrigatório — não o contrário.
CAMPOS_RESPONSAVEL: Tuple[Tuple[Any, ...], ...] = (
    ("responsavel_nome", "Nome do responsável técnico", None,
     "Sai impresso no laudo, acima da linha de assinatura", False, "", "Ex.: Maria Souza"),
    ("responsavel_registro", "Registro profissional", None,
     "CREA, CRT ou outro conselho, com a UF", False, "", "Ex.: CREA-RS 123456"),
    ("responsavel_documento", "CPF ou CNPJ", None, None, False, "", "Ex.: 000.000.000-00"),
)

#: Por que valeria a pena preencher cada campo OPCIONAL.
#:
#: Um campo opcional sem explicação vira um campo ignorado: quem olha a tela rápido pula
#: tudo que não tem asterisco, e perde recurso que o sistema só entrega com o dado em
#: mãos. Cada frase aqui diz o que MUDA no resultado, e não o que o campo significa —
#: significado já é papel do texto de ajuda logo abaixo do campo.
#:
#: Nenhuma delas promete critério agronômico novo: descrevem o que o motor já faz com o
#: valor, e cada uma corresponde a um caminho que existe no código.
MOTIVO_DE_PREENCHER: Dict[str, str] = {
    "area_ha": (
        "Com a área de todos os talhões preenchida, o laudo deixa de dar só a dose por "
        "hectare e passa a somar a quantidade total a comprar — quantas toneladas de "
        "calcário e quantos quilos de adubo a lavoura inteira exige."
    ),
    "saturacao_al": (
        "Informada, o sistema usa a saturação por alumínio medida pelo laboratório. Em "
        "branco, ele a deriva de Al, Ca, Mg e K — o que continua correto, mas é uma "
        "conta a partir de outros valores, e não o dado medido."
    ),
    "expectativa_rendimento": (
        "Algumas culturas recebem um incremento de dose acima de um rendimento de "
        "referência publicado pelo Manual. Sem este campo, a dose fica a da tabela, sem "
        "esse acréscimo."
    ),
    "propriedade": "Sai impressa no cabeçalho do laudo, identificando a que área ele se refere.",
    "talhao": (
        "Sai impresso no cabeçalho do laudo. Passa a ser obrigatório quando a análise "
        "cobre mais de um talhão, para que cada recomendação diga a qual área pertence."
    ),
    "responsavel_nome": (
        "Sai impresso acima da linha de assinatura, e aí basta assinar e carimbar — em "
        "branco, a linha sai vazia para preencher à mão."
    ),
    "responsavel_registro": (
        "Sai impresso junto do nome. É o que dá ao documento validade como peça técnica "
        "assinada por profissional habilitado."
    ),
    "responsavel_documento": "Sai impresso junto do registro, na identificação de quem assina.",

    # As três variáveis condicionais que a base declara como dispensáveis. São opcionais
    # porque só valem em certas fases — e é justamente nessas fases que o motor as exige
    # para conseguir chegar a uma dose.
    "ano": (
        "Na fase de manutenção do pomar, o Manual escalona a dose por ano após o plantio. "
        "Sem este campo, o sistema não consegue emitir a recomendação dessa fase."
    ),
    "produtividade_estimada": (
        "Na fase de manutenção, várias frutíferas têm a dose escalonada por faixa de "
        "produtividade. Sem este campo, o sistema não consegue emitir a recomendação "
        "dessa fase."
    ),
    "momento": (
        "Na fase de plantio e crescimento, as doses de N, P e K mudam conforme o momento "
        "da aplicação. Sem este campo, o sistema não consegue emitir a recomendação "
        "dessa fase."
    ),
}

#: A camada de 10-20 cm inteira tem um motivo só: é um critério de calagem que a lê.
_MOTIVO_DA_SUBSUPERFICIE = (
    "O critério de plantio direto consolidado COM restrições decide pela camada de "
    "10-20 cm (Manual 2016, Tab. 5.3, notas 6-7). Sem ela, esse critério não pode ser "
    "aplicado e resta escolher outro sistema de manejo."
)
for _campo in CAMPOS_SUBSUPERFICIE:
    MOTIVO_DE_PREENCHER.setdefault(_campo[0], _MOTIVO_DA_SUBSUPERFICIE)

_TODOS_OS_CAMPOS = CAMPOS_ACIDEZ + CAMPOS_FERTILIDADE + CAMPOS_SUBSUPERFICIE + CAMPOS_CONTEXTO
_ROTULO_POR_CAMPO = {campo[0]: campo[1] for campo in _TODOS_OS_CAMPOS}

#: O que se repete a cada talhão: só a análise de solo.
#:
#: Cultura, sistema de manejo, PRNT, cultivo, antecedente e expectativa de rendimento
#: são preenchidos uma vez e valem para todos — é o caso real de uma lavoura amostrada em
#: várias áreas, e é o que evita transformar o formulário em vinte campos vezes N.
CAMPOS_DO_TALHAO: Tuple[Tuple[Any, ...], ...] = (
    CAMPOS_ACIDEZ + CAMPOS_FERTILIDADE + CAMPOS_SUBSUPERFICIE
)

#: Área do talhão, em hectares. Opcional, e com uma consequência declarada: o laudo só
#: consolida quantidades a comprar quando TODOS os talhões a informam. Com uma área
#: faltando, a soma seria sobre um conjunto incompleto e diria menos do que aparenta.
CAMPO_AREA: Tuple[Any, ...] = (
    "area_ha", "Área do talhão", "ha",
    "Em hectares, como consta na declaração da área",
    False, "0.1", "12,5",
)


@dataclass
class BlocoDeTalhao:
    """Uma área amostrada: seu nome, sua extensão e a análise que a descreve."""

    rotulo: str
    area_ha: Optional[float]
    analise: AnaliseSolo


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
    #: subconjunto de 'invalidos' que veio de campo de escolha, e não de medida
    invalidos_de_escolha: List[str] = field(default_factory=list)
    #: o que veio do formulário, para devolver a tela preenchida
    valores: Dict[str, str] = field(default_factory=dict)

    @property
    def responsavel(self) -> Dict[str, str]:
        """Identificação do documento, como veio do formulário. Texto livre, e nunca
        entrada de cálculo: o motor não a recebe.

        O documento do responsável é a única exceção ao "como veio": ele sai pontuado, e
        a pontuação é decidida aqui, no servidor. Fazê-la só no navegador deixaria o laudo
        de quem estiver sem JavaScript com onze dígitos corridos.
        """
        identificacao = {
            chave[0]: (self.valores.get(chave[0]) or "").strip()
            for chave in CAMPOS_RESPONSAVEL + CAMPOS_DA_AREA
        }
        identificacao["responsavel_documento"] = formatar_documento(
            identificacao["responsavel_documento"]
        )
        return identificacao

    @property
    def tem_erro_numerico(self) -> bool:
        """Sobrou algum erro que não veio de campo de escolha?

        Separa as duas naturezas porque a tela sugere "confira a unidade no laudo do
        laboratório" — conselho certo para um pH fora de faixa e sem sentido para uma
        cultura antecedente, que não tem unidade e é escolhida de uma lista.

        A conta é por exclusão, e não por campo marcado: as recusas de faixa vêm do
        domínio já formatadas e não nomeiam o campo de volta, então perguntar quais
        campos estão marcados perderia justamente o erro de medida mais comum.
        """
        return len(self.invalidos) > len(self.invalidos_de_escolha)

    @property
    def ok(self) -> bool:
        return self.analise is not None and self.contexto is not None


#: Quantos dígitos cada documento tem, e como ele se escreve.
#:
#: São as máscaras oficiais brasileiras, e não escolha de interface: um CPF escrito
#: 023.883.993-02 e um CNPJ escrito 12.345.678/0001-95 são o que qualquer conferente
#: espera ver num laudo assinado. A chave é a contagem de dígitos, porque é ela que
#: distingue um do outro sem precisar perguntar.
_MASCARA_DO_DOCUMENTO = {
    11: "{0}{1}{2}.{3}{4}{5}.{6}{7}{8}-{9}{10}",
    14: "{0}{1}.{2}{3}{4}.{5}{6}{7}/{8}{9}{10}{11}-{12}{13}",
}


def formatar_documento(bruto: str) -> str:
    """Pontua CPF ou CNPJ pela contagem de dígitos. Devolve o texto intacto se não for
    nem um nem outro.

    Devolver intacto é deliberado: com dez ou doze dígitos não há máscara que sirva, e
    encaixar o número na do CPF à força produziria um documento que parece válido e não
    é. Melhor sair como foi digitado — erro visível é erro corrigível.

    Idempotente: recebe tanto os dígitos corridos quanto o texto já pontuado, porque é
    exatamente isso que volta do formulário depois do primeiro envio.
    """
    digitos = [caractere for caractere in bruto if caractere.isdigit()]
    mascara = _MASCARA_DO_DOCUMENTO.get(len(digitos))
    if mascara is None:
        return bruto.strip()
    return mascara.format(*digitos)


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
    "instalacao": "Instalação",
    "formacao": "Formação",
    "plantio": "No plantio",
    "6_meses": "6 meses após o plantio",
    "14_meses": "14 meses após o plantio",
    "18_meses": "18 meses após o plantio",
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


def _coletar(no: Any, chave: str, achados: List[str]) -> List[str]:
    """Todos os valores de uma lista `chave`, em qualquer profundidade da cultura."""
    if isinstance(no, dict):
        valores = no.get(chave)
        if isinstance(valores, list):
            for valor in valores:
                if isinstance(valor, str) and valor not in achados:
                    achados.append(valor)
        for filho in no.values():
            _coletar(filho, chave, achados)
    elif isinstance(no, list):
        for item in no:
            _coletar(item, chave, achados)
    return achados


def _fases_declaradas(entrada: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fases que a cultura publica em `n.fases` / `pk.fases` (caso do aspargo).

    O Manual nomeia as fases de N e as de P/K de formas diferentes para a mesma cultura —
    'instalacao' num eixo e 'pre_plantio' no outro —, e não é o mesmo eixo de três fases.
    Por isso saem dois campos, exatamente como calcular_adubacao_hortalicas() os recebe:
    unir as duas listas num campo só ofereceria combinações que a tabela não tem.
    """
    campos = []
    for bloco, campo, rotulo in (
        ("n", "fase_n", "Fase — nitrogênio"),
        ("pk", "fase_pk", "Fase — fósforo e potássio"),
    ):
        fases = (entrada.get(bloco) or {}).get("fases")
        if isinstance(fases, list) and fases:
            campos.append({
                "campo": campo,
                "rotulo": rotulo,
                "tipo": "escolha",
                "obrigatorio": True,
                "valores": [(fase, _rotular(fase)) for fase in fases],
                "ajuda": "O Manual publica tabela própria para cada fase desta cultura",
            })
    return campos


def _momentos_declarados(entrada: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Momentos de aplicação dentro da fase (caso da erva-mate, campo `momentos`).

    Os momentos vivem dentro de cada fase, então a lista oferecida é a união das fases.
    Quem recusa uma combinação inválida é a função de adubação, que já nomeia o que
    falta — a tela não repete essa regra.
    """
    momentos = _coletar(entrada, "momentos", [])
    if not momentos:
        return []
    return [{
        "campo": "momento",
        "rotulo": _rotular("momento"),
        "tipo": "escolha",
        "obrigatorio": False,
        "valores": [(momento, _rotular(momento)) for momento in momentos],
        "ajuda": _AJUDA_DE_VARIAVEL.get("momento"),
    }]


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
        # O mirtileiro e o morangueiro declaram na base que crescimento e manutenção são
        # um bloco só. Oferecer "Crescimento" para eles era propor uma opção que o motor
        # recusa sempre — a tela perguntava algo que nunca teria resposta. Quem declara a
        # unificação é a base, e é dela que a tela tira isto.
        if entrada.get("crescimento_e_manutencao_unificados"):
            fases = [fase for fase in fases if fase != "crescimento"]
        if fases:
            variaveis.append({
                "campo": "fase",
                "rotulo": _rotular("fase"),
                "tipo": "escolha",
                "obrigatorio": True,
                "valores": [(fase, _rotular(fase)) for fase in fases],
                "ajuda": _AJUDA_DE_VARIAVEL.get("fase"),
            })

    variaveis.extend(_fases_declaradas(entrada))
    variaveis.extend(_momentos_declarados(entrada))

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


#: Rótulos das antecedentes. O identificador da base é legível, mas "Consorciacao ou
#: pousio" sem acento e com a primeira letra maiúscula é texto de máquina numa tela que
#: o técnico lê. Só tradução de rótulo — a lista de quais existem continua vindo da base.
_ROTULO_DE_ANTECEDENTE = {
    "leguminosa": "Leguminosa",
    "graminea": "Gramínea",
    "consorciacao_ou_pousio": "Consorciação ou pousio",
}


def antecedentes_da_cultura(dados_graos: Dict[str, Any], cultura_id: str) -> List[Tuple[str, str]]:
    """Antecedentes que ESTA cultura aceita, e não a união de todas as de grãos.

    A distinção não é cosmética: o milho aceita 'consorciacao_ou_pousio', e aveia, trigo,
    centeio, cevada e triticale não. Oferecer a união deixava a tela propor uma opção que
    o motor recusa — o usuário escolhia de uma lista legítima e recebia erro.
    """
    entrada = dados_graos["adubacao_n"]["culturas"].get(cultura_id, {})
    return [
        (a, _ROTULO_DE_ANTECEDENTE.get(a, a.replace("_", " ").capitalize()))
        for a in entrada.get("antecedentes") or ()
    ]


def exige_antecedente(dados_graos: Dict[str, Any], cultura_id: str) -> bool:
    """A cultura dosa N cruzando matéria orgânica com a antecedente (modelo
    'mo_x_antecedente')? Então sem antecedente não há dose de N a calcular."""
    entrada = dados_graos["adubacao_n"]["culturas"].get(cultura_id, {})
    return entrada.get("modelo") == "mo_x_antecedente"


#: Sufixo dos campos de um talhão adicional: "ph_agua__2", "talhao__3".
#:
#: O PRIMEIRO talhão mantém os nomes de campo originais, sem sufixo. Não é detalhe de
#: implementação: é o que faz a análise de uma área só continuar exatamente o que já era
#: — a leitura ao vivo, o preenchimento por exemplo e a volta do laudo para a edição
#: seguem funcionando sem saber que talhões múltiplos existem.
_SUFIXO_DE_TALHAO = re.compile(r"__(\d+)$")


def indices_de_talhoes(form: Mapping[str, str]) -> List[int]:
    """Quais talhões adicionais vieram neste envio, em ordem crescente."""
    achados = set()
    for chave in form:
        casou = _SUFIXO_DE_TALHAO.search(chave)
        if casou:
            achados.add(int(casou.group(1)))
    return sorted(achados)


def _analise_de(numeros: Dict[str, Optional[float]]) -> AnaliseSolo:
    return AnaliseSolo(
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


def _ler_talhao_adicional(
    form: Mapping[str, str], indice: int, leitura: LeituraFormulario
) -> Optional[BlocoDeTalhao]:
    """Lê um talhão adicional. Devolve None quando algo o impede, registrando o motivo
    em `leitura` com o número do talhão no rótulo — num formulário com quatro áreas,
    "falta o pH" sem dizer de qual delas não ajuda ninguém."""
    rotulo_bruto = (form.get(f"talhao__{indice}") or "").strip()
    identificacao = rotulo_bruto or f"#{indice}"

    numeros: Dict[str, Optional[float]] = {}
    for campo_id, rotulo, _un, _ajuda, obrigatorio, _passo, _ex in CAMPOS_DO_TALHAO:
        bruto = (form.get(f"{campo_id}__{indice}") or "").strip()
        if not bruto:
            if obrigatorio:
                leitura.faltando.append(f"{rotulo} (talhão {identificacao})")
                leitura.campos_com_erro.append(f"{campo_id}__{indice}")
            numeros[campo_id] = None
            continue
        valor = para_numero(bruto)
        if valor is None:
            leitura.invalidos.append(
                f"{rotulo} (talhão {identificacao}): “{bruto}” não é um número"
            )
            leitura.campos_com_erro.append(f"{campo_id}__{indice}")
        numeros[campo_id] = valor

    area_bruta = (form.get(f"area_ha__{indice}") or "").strip()
    area = para_numero(area_bruta) if area_bruta else None
    if area_bruta and area is None:
        leitura.invalidos.append(
            f"Área do talhão {identificacao}: “{area_bruta}” não é um número"
        )
        leitura.campos_com_erro.append(f"area_ha__{indice}")

    if any(valor is None for campo, valor in numeros.items()
           if campo in {c[0] for c in CAMPOS_DO_TALHAO if c[4]}):
        return None

    try:
        analise = _analise_de(numeros)
    except ValueError as erro:
        leitura.invalidos.append(f"Talhão {identificacao} — {erro}")
        return None

    return BlocoDeTalhao(rotulo=rotulo_bruto, area_ha=area, analise=analise)


def ler_talhoes(
    form: Mapping[str, str],
    dados: Dict[str, Any],
    entradas_do_grupo: Optional[Dict[str, Any]] = None,
) -> Tuple[LeituraFormulario, List[BlocoDeTalhao]]:
    """Lê o formulário inteiro: o contexto compartilhado e um bloco por talhão.

    Com um talhão só, devolve exatamente o que `ler()` sempre devolveu mais um bloco —
    nada no caminho de uma área muda.

    Com mais de um, o nome de cada talhão passa a ser obrigatório: um laudo que traz
    quatro recomendações diferentes e não diz a qual área cada uma pertence é pior que
    não trazê-las.
    """
    leitura = ler(form, dados, entradas_do_grupo)
    indices = indices_de_talhoes(form)

    blocos: List[BlocoDeTalhao] = []
    if leitura.analise is not None:
        area_bruta = (form.get("area_ha") or "").strip()
        area = para_numero(area_bruta) if area_bruta else None
        if area_bruta and area is None:
            leitura.invalidos.append(f"Área do talhão: “{area_bruta}” não é um número")
            leitura.campos_com_erro.append("area_ha")
        blocos.append(
            BlocoDeTalhao(
                rotulo=(form.get("talhao") or "").strip(),
                area_ha=area,
                analise=leitura.analise,
            )
        )

    for indice in indices:
        bloco = _ler_talhao_adicional(form, indice, leitura)
        if bloco is not None:
            blocos.append(bloco)

    if indices:
        for posicao, bloco in enumerate(blocos, start=1):
            if not bloco.rotulo:
                leitura.faltando.append(f"Nome do talhão {posicao}")
                leitura.campos_com_erro.append(
                    "talhao" if posicao == 1 else f"talhao__{indices[posicao - 2]}"
                )

    if leitura.faltando or leitura.invalidos:
        leitura.analise = None
        leitura.contexto = None

    return leitura, blocos


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
        leitura.invalidos_de_escolha.append(leitura.invalidos[-1])
        leitura.campos_com_erro.append("cultura_id")

    criterio_id = (form.get("criterio_id") or "").strip()
    criterios = {identificador: rotulo for identificador, rotulo in opcoes_de_manejo(dados, grupo)}
    if not criterio_id:
        leitura.faltando.append("Sistema de manejo")
        leitura.campos_com_erro.append("criterio_id")
    elif criterio_id not in criterios:
        leitura.invalidos.append(f"Sistema de manejo: “{criterio_id}” não corresponde a nenhum critério")
        leitura.invalidos_de_escolha.append(leitura.invalidos[-1])
        leitura.campos_com_erro.append("criterio_id")

    # A antecedente é obrigatória para as culturas de grãos cujo modelo de N é
    # 'mo_x_antecedente', e inexistente para todas as outras. Validada aqui porque o
    # motor já a exigia: sem isto, deixá-la em branco devolvia a mensagem interna do
    # módulo de adubação à tela, em vez do aviso de campo faltando que todo campo
    # obrigatório recebe.
    if grupo == "graos":
        from siras.conhecimento.carregador import carregar_dados_graos

        dados_graos = carregar_dados_graos()
        antecedente = (form.get("antecedente") or "").strip()
        if exige_antecedente(dados_graos, cultura_id):
            aceitos = dict(antecedentes_da_cultura(dados_graos, cultura_id))
            if not antecedente:
                leitura.faltando.append("Cultura antecedente")
                leitura.campos_com_erro.append("antecedente")
            elif antecedente not in aceitos:
                leitura.invalidos.append(
                    f"Cultura antecedente: esta cultura aceita "
                    f"{', '.join(aceitos.values())}"
                )
                leitura.invalidos_de_escolha.append(leitura.invalidos[-1])
                leitura.campos_com_erro.append("antecedente")

    if leitura.faltando or leitura.invalidos:
        return leitura

    criterio = next(c for c in dados["criterios_calagem"]["criterios"] if c["id"] == criterio_id)

    try:
        leitura.analise = _analise_de(numeros)
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
    "CAMPOS_RESPONSAVEL",
    "FAIXA_DO_CAMPO",
    "CAMPOS_CONTEXTO",
    "CAMPOS_FERTILIDADE",
    "CAMPOS_SUBSUPERFICIE",
    "LeituraFormulario",
    "BlocoDeTalhao",
    "CAMPOS_DA_AREA",
    "CAMPOS_DO_TALHAO",
    "MOTIVO_DE_PREENCHER",
    "CAMPO_AREA",
    "antecedentes_da_cultura",
    "para_numero",
    "culturas_disponiveis",
    "exige_antecedente",
    "formatar_documento",
    "indices_de_talhoes",
    "ler_talhoes",
    "grupo_da_cultura",
    "variaveis_condicionais",
    "ler",
    "opcoes_de_manejo",
]
