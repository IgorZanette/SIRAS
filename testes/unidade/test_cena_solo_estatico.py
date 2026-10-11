"""Testes estáticos da cena 3D: arquivos, offline, contrato e domínio.

Não dependem do Flask nem de navegador: leem os arquivos do repositório.
Um canvas não se testa em pytest; o que importa para o SIRAS (offline, sem
dado inventado, acessibilidade do markup, fallback no lugar) se testa.
"""
import hashlib
import re
import struct
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
STATIC = RAIZ / "siras/web/static"
PARCIAIS = RAIZ / "siras/web/templates/_parciais"
VENDOR = STATIC / "vendor/three/0.160.0"

ARQUIVOS_JS = [
    STATIC / "js/cena-solo.js",
    STATIC / "js/cena-solo/soilScene.js",
    STATIC / "js/cena-solo/stages.js",
]
PARCIAIS_CENA = sorted(PARCIAIS.glob("cena_solo_*.html"))


def ler(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# --------------------------------------------------------------- dependência
def test_three_vendorizado_com_licenca_e_hash_registrado():
    arquivo = VENDOR / "three.module.min.js"
    assert arquivo.is_file()
    assert (VENDOR / "LICENSE").is_file(), "licença do three.js precisa acompanhar o arquivo"
    versao = ler(VENDOR / "VERSAO.txt")
    sha = hashlib.sha256(arquivo.read_bytes()).hexdigest()
    assert sha in versao, "VERSAO.txt deve registrar o SHA-256 do arquivo vendorizado"


def test_peso_do_three_dentro_do_registrado():
    # Se alguém trocar pelo build não minificado (1,2 MiB), o teste avisa.
    assert (VENDOR / "three.module.min.js").stat().st_size < 700 * 1024


# --------------------------------------------------------------- offline
@pytest.mark.parametrize("arquivo", ARQUIVOS_JS + [STATIC / "css/cena-solo.css"] + PARCIAIS_CENA,
                         ids=lambda p: p.name)
def test_nenhuma_url_externa(arquivo):
    assert not re.search(r"https?://", ler(arquivo)), f"{arquivo.name} referencia a rede"


def test_motor_importa_apenas_three_e_estagios():
    imports = re.findall(r"^import .* from ['\"]([^'\"]+)['\"];", ler(STATIC / "js/cena-solo/soilScene.js"), re.M)
    assert sorted(imports) == ["./stages.js", "three"]


def test_import_map_aponta_para_a_pasta_vendorizada():
    cab = ler(PARCIAIS / "cena_solo_cabecalho.html")
    assert '"three"' in cab and "vendor/three/0.160.0/three.module.min.js" in cab


# --------------------------------------------------------------- padrão do projeto
def test_adaptador_e_iife_estrito_sem_exports():
    js = ler(STATIC / "js/cena-solo.js")
    codigo = re.sub(r"/\*.*?\*/", "", js, flags=re.S).strip()
    assert codigo.startswith("(function ()")
    assert '"use strict";' in codigo
    assert not re.search(r"^\s*(export|import)\s", codigo, re.M), "IIFE não usa import/export estáticos"


def test_adaptador_sai_cedo_sem_contener():
    js = ler(STATIC / "js/cena-solo.js")
    assert re.search(r'querySelectorAll\("\[data-cena-solo\]"\);\s*if \(!raizes\.length\) return;', js)


# --------------------------------------------------------------- markup e acessibilidade
@pytest.mark.parametrize("parcial", ["cena_solo_hero.html", "cena_solo_gerando.html"])
def test_contener_decorativo_e_nao_imprime(parcial):
    html = ler(PARCIAIS / parcial)
    tag = re.search(r"<div[^>]*data-cena-solo=[^>]*>", html, re.S).group(0)
    assert 'aria-hidden="true"' in tag
    assert "nao-imprime" in tag


def test_controles_e_legenda_comecam_ocultos():
    # Sem JS ou sem WebGL, eles não fariam sentido: só a imagem estática aparece.
    html = ler(PARCIAIS / "cena_solo_hero.html")
    for marcador in ("data-cena-controles", "data-cena-legenda"):
        tag = re.search(rf"<[^>]*{marcador}[^>]*>", html).group(0)
        assert re.search(r"\shidden(\s|>)", tag), f"{marcador} deve começar com hidden"


def _dimensoes_webp(p: Path):
    dados = p.read_bytes()
    assert dados[:4] == b"RIFF" and dados[8:12] == b"WEBP"
    tipo = dados[12:16]
    if tipo == b"VP8X":
        w = int.from_bytes(dados[24:27], "little") + 1
        h = int.from_bytes(dados[27:30], "little") + 1
    elif tipo == b"VP8L":
        b = struct.unpack("<I", dados[21:25])[0]
        w, h = (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    else:  # VP8
        w, h = struct.unpack("<HH", dados[26:30])
        w, h = w & 0x3FFF, h & 0x3FFF
    return w, h


@pytest.mark.parametrize("parcial", ["cena_solo_hero.html", "cena_solo_gerando.html"])
def test_fallback_existe_e_dimensoes_batem(parcial):
    # width/height corretos reservam o espaço: nada de salto de layout.
    html = ler(PARCIAIS / parcial)
    img = re.search(r"<img[^>]*cena-solo__fallback[^>]*>", html, re.S).group(0)
    nome = re.search(r"filename='([^']+)'", img).group(1)
    arquivo = STATIC / nome
    assert arquivo.is_file(), f"fallback ausente: {nome}"
    w = int(re.search(r'width="(\d+)"', img).group(1))
    h = int(re.search(r'height="(\d+)"', img).group(1))
    assert _dimensoes_webp(arquivo) == (w, h)
    assert 'alt=""' in img


# --------------------------------------------------------------- domínio
UNIDADES = re.compile(r"\d+(?:[.,]\d+)?\s*(?:mg|cmol|g/kg|cm\b|%|dm)", re.I)


@pytest.mark.parametrize("arquivo", PARCIAIS_CENA + [STATIC / "js/cena-solo/stages.js"], ids=lambda p: p.name)
def test_nenhum_numero_agronomico_na_cena(arquivo):
    achados = UNIDADES.findall(ler(arquivo))
    assert not achados, f"valor com unidade em {arquivo.name}: {achados}"


def test_legenda_da_hero_se_declara_ilustrativa():
    html = ler(PARCIAIS / "cena_solo_hero.html")
    assert "exemplo ilustrativo" in html and "sem valores" in html


def test_camadas_sem_rotulo_de_horizonte():
    js = ler(STATIC / "js/cena-solo/stages.js")
    bloco = js[js.index("export const SOIL_LAYERS"):js.index("];", js.index("export const SOIL_LAYERS"))]
    assert not re.search(r"horizonte|\b[ABCER]\s*\+|\bA\d?\b'", bloco)


def test_narrativa_sem_brotos_extras_na_hero():
    # "Aptidão potencial" é o MESMO solo: sem brotar plantas novas.
    js = ler(STATIC / "js/cena-solo/stages.js")
    hero = js[js.index("export const HERO_STAGES"):js.index("export const PROCESSING_STAGES")]
    assert "sprouts: 1" not in hero and "sprouts:1" not in hero


# --------------------------------------------------------------- v3
def _bloco(js: str, inicio: str, fim: str) -> str:
    return js[js.index(inicio):js.index(fim, js.index(inicio))]


def test_espera_nao_muda_a_cor_do_solo():
    # Efeitos mostram a PRÁTICA recomendada; o solo é o mesmo do começo ao fim.
    # Só o fechamento 'dois-cenarios' alterna, via CENARIO_TARGETS.
    js = ler(STATIC / "js/cena-solo/stages.js")
    espera = _bloco(js, "export const PROCESSING_STAGES", "];")
    assert "vitality" not in espera


def test_nenhum_estagio_com_nome_de_horizonte_ou_profundidade():
    js = ler(STATIC / "js/cena-solo/stages.js")
    rotulos = re.findall(r"label: '([^']+)'", js)
    assert rotulos
    for r in rotulos:
        assert not re.search(r"horizonte|profundidade|\bcm\b", r, re.I), r


def test_estado_ausente_nunca_vira_outro():
    js = ler(STATIC / "js/cena-solo/stages.js")
    corpo = _bloco(js, "export function estadoDoAtributo", "}")
    # a primeira regra precisa ser a do ausente (antes de qualquer modo)
    assert corpo.index("'ausente'") < corpo.index("modo ===")


def test_adaptador_recusa_renderizacao_por_software():
    js = ler(STATIC / "js/cena-solo.js")
    assert "isSoftwareRenderer()" in js and "cena-software=1" in js


def test_a_cena_do_formulario_e_cabecalho_da_leitura_e_nao_painel_rival():
    """A D12.2 cortou a cena do formulário; em 11/10/2026 ela voltou, e em outro lugar.

    O corte estava certo pelo motivo que deu: um painel 3D AO LADO dos campos disputaria
    atenção com a leitura ao vivo, que é o elemento de maior valor pedagógico da tela —
    ela mostra a CLASSE de cada valor, com a régua e a tabela do Manual.

    O que mudou foi a posição, não o argumento. Como CABEÇALHO do mesmo painel, as duas
    não disputam: respondem perguntas diferentes, em sequência. A cena diz O QUE JÁ FOI
    INFORMADO — cada atributo preenchido acende o seu ponto no perfil — e as linhas
    abaixo dizem O QUE AQUILO SIGNIFICA. Inventário e depois interpretação.

    Este teste guarda as duas metades: que a cena está dentro do painel da leitura, e
    que ela continua sem interpretar nada."""
    assert (PARCIAIS / "cena_solo_formulario.html").exists()

    # Dentro do painel da leitura ao vivo, e não solta na coluna dos campos.
    dados = ler(RAIZ / "siras/web/templates/dados.html")
    aside = dados[dados.index("<aside"):]
    aside = aside[:aside.index("</aside>")]
    assert "cena_solo_formulario.html" in aside, "a cena saiu do painel de leitura"

    js = ler(STATIC / "js/cena-solo.js")
    # O adaptador mantém a função; ela simplesmente não encontra contêiner nenhum.
    # O que não pode é ela interpretar — isso é papel da leitura ao vivo.
    corpo = _bloco(js, "function seguirFormulario", "/** Tela de espera")
    assert "limitante" not in corpo and "corrigido" not in corpo


def test_planta_generica_declarada_na_espera():
    """É a tela onde a planta cresce, e por isso a que mais se parece com uma promessa
    de safra. A declaração fica junto da cena, não num rodapé."""
    parcial = ler(PARCIAIS / "cena_solo_gerando.html")

    assert "planta é genérica" in parcial
    assert "não representa a sua cultura" in parcial


def test_nenhum_parcial_de_laudo():
    # Escopo: o laudo (tela e impressão) não recebe 3D.
    assert not [p for p in PARCIAIS_CENA if "laudo" in p.name]


def test_pagina_da_defesa_e_autonoma():
    pagina = RAIZ / "defesa/apresentacao.html"
    if not pagina.exists():
        pytest.skip("defesa/ não foi copiada (ela fica fora do repositório)")
    html = ler(pagina)
    assert not re.search(r'(src|href)="https?://', html), "a defesa precisa abrir sem internet"


# --------------------------------------------------------------- v4
def test_cores_npk_sao_identidade_e_montes_iguais_sem_dado():
    js = ler(STATIC / "js/cena-solo/soilScene.js")
    assert "NPK_COR" in js and "setNPK" in js
    # sem dado real, setNPK(null) mostra todos os grânulos (montes iguais)
    corpo = js[js.index("function setNPK"):js.index("}", js.index("function setNPK")) + 200]
    assert "ratio ?" in corpo
    adapt = ler(STATIC / "js/cena-solo.js")
    assert "setNPK(null)" in adapt and "proporção ilustrativa" in adapt


def test_moleculas_sao_so_carbonatos_genericos():
    # CaCO3 e MgCO3 compõem qualquer calcário; o corretivo específico fica no texto.
    js = ler(STATIC / "js/cena-solo/soilScene.js")
    chamadas = re.findall(r"molecule\('(\w+)'", js)
    assert set(chamadas) <= {"Ca", "Mg"} and chamadas
    assert not re.search(r"CaO\b|Ca\(OH\)|CaSO4", js)


def test_potencial_mostra_as_correcoes_como_causa():
    js = ler(STATIC / "js/cena-solo/stages.js")
    hero = js[js.index("id: 'aptidao-potencial'"):js.index("];", js.index("id: 'aptidao-potencial'"))]
    assert "calagem: 1" in hero and "adubacao: 1" in hero
    cen = js[js.index("export const CENARIO_TARGETS"):js.index("};", js.index("export const CENARIO_TARGETS"))]
    assert re.search(r"potencial:.*calagem: 1", cen) and re.search(r"diagnostico:.*calagem: 0", cen)
