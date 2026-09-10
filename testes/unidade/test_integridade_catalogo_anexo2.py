"""
Integridade do catálogo do Anexo 2 (dados/comum/catalogo_anexo2.json).

Trava a concordância entre três transcrições independentes do mesmo dado, feitas
em momentos distintos e por caminhos distintos:

1. o catálogo do Anexo 2 (p. 361-365), transcrito do impresso em 2026-09-10;
2. as listas `culturas` dos grupos de exigência em interpretacao_p.json e
   interpretacao_k.json, transcritas em 2026-09-07 e 2026-09-10;
3. o campo `grupo_exigencia` de cada cultura nos arquivos de adubação por grupo,
   transcrito ao longo de agosto de 2026.

Convergência entre elas é evidência de **correção da transcrição**, não de correção
agronômica dos critérios — a distinção importa e está registrada em docs/VALIDACAO.md.

Estes testes são de leitura: nenhum deles altera dados/.
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from siras.dominio.nomes import normalizar_nome_cultura

RAIZ = Path(__file__).resolve().parents[2]
COMUM = RAIZ / "dados" / "comum"
CULTURAS = RAIZ / "dados" / "culturas"
ESQUEMAS = RAIZ / "siras" / "conhecimento" / "esquemas"

# Nomes usados pelos arquivos de adubação que não têm correspondente individual no
# Anexo 2. Oito são identificadores agregados (o Manual publica uma linha de adubação
# para o conjunto); "berinjela" é divergência de grafia — o Anexo 2 escreve "Beringela",
# e a troca de letra não é normalização ortográfica, precisa de alias declarado.
# Esta lista é o estado congelado: um nome novo aqui é uma lacuna a resolver, não um
# item a acrescentar sem análise.
NAO_RESOLVIDOS_CONHECIDOS = {
    "abobora_abobrinha_moranga",
    "alface_almeirao_chicoria_rucula_salsa",
    "berinjela",
    "beterraba_cenoura",
    "brocolis_couve_flor",
    "melancia_melao",
    "nabo_rabanete",
    "pessegueiro_nectarineira",
}

# As culturas em que o grupo de P difere do de K (Anexo 2). Nenhuma regra deriva um
# do outro; a lista existe para que uma derivação acidental quebre o teste.
DIVERGENCIAS_P_DIFERENTE_K = {
    "arroz_irrigado": (4, 2),
    "batata_doce": (3, 1),
    "gengibre": (2, 3),
    "mandioca": (3, 2),
    "mandioquinha_salsa": (2, 1),
    "tomateiro": (2, 1),
}


def _ler(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def catalogo() -> dict:
    return _ler(COMUM / "catalogo_anexo2.json")


@pytest.fixture(scope="module")
def sinonimos() -> dict:
    """Nome normalizado -> conjunto dos nomes normalizados equivalentes a ele."""
    dados = _ler(COMUM / "aliases_culturas.json")
    indice: dict = {}
    for grupo in dados["grupos_de_sinonimos"]:
        nomes = {normalizar_nome_cultura(nome) for nome in grupo["nomes"]}
        for nome in nomes:
            indice.setdefault(nome, set()).update(nomes)
    return indice


@pytest.fixture(scope="module")
def resolver(catalogo, sinonimos):
    """Devolve o id de catálogo de um nome, ou None se ele não resolver.

    A resolução é ortográfica (nomes.py) mais os sinônimos declarados — a mesma
    precedência que motor/aptidao.py usa, reimplementada aqui de propósito: se o
    teste chamasse o motor, deixaria de ser uma conferência independente.
    """
    por_norma = {normalizar_nome_cultura(sid): sid for sid in catalogo["culturas"]}

    def _resolver(nome: str):
        canonico = normalizar_nome_cultura(nome)
        for candidato in (canonico, *sorted(sinonimos.get(canonico, ()))):
            if candidato in por_norma:
                return por_norma[candidato]
        return None

    return _resolver


def _culturas_com_grupo_exigencia():
    """(arquivo, cultura_id, grupo_exigencia) de todos os arquivos de adubação."""
    for arquivo in sorted(CULTURAS.rglob("*.json")):
        dados = _ler(arquivo)
        culturas = (dados.get("adubacao") or dados).get("culturas")
        if not isinstance(culturas, dict):
            continue
        for cultura_id, entrada in culturas.items():
            grupo = (entrada or {}).get("grupo_exigencia")
            if isinstance(grupo, dict):
                yield arquivo.name, cultura_id, grupo


class TestEstruturaDoCatalogo:
    def test_valida_contra_o_schema(self, catalogo):
        schema = _ler(ESQUEMAS / "catalogo_anexo2_v1.schema.json")
        erros = sorted(Draft202012Validator(schema).iter_errors(catalogo),
                       key=lambda e: list(e.path))
        assert not erros, "\n".join(
            f"{list(e.path)}: {e.message}" for e in erros[:10]
        )

    def test_nao_traz_ph_de_referencia_nem_criterio_de_calagem(self, catalogo):
        """O Anexo 2 fornece somente grupo_p e grupo_k.

        pH de referência é da Tabela 5.1 (ph_referencia.json, 114 culturas) e critério
        de calagem é das Tabelas 5.3 a 5.7 (mapa_culturas.json). Preencher qualquer um
        dos dois aqui criaria uma segunda fonte da verdade, mais pobre que a primeira —
        decisão do autor em 2026-09-10.
        """
        proibidos = {"ph_referencia", "ph_referencia_status", "criterio_calagem"}
        for cultura_id, entrada in catalogo["culturas"].items():
            intrusos = proibidos & set(entrada)
            assert not intrusos, f"{cultura_id} traz campo de outra fonte: {intrusos}"

    def test_divergencias_entre_grupo_p_e_grupo_k(self, catalogo):
        obtido = {
            sid: (c["grupo_p"], c["grupo_k"])
            for sid, c in catalogo["culturas"].items()
            if c["grupo_p"] != c["grupo_k"]
        }
        assert obtido == DIVERGENCIAS_P_DIFERENTE_K


class TestConcordanciaComOsCabecalhos:
    """Tabelas 6.2 e 6.7 nomeiam exaustivamente os Grupos 1 e 4.

    Nenhuma cultura fora dessas listas nominais pode receber esses grupos; toda cultura
    dentro delas tem de receber. É a checagem que o Manual permite fazer sem sair do
    próprio Manual.
    """

    @pytest.mark.parametrize("eixo,arquivo", [("p", "interpretacao_p.json"),
                                              ("k", "interpretacao_k.json")])
    def test_grupos_nominais(self, eixo, arquivo, catalogo, resolver):
        grupos = _ler(COMUM / arquivo)["grupos_exigencia"]
        nominais = {
            int(g["grupo"].split("_")[1]): {
                resolver(nome) for nome in g.get("culturas", [])
            } - {None}
            for g in grupos
            if g["grupo"] in ("grupo_1", "grupo_4")
        }
        for numero, esperados in nominais.items():
            obtidos = {
                sid for sid, c in catalogo["culturas"].items()
                if c[f"grupo_{eixo}"] == numero
            }
            assert obtidos == esperados, (
                f"grupo_{eixo}=={numero}: catálogo tem {sorted(obtidos)}, "
                f"cabeçalho nomeia {sorted(esperados)}"
            )


class TestConcordanciaEntreTranscricoes:
    @pytest.mark.parametrize("eixo,arquivo", [("p", "interpretacao_p.json"),
                                              ("k", "interpretacao_k.json")])
    def test_listas_de_interpretacao(self, eixo, arquivo, catalogo, resolver):
        divergencias = []
        for grupo in _ler(COMUM / arquivo)["grupos_exigencia"]:
            numero = int(grupo["grupo"].split("_")[1])
            for nome in grupo.get("culturas", []):
                sid = resolver(nome)
                if sid is None:
                    divergencias.append(f"{arquivo}: {nome!r} não existe no catálogo")
                    continue
                catalogado = catalogo["culturas"][sid][f"grupo_{eixo}"]
                if catalogado != numero:
                    divergencias.append(
                        f"{arquivo}: {nome!r} está no grupo_{numero}, "
                        f"catálogo diz grupo_{catalogado}"
                    )
        assert not divergencias, "\n".join(divergencias)

    def test_grupo_exigencia_dos_arquivos_de_adubacao(self, catalogo, resolver):
        divergencias = []
        for arquivo, cultura_id, grupo in _culturas_com_grupo_exigencia():
            sid = resolver(cultura_id)
            if sid is None:
                continue  # coberto por test_nomes_nao_resolvidos_sao_os_conhecidos
            for eixo in ("p", "k"):
                if eixo not in grupo:
                    continue
                catalogado = catalogo["culturas"][sid][f"grupo_{eixo}"]
                if grupo[eixo] != catalogado:
                    divergencias.append(
                        f"{arquivo}: {cultura_id!r} declara grupo_{eixo}={grupo[eixo]}, "
                        f"catálogo ({sid}) diz {catalogado}"
                    )
        assert not divergencias, "\n".join(divergencias)

    def test_nomes_nao_resolvidos_sao_os_conhecidos(self, resolver):
        nao_resolvidos = {
            cultura_id
            for _, cultura_id, _ in _culturas_com_grupo_exigencia()
            if resolver(cultura_id) is None
        }
        assert nao_resolvidos == NAO_RESOLVIDOS_CONHECIDOS
