"""
Preenchimento de exemplo do formulário.

Serve à demonstração, ao teste de usabilidade e à apresentação para a banca: transcrever
à mão dezenove campos por talhão antes de ver qualquer resultado é barreira alta para
quem só quer conhecer o sistema, e no roteiro de usabilidade essa transcrição consome o
tempo da tarefa sem medir nada.

São dez exemplos — sete de talhão único e três de talhões múltiplos (2, 4 e 6 áreas) —, e
o usuário escolhe só entre essas duas naturezas: qual dos exemplos cai é sorteado. Dez em
vez de um porque um exemplo só percorre um caminho do motor, e o conjunto cobre
deliberadamente os caminhos que divergem entre si (ver COBERTURA abaixo).

CADA EXEMPLO TRAZ A PRÓPRIA CULTURA, e é por isso que a escolha fica na tela ANTERIOR, a
da cultura. Enquanto o botão morava na tela de dados, o exemplo tinha de servir a
qualquer uma das 61 culturas, e campo condicional que só uma delas exige — a massa verde
da erva-mate — ficava em branco, porque não há valor único que sirva para todas. Com a
cultura dentro do exemplo, o conjunto dos dez passa a cobrir os seis grupos e a garantia
passa a ser literal: não sobra campo nenhum por preencher, e dá para clicar em "Gerar
laudo" sem digitar nada.

A rota continua aceitando `?cultura_id=<outra>&exemplo=<id>`: aí o exemplo empresta a
análise de solo para a cultura pedida, que é o que as bancadas de `testes/integracao/`
usam para percorrer as 61.

TUDO VEM PREENCHIDO, inclusive o que é opcional: subsuperfície, saturação por alumínio,
área, identificação do responsável, N na semeadura e fórmulas da revenda. A versão
anterior deixava a subsuperfície de fora, pelo argumento de que preenchê-la sugeriria que
toda análise precisa de duas amostragens. O argumento vale para o formulário em branco e
não para o exemplo: quem clica em "preencher com um exemplo" quer ver o que o sistema
entrega quando tem tudo em mãos, e um campo vazio no exemplo é um recurso que nunca
aparece na demonstração.

DE ONDE VEM CADA NÚMERO, e esta separação é a parte que importa:

- a ANÁLISE DE SOLO é um laudo de laboratório de DEMONSTRAÇÃO. São ENTRADAS plausíveis de
  um laboratório do RS, escolhidas para o exemplo exercitar o sistema. Nenhuma delas é
  valor de recomendação, e nenhuma sai de tabela do Manual. A saturação por bases e a
  saturação por alumínio de cada perfil são coerentes com os cátions do mesmo perfil, e
  `testes/unidade/test_exemplo_formulario.py` verifica essa coerência — um laudo de
  demonstração internamente contraditório seria pior que nenhum;
- a PRODUTIVIDADE sai da própria base, sempre que ela a transcreve: o rendimento de
  referência da cultura em grãos, ou o piso da primeira faixa de produtividade nos grupos
  que a publicam. Inventar uma produtividade típica por cultura seria afirmação
  agronômica, e `CLAUDE.md` nomeia "faixas de expectativa de rendimento" entre os valores
  que não se inventam. Onde a base não transcreve, o campo fica em branco;
- o SISTEMA DE MANEJO e as VARIÁVEIS CONDICIONAIS saem da base, pela cultura escolhida.
  Um exemplo pode declarar `criterio_preferido`, que só é usado se a cultura o oferecer;
- as FÓRMULAS da revenda saem de `dados/mercado/formulas_npk.json`, e não de invenção;
- PRNT, N na semeadura, áreas e identificação são escolha da interface: são dados do
  usuário, não do Manual.

IDENTIFICAÇÃO FICTÍCIA. Propriedades, talhões e responsáveis técnicos são inventados, com
nomes deliberadamente incomuns para que ninguém os associe a pessoa ou estabelecimento
real. Os CPFs são sequências de dígito repetido, que a regra de verificação brasileira
rejeita: nenhum deles pode pertencer a alguém.

COBERTURA dos sete perfis de solo, que é o que justifica serem sete:

| Perfil              | Argila | P            | CTC | K           | Calagem                  |
|---------------------|--------|--------------|-----|-------------|--------------------------|
| argiloso-acido      | cl. 1  | baixo        |  b  | medio       | dispara, dose alta       |
| arenoso             | cl. 4  | baixo        |  a  | medio       | dispara, dose baixa      |
| corrigido           | cl. 3  | alto         |  b  | alto        | NÃO dispara (pH acima)   |
| tampao-fraco        | cl. 4  | muito_baixo  |  a  | muito_baixo | equações polinomiais     |
| teor-muito-alto     | cl. 2  | muito_alto   |  c  | muito_alto  | NÃO dispara              |
| aluminio-alto       | cl. 2  | muito_baixo  |  b  | baixo       | dispara, dose muito alta |
| pd-restricoes       | cl. 2  | medio        |  b  | alto        | decide pela subsuperfície|

O exemplo é ponto de partida editável, e não um caso de validação: os casos com oráculo
vivem em `testes/casos/` e continuam sendo o que mede a concordância do sistema.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from siras.dominio.nomes import buscar_por_nome

#: Sete laudos de laboratório de DEMONSTRAÇÃO, cada um percorrendo um caminho diferente
#: do motor (ver a tabela de COBERTURA no topo do módulo). São valores de ENTRADA, do tipo
#: que o técnico transcreve do laudo do laboratório — nenhum sai de tabela do Manual.
#:
#: `v_percent` e `saturacao_al` não são escolhidos à parte: são a saturação por bases e a
#: saturação por alumínio que os próprios cátions do perfil produzem, arredondadas a uma
#: casa. Guardá-las escritas, em vez de calculá-las aqui, deixa o perfil legível de uma
#: olhada; o teste de coerência é que impede as duas versões de divergirem.
PERFIS: Dict[str, Dict[str, str]] = {
    "argiloso-acido": {
        "ph_agua": "5.0", "indice_smp": "5.5", "al": "1.4", "ca": "2.6", "mg": "1.1",
        "v_percent": "35.0", "saturacao_al": "26.3",
        "argila": "64", "mo": "3.4", "p": "5.2", "k": "88", "ctc_ph7": "11.2",
        "sub_ph_agua": "4.8", "sub_indice_smp": "5.3", "sub_v_percent": "28.0",
        "sub_al": "1.9", "sub_ca": "1.8", "sub_mg": "0.7", "sub_k": "62",
    },
    "arenoso": {
        "ph_agua": "5.4", "indice_smp": "5.9", "al": "0.5", "ca": "1.6", "mg": "0.7",
        "v_percent": "43.1", "saturacao_al": "17.2",
        "argila": "14", "mo": "1.8", "p": "12.5", "k": "44", "ctc_ph7": "5.6",
        "sub_ph_agua": "5.2", "sub_indice_smp": "5.7", "sub_v_percent": "38.0",
        "sub_al": "0.8", "sub_ca": "1.1", "sub_mg": "0.5", "sub_k": "31",
    },
    "corrigido": {
        "ph_agua": "6.2", "indice_smp": "6.2", "al": "0.1", "ca": "4.2", "mg": "1.8",
        "v_percent": "64.9", "saturacao_al": "1.5",
        "argila": "38", "mo": "3.1", "p": "24.0", "k": "140", "ctc_ph7": "9.8",
        "sub_ph_agua": "5.9", "sub_indice_smp": "6.0", "sub_v_percent": "58.0",
        "sub_al": "0.2", "sub_ca": "3.4", "sub_mg": "1.4", "sub_k": "98",
    },
    "tampao-fraco": {
        "ph_agua": "5.3", "indice_smp": "6.5", "al": "0.3", "ca": "1.2", "mg": "0.5",
        "v_percent": "41.6", "saturacao_al": "14.7",
        "argila": "11", "mo": "1.2", "p": "9.8", "k": "18", "ctc_ph7": "4.2",
        "sub_ph_agua": "5.1", "sub_indice_smp": "6.4", "sub_v_percent": "36.0",
        "sub_al": "0.5", "sub_ca": "0.9", "sub_mg": "0.3", "sub_k": "14",
    },
    "teor-muito-alto": {
        "ph_agua": "5.9", "indice_smp": "6.1", "al": "0.1", "ca": "5.4", "mg": "2.2",
        "v_percent": "46.5", "saturacao_al": "1.2",
        "argila": "42", "mo": "4.2", "p": "48.0", "k": "300", "ctc_ph7": "18.0",
        "sub_ph_agua": "5.6", "sub_indice_smp": "5.9", "sub_v_percent": "41.0",
        "sub_al": "0.3", "sub_ca": "4.1", "sub_mg": "1.6", "sub_k": "210",
    },
    "aluminio-alto": {
        "ph_agua": "4.7", "indice_smp": "5.1", "al": "2.8", "ca": "1.1", "mg": "0.4",
        "v_percent": "17.0", "saturacao_al": "63.2",
        "argila": "46", "mo": "2.2", "p": "3.4", "k": "52", "ctc_ph7": "9.6",
        "sub_ph_agua": "4.5", "sub_indice_smp": "4.9", "sub_v_percent": "12.0",
        "sub_al": "3.4", "sub_ca": "0.7", "sub_mg": "0.3", "sub_k": "38",
    },
    "pd-restricoes": {
        "ph_agua": "5.6", "indice_smp": "6.0", "al": "0.3", "ca": "3.1", "mg": "1.3",
        "v_percent": "45.0", "saturacao_al": "6.0",
        "argila": "52", "mo": "3.8", "p": "10.5", "k": "110", "ctc_ph7": "10.4",
        "sub_ph_agua": "4.8", "sub_indice_smp": "5.1", "sub_v_percent": "28.0",
        "sub_al": "1.9", "sub_ca": "1.0", "sub_mg": "0.4", "sub_k": "60",
    },
}

#: Os dez exemplos. `talhoes` é a lista de (nome da área, área em ha, id do perfil); o
#: primeiro item é o talhão que ocupa os campos sem sufixo do formulário, e os demais
#: viram cartões "__2", "__3"... (ver siras/web/static/js/talhoes.js).
#:
#: `criterio_preferido` é uma PREFERÊNCIA, e não uma imposição: a lista de manejos
#: depende do grupo da cultura, e o exemplo precisa funcionar para as 61 do escopo. Se a
#: cultura não oferecer aquele critério, vale o primeiro que ela oferece.
EXEMPLOS: Tuple[Dict[str, Any], ...] = (
    # --- talhão único ----------------------------------------------------------------
    {
        "id": "unico-argiloso-acido",
        "tipo": "unico",
        "cultura": "soja",
        "nome": "Soja em solo argiloso ácido",
        "resumo": "Dispara a calagem com dose alta; leguminosa não recebe nitrogênio.",
        "propriedade": "Estância Varaschin",
        "talhoes": (("Coxilha Norte", "42.5", "argiloso-acido"),),
        "responsavel": ("Teobaldo Vunke", "CREA-RS 148207/D", "111.111.111-11"),
        "prnt": "75", "profundidade_incorporacao_cm": "20", "cultivo": "1",
        "n_plantio": "20",
        "formulas": ("05-20-20", "10-30-10", "02-18-18"),
    },
    {
        "id": "unico-arenoso",
        "tipo": "unico",
        "cultura": "milho",
        "nome": "Milho em solo arenoso",
        "resumo": "CTC baixa muda a faixa do potássio; o N depende da cultura antecedente.",
        "propriedade": "Granja Pelzmann",
        "talhoes": (("Areal do Lajeado", "18.0", "arenoso"),),
        "responsavel": ("Hildegard Menck", "CREA-RS 203514/D", "222.222.222-22"),
        "prnt": "85", "profundidade_incorporacao_cm": "20", "cultivo": "1",
        "n_plantio": "15",
        "formulas": ("04-14-08", "10-10-10", "20-05-20"),
    },
    {
        "id": "unico-corrigido",
        "tipo": "unico",
        "cultura": "cebola",
        "nome": "Cebola em solo já corrigido",
        "resumo": "pH acima do gatilho: o laudo em que a calagem NÃO é indicada.",
        "propriedade": "Fazenda Quatro Vertentes",
        "talhoes": (("Várzea Velha", "27.4", "corrigido"),),
        "responsavel": ("Aldrovando Pechtoll", "CREA-RS 176930/D", "333.333.333-33"),
        "prnt": "90", "profundidade_incorporacao_cm": "30", "cultivo": "1",
        "n_plantio": "25",
        "formulas": ("08-28-16", "00-20-30", "15-15-15"),
    },
    {
        "id": "unico-tampao-fraco",
        "tipo": "unico",
        "cultura": "batata",
        "nome": "Batata em solo de baixo poder tampão",
        "resumo": "SMP acima de 6,3: a dose sai das equações polinomiais, não da tabela.",
        "propriedade": "Sítio Oberdan",
        "talhoes": (("Planalto Raso", "9.6", "tampao-fraco"),),
        "responsavel": ("Inácia Rohrbacher", "CRT-RS 09412", "444.444.444-44"),
        "prnt": "70", "profundidade_incorporacao_cm": "20", "cultivo": "1",
        "n_plantio": "12",
        "formulas": ("04-24-12", "09-25-15", "10-20-10"),
    },
    {
        "id": "unico-teor-muito-alto",
        "tipo": "unico",
        "cultura": "trigo",
        "nome": "Trigo em 2º cultivo, teores muito altos",
        "resumo": "P e K na classe Muito alto: a dose vira teto de reposição (ADR 0010).",
        "propriedade": "Estância Krumholz",
        "talhoes": (("Chapadão Leste", "63.0", "teor-muito-alto"),),
        "responsavel": ("Solano Drehmer", "CREA-RS 215688/D", "555.555.555-55"),
        "prnt": "95", "profundidade_incorporacao_cm": "20", "cultivo": "2",
        "n_plantio": "30",
        "formulas": ("20-00-20", "25-00-25", "30-00-12"),
    },
    {
        "id": "unico-aluminio-alto",
        "tipo": "unico",
        "cultura": "amoreira_preta",
        "nome": "Amoreira-preta em solo com alumínio alto",
        "resumo": "Frutífera por ano do pomar, no perfil mais restritivo do conjunto.",
        "propriedade": "Chácara Bergmeier",
        "talhoes": (("Barranco do Fundo", "6.8", "aluminio-alto"),),
        "responsavel": ("Maribel Zottil", "CREA-RS 131042/D", "666.666.666-66"),
        "prnt": "80", "profundidade_incorporacao_cm": "30", "cultivo": "1",
        "n_plantio": "18",
        "formulas": ("02-23-23", "05-25-25", "06-30-06"),
    },
    {
        "id": "unico-plantio-direto",
        "tipo": "unico",
        "cultura": "erva-mate",
        "nome": "Erva-mate em produção",
        "resumo": "Calagem por saturação por bases e dose em função da massa verde colhida.",
        "propriedade": "Fazenda Três Palhadas",
        "talhoes": (("Palhada Antiga", "35.2", "pd-restricoes"),),
        "responsavel": ("Elpídio Krammert", "CREA-SC 198375/D", "777.777.777-77"),
        "prnt": "88", "profundidade_incorporacao_cm": "20", "cultivo": "1",
        "n_plantio": "22",
        "formulas": ("10-28-20", "08-30-10", "04-30-10"),
    },
    # --- talhões múltiplos -------------------------------------------------------------
    {
        "id": "multi-2-talhoes",
        "tipo": "multiplo",
        "cultura": "soja",
        "nome": "Soja em dois talhões",
        "resumo": "Uma área pede calcário e a outra não, no mesmo laudo.",
        "propriedade": "Agropecuária Tschoepke",
        "talhoes": (
            ("Volta do Arroio", "24.0", "argiloso-acido"),
            ("Topo da Coxilha", "31.5", "corrigido"),
        ),
        "responsavel": ("Noemi Fahrendorff", "CREA-RS 162859/D", "888.888.888-88"),
        "prnt": "78", "profundidade_incorporacao_cm": "20", "cultivo": "1",
        "n_plantio": "25",
        "formulas": ("05-20-20", "10-30-20", "00-25-15"),
    },
    {
        "id": "multi-4-talhoes",
        "tipo": "multiplo",
        "cultura": "cana_de_acucar",
        "nome": "Cana-de-açúcar em quatro talhões",
        "resumo": "Quatro solos na mesma propriedade, com o total a comprar somado.",
        "propriedade": "Estância Hollenbach",
        "talhoes": (
            ("Quadra Um", "28.0", "argiloso-acido"),
            ("Quadra Dois", "16.5", "arenoso"),
            ("Quadra Três", "11.2", "aluminio-alto"),
            ("Quadra Quatro", "33.8", "corrigido"),
        ),
        "responsavel": ("Valdomiro Spessani", "CREA-RS 187204/D", "999.999.999-99"),
        "prnt": "92", "profundidade_incorporacao_cm": "20", "cultivo": "1",
        "n_plantio": "20",
        "formulas": ("10-20-10", "23-06-23", "02-18-18"),
    },
    {
        "id": "multi-6-talhoes",
        "tipo": "multiplo",
        "cultura": "milho",
        "nome": "Milho em seis talhões, plantio direto",
        "resumo": "Seis perfis num documento só, e a subsuperfície decidindo a calagem.",
        "propriedade": "Granja Vorndran",
        "talhoes": (
            ("Gleba A", "40.0", "argiloso-acido"),
            ("Gleba B", "22.5", "arenoso"),
            ("Gleba C", "17.0", "corrigido"),
            ("Gleba D", "8.4", "tampao-fraco"),
            ("Gleba E", "51.3", "teor-muito-alto"),
            ("Gleba F", "13.9", "aluminio-alto"),
        ),
        "responsavel": ("Eurides Vonbrack", "CRT-RS 07733", "000.000.000-00"),
        "prnt": "82", "profundidade_incorporacao_cm": "30", "cultivo": "1",
        "criterio_preferido": "graos_pd_com_restricoes",
        "n_plantio": "28",
        "formulas": ("15-15-15", "08-28-16", "20-05-20"),
    },
)

_POR_ID = {exemplo["id"]: exemplo for exemplo in EXEMPLOS}

#: As duas naturezas que a tela oferece. O usuário escolhe entre elas; qual exemplo cai é
#: sorteado, e é isso que faz o botão valer mais de um clique — quem demonstra o sistema
#: duas vezes seguidas vê dois solos diferentes.
TIPOS: Tuple[Dict[str, str], ...] = (
    {
        "id": "unico",
        "nome": "Um talhão",
        "resumo": "Sorteia um entre sete laudos de demonstração, cada um num solo diferente.",
    },
    {
        "id": "multiplo",
        "nome": "Vários talhões",
        "resumo": "Sorteia um entre três exemplos com 2, 4 ou 6 áreas no mesmo laudo.",
    },
)

#: Fallback de quem chama sem escolher — e de quem chama com um id que não existe, como o
#: `exemplo=1` que as bancadas de `testes/integracao/` usam para as 61 culturas.
PADRAO = EXEMPLOS[0]

#: Variáveis condicionais NUMÉRICAS que não são produtividade e não têm valor transcrito
#: na base. São poucas, e cada uma é um dado do produtor — da mesma natureza do PRNT e da
#: área, que a interface já preenche —, e não um valor de tabela do Manual.
#:
#: `massa_verde_t_ha` é a erva-mate comercial colhida, multiplicador direto da dose
#: (§6.6.5: "coeficiente * MV"). O Manual não publica faixa nenhuma de MV, então não há o
#: que transcrever: ou a interface põe um valor de demonstração, ou o exemplo da
#: erva-mate sai com um campo obrigatório em branco e não gera laudo.
#: `ano` é o ano do pomar, e 3 é um ano que existe em todas as tabelas por ano.
VARIAVEIS_DE_DEMONSTRACAO: Dict[str, str] = {
    "massa_verde_t_ha": "18",
    "ano": "3",
}


def escolher(pedido: str, sorteio: Optional[random.Random] = None) -> Dict[str, Any]:
    """O exemplo que corresponde ao que a tela pediu.

    Três formas de pedir, em ordem de precedência: o id de um exemplo (fixa aquele —
    é o que serve a uma apresentação, em que se quer sempre o mesmo caso na tela), o id
    de um tipo (sorteia entre os exemplos daquele tipo), ou qualquer outra coisa (o
    exemplo padrão).
    """
    if pedido in _POR_ID:
        return _POR_ID[pedido]
    do_tipo = [exemplo for exemplo in EXEMPLOS if exemplo["tipo"] == pedido]
    if do_tipo:
        return (sorteio or random).choice(do_tipo)
    return PADRAO


def _numero_para_campo(valor: Any) -> str:
    """Número no formato que um `<input type="number">` ACEITA: com ponto decimal.

    Devolvia vírgula até 11/10/2026, e era o defeito que esvaziava o exemplo inteiro. O
    HTML exige que o `value` de um campo numérico seja um "valid floating-point number",
    cuja gramática só admite ponto; diante de uma vírgula o navegador sanitiza o valor
    para vazio, sem avisar nada. No HTML servido a vírgula estava lá, e por isso a
    verificação pelo servidor não via problema algum — na tela, o campo aparecia em
    branco e o envio era barrado por campo obrigatório não preenchido.

    Só o `value` precisa do ponto. O texto que o laudo imprime continua com vírgula, pelo
    `formatar_numero` de siras/relatorio/apresentacao.py, e quem digita vírgula na tela
    continua sendo entendido: `para_numero` em siras/web/formulario.py troca uma pela
    outra na leitura.
    """
    if valor is None:
        return ""
    return f"{float(valor):g}"


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


def _criterio(exemplo: Dict[str, Any], manejos: Sequence[Any]) -> Optional[str]:
    """O manejo que o exemplo prefere, se a cultura o oferecer; senão o primeiro dela."""
    if not manejos:
        return None
    oferecidos = [identificador for identificador, *_ in manejos]
    preferido = exemplo.get("criterio_preferido")
    if preferido in oferecidos:
        return preferido
    return oferecidos[0]


def montar(
    cultura_id: str,
    grupo: str,
    dados: Dict[str, Any],
    manejos: List[Any],
    variaveis: List[Dict[str, Any]],
    entradas_do_grupo: Optional[Dict[str, Any]] = None,
    exemplo: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Os campos do formulário preenchidos por este exemplo, para esta cultura.

    Devolve o dicionário achatado que a tela consome, já com os sufixos "__2", "__3"...
    dos talhões adicionais. Quem decide QUAL exemplo é `escolher()`; aqui ele chega
    escolhido, para que a tela e os testes possam fixar um sem passar pelo sorteio.
    """
    exemplo = exemplo or PADRAO
    valores: Dict[str, str] = {"cultura_id": cultura_id}

    talhoes = exemplo["talhoes"]
    for ordem, (nome, area, perfil_id) in enumerate(talhoes):
        # O primeiro talhão ocupa os campos sem sufixo: é o que faz a análise de uma área
        # só continuar sendo exatamente o que sempre foi (siras/web/static/js/talhoes.js).
        sufixo = "" if ordem == 0 else f"__{ordem + 1}"
        valores[f"talhao{sufixo}"] = nome
        valores[f"area_ha{sufixo}"] = area
        for campo, valor in PERFIS[perfil_id].items():
            valores[f"{campo}{sufixo}"] = valor

    valores["propriedade"] = exemplo["propriedade"]
    nome, registro, documento = exemplo["responsavel"]
    valores["responsavel_nome"] = nome
    valores["responsavel_registro"] = registro
    valores["responsavel_documento"] = documento

    valores["prnt"] = exemplo["prnt"]
    valores["profundidade_incorporacao_cm"] = exemplo["profundidade_incorporacao_cm"]
    valores["n_plantio"] = exemplo["n_plantio"]
    # As três caixas de fórmula compartilham o name `formula_usuario` e chegam ao servidor
    # como LISTA (ver o macro campo_texto). O template as lê por posição desta lista, e
    # não por `formula_usuario_1`: escrever as chaves numeradas deixava as três em branco.
    valores["formula_usuario"] = list(exemplo["formulas"])

    criterio = _criterio(exemplo, manejos)
    if criterio:
        valores["criterio_id"] = criterio

    if grupo == "graos":
        valores["cultivo"] = exemplo["cultivo"]

        # Sete culturas de grãos dosam N por matéria orgânica CRUZADA com a antecedente, e
        # sem ela o motor recusa. A lista de antecedentes válidas é declarada na própria
        # cultura, então o exemplo pega a primeira em vez de escolher uma por fora.
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
        elif variavel["tipo"] == "numero":
            # Primeiro o que a base transcreve para a cultura; só o que ela não transcreve
            # cai no valor de demonstração, e a lista desses é curta e declarada.
            if campo in VARIAVEIS_DE_DEMONSTRACAO:
                valores[campo] = VARIAVEIS_DE_DEMONSTRACAO[campo]
            elif produtividade is not None:
                valores[campo] = _numero_para_campo(produtividade)

    return valores


__all__ = ["EXEMPLOS", "PADRAO", "PERFIS", "TIPOS",
           "VARIAVEIS_DE_DEMONSTRACAO", "escolher", "montar"]
