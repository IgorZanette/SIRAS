"""
grupo_exigencia() resolve pelo catálogo do Anexo 2 — débito 3 do roadmap.

Os grupos de exigência de P e K foram transcritos três vezes: nos arquivos de adubação por
grupo, nas listas `culturas` de interpretacao_p.json e interpretacao_k.json, e no catálogo
completo do Anexo 2 (catalogo_anexo2.json, 141 culturas). As três concordam integralmente
— test_integridade_catalogo_anexo2.py trava isso. Mesmo assim, `grupo_exigencia()` lia as
listas, que eram PARCIAIS: cobriam só as culturas conferidas até então.

Agora ela lê o catálogo. Este arquivo guarda as duas coisas que a troca não podia fazer:

1. mudar o grupo de alguma cultura que já resolvia — o oráculo é a regra antiga,
   reconstruída das próprias listas, que continuam em dados/;
2. derivar P de K ou K de P — as culturas em que os dois divergem precisam continuar
   divergindo.
"""

import copy
import inspect
import sys
from pathlib import Path

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.nomes import normalizar_nome_cultura
from siras.motor.adubacao import ErroAdubacao, grupo_exigencia
from siras.motor.aptidao import _nomes_candidatos

sys.path.insert(0, str(Path(__file__).parent))
from test_integridade_catalogo_anexo2 import DIVERGENCIAS_P_DIFERENTE_K  # noqa: E402

_DADOS = carregar_dados_comum()
_MAPA = _DADOS["mapa_culturas"]
_CATALOGO = _DADOS["catalogo_anexo2"]


def _pelas_listas_antigas(nome: str, eixo: str):
    """A resolução anterior: lista explícita, depois o fallback de grãos."""
    for grupo in _DADOS["interpretacao_" + eixo]["grupos_exigencia"]:
        if nome in grupo.get("culturas", []):
            return grupo["grupo"]
    entrada = _MAPA["culturas"].get(nome)
    if entrada and entrada.get("grupo") == "graos":
        return "grupo_2"
    return None


def _pelo_catalogo(nome: str, eixo: str):
    """Como os chamadores resolvem: pelas grafias candidatas, a primeira que o catálogo
    conhecer — é o que motor/aptidao.py faz com os nomes do Manual."""
    for candidato in _nomes_candidatos(nome, _DADOS):
        try:
            return grupo_exigencia(candidato, _MAPA, _CATALOGO, eixo)
        except ErroAdubacao:
            continue
    return None


_NOMES = sorted(
    set(_MAPA["culturas"])
    | {
        cultura
        for eixo in "pk"
        for grupo in _DADOS["interpretacao_" + eixo]["grupos_exigencia"]
        for cultura in grupo.get("culturas", [])
    }
)


@pytest.mark.parametrize("eixo", ["p", "k"])
def test_onde_as_listas_resolviam_o_catalogo_da_o_mesmo_grupo(eixo):
    comparados, divergentes = 0, []
    for nome in _NOMES:
        antes = _pelas_listas_antigas(nome, eixo)
        if antes is None:
            continue
        comparados += 1
        agora = _pelo_catalogo(nome, eixo)
        if agora != antes:
            divergentes.append(f"{nome}: listas={antes} catalogo={agora}")

    assert comparados >= 30, "a comparação precisa cobrir as culturas que as listas resolviam"
    assert not divergentes, "a troca de fonte mudou o grupo de: " + "; ".join(divergentes)


#: Grãos do mapa que o Anexo 2 não lista pelo nome, e que por isso dependem do fallback.
#: O arroz de sequeiro é lacuna de transcrição já registrada (test_apresentacao.py). Esta
#: lista é o estado conhecido: um nome novo aqui é um grão que entrou no mapa sem entrar
#: no catálogo, e merece ser visto.
_GRAOS_SO_PELO_FALLBACK = ["arroz_de_sequeiro"]


def test_so_os_graos_conhecidos_dependem_do_fallback():
    no_catalogo = {normalizar_nome_cultura(chave) for chave in _CATALOGO["culturas"]}
    graos = [c for c, e in _MAPA["culturas"].items() if e.get("grupo") == "graos"]

    fora = sorted(c for c in graos if normalizar_nome_cultura(c) not in no_catalogo)
    assert len(graos) == 21
    assert fora == _GRAOS_SO_PELO_FALLBACK


def test_o_grao_fora_do_catalogo_continua_no_grupo_2():
    """O fallback dá o mesmo grupo que a resolução anterior dava."""
    for cultura in _GRAOS_SO_PELO_FALLBACK:
        assert grupo_exigencia(cultura, _MAPA, _CATALOGO, "p") == "grupo_2"
        assert grupo_exigencia(cultura, _MAPA, _CATALOGO, "k") == "grupo_2"


def test_o_fallback_de_graos_continua_valendo():
    """Para o grão que entrar no mapa antes de entrar no catálogo."""
    sem_soja = copy.deepcopy(_CATALOGO)
    del sem_soja["culturas"]["soja"]

    assert grupo_exigencia("soja", _MAPA, sem_soja, "p") == "grupo_2"


@pytest.mark.parametrize("cultura, esperado", sorted(DIVERGENCIAS_P_DIFERENTE_K.items()))
def test_p_e_k_continuam_independentes(cultura, esperado):
    grupo_p, grupo_k = esperado

    assert grupo_exigencia(cultura, _MAPA, _CATALOGO, "p") == f"grupo_{grupo_p}"
    assert grupo_exigencia(cultura, _MAPA, _CATALOGO, "k") == f"grupo_{grupo_k}"


def test_o_nome_do_manual_resolve_pela_forma_normalizada():
    """O catálogo escreve 'acacia_negra'; o Manual, 'acácia-negra'."""
    assert grupo_exigencia("acácia-negra", _MAPA, _CATALOGO, "p") == grupo_exigencia(
        "acacia_negra", _MAPA, _CATALOGO, "p"
    )


def test_cultura_desconhecida_levanta_erro():
    with pytest.raises(ErroAdubacao, match="catalogo_anexo2.json"):
        grupo_exigencia("cultura_inexistente_xyz", _MAPA, _CATALOGO, "p")


def test_eixo_invalido_e_erro_de_programacao():
    with pytest.raises(ValueError):
        grupo_exigencia("soja", _MAPA, _CATALOGO, "n")


def test_a_funcao_nao_le_mais_as_listas():
    """Fonte única quer dizer uma fonte: se as listas voltarem a ser lidas aqui, as duas
    podem divergir em silêncio de novo."""
    codigo = inspect.getsource(grupo_exigencia)

    assert '["grupos_exigencia"]' not in codigo
    assert 'catalogo_anexo2["culturas"]' in codigo
