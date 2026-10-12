#!/usr/bin/env python3
"""Põe o SIRAS no ar com UM comando, em qualquer máquina.

    python run.py              # ou  py run.py  (Windows)  ou  python3 run.py

É o arquivo que existe para a defesa não depender de nada estar preparado na máquina
onde ela acontece. Ele cria o ambiente virtual, instala as dependências, sobe o servidor
e abre o navegador. Não pede ativação de venv, não pede `make`, não pede `pip` no PATH.

POR QUE UM SCRIPT E NÃO SÓ O MAKEFILE

O `Makefile` ao lado faz o mesmo, e é o atalho de quem já tem `make`. Só que `make` não
vem no Windows, e esta máquina não o tem. Um Makefile sozinho transformaria a
demonstração em "primeiro instale o make" — exatamente o tipo de passo que não se quer
descobrir na frente da banca. Já o Python tem de estar instalado de qualquer jeito, pois
o sistema é escrito nele: usar o próprio Python como instalador não acrescenta
requisito nenhum.

COMO ELE SE REEXECUTA

Na primeira passada ele roda com o Python do sistema, cria `.venv` e instala o que falta.
Depois chama a si mesmo com o Python de DENTRO da venv (`os.execv`), e é essa segunda
passada que importa o Flask e sobe o servidor. O desvio é necessário porque um
interpretador já em execução não enxerga pacotes instalados depois que ele começou.

COMANDOS

    python run.py             sobe o servidor (padrão)
    python run.py testes      bancada rápida
    python run.py completa    bancada completa, as duas camadas
    python run.py validar     confere a base de conhecimento contra os schemas
    python run.py limpar      apaga .venv, caches e saídas geradas
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
IMPLEMENTACAO = RAIZ / "siras"
VENV = RAIZ / ".venv"
REQUISITOS = IMPLEMENTACAO / "requirements.txt"

#: Onde cada sistema operacional põe os executáveis da venv.
_BIN = "Scripts" if os.name == "nt" else "bin"
PYTHON_DA_VENV = VENV / _BIN / ("python.exe" if os.name == "nt" else "python")

#: Marca o que já foi instalado. Comparar com o requirements.txt evita reinstalar a cada
#: execução — a diferença é de segundos, e numa demonstração segundos aparecem.
SELO = VENV / ".requisitos-instalados"

HOSPEDEIRO = "127.0.0.1"
PORTA = 5000


def _versao_minima() -> None:
    if sys.version_info < (3, 12):
        sys.exit(
            f"O SIRAS precisa de Python 3.12 ou mais novo; este é "
            f"{sys.version_info.major}.{sys.version_info.minor}.\n"
            "Instale uma versão atual em https://www.python.org/downloads/ e rode de novo."
        )


def _dentro_da_venv() -> bool:
    """Estamos rodando com o Python da venv do projeto?"""
    try:
        return Path(sys.executable).resolve() == PYTHON_DA_VENV.resolve()
    except OSError:
        return False


def _venv_sadia() -> bool:
    """A venv existe E está íntegra?

    `pyvenv.cfg` é o que o interpretador procura para saber que está num ambiente
    virtual. Sem ele, o python da pasta existe e morre com "failed to locate
    pyvenv.cfg" — um erro que não diz o que fazer.

    Isso acontece de verdade: uma remoção interrompida, por um servidor ainda no ar
    segurando o executável, deixa a casca da pasta para trás. Conferir aqui transforma
    esse caso num recomeço silencioso, em vez de uma mensagem críptica cinco minutos
    antes da defesa.
    """
    return PYTHON_DA_VENV.exists() and (VENV / "pyvenv.cfg").exists()


def _preparar_ambiente() -> None:
    """Cria a venv e instala o que falta. Idempotente, e refaz o que estiver quebrado."""
    if VENV.exists() and not _venv_sadia():
        print(f"[1/2] O ambiente em {VENV.name}/ está incompleto; refazendo ...")
        shutil.rmtree(VENV, ignore_errors=True)
    if not _venv_sadia():
        print(f"[1/2] Criando o ambiente virtual em {VENV.name}/ ...")
        venv.EnvBuilder(with_pip=True, clear=True).create(VENV)
    else:
        print(f"[1/2] Ambiente virtual já existe em {VENV.name}/")

    assinatura = REQUISITOS.read_text(encoding="utf-8")
    if SELO.exists() and SELO.read_text(encoding="utf-8") == assinatura:
        print("[2/2] Dependências já instaladas.")
        return

    print("[2/2] Instalando as dependências ...")
    subprocess.run(
        [str(PYTHON_DA_VENV), "-m", "pip", "install", "--quiet",
         "--disable-pip-version-check", "--upgrade", "pip"],
        check=False,
    )
    concluido = subprocess.run(
        [str(PYTHON_DA_VENV), "-m", "pip", "install", "--quiet",
         "--disable-pip-version-check", "-r", str(REQUISITOS)],
    )
    if concluido.returncode != 0:
        sys.exit("Falha ao instalar as dependências. A saída do pip está acima.")
    SELO.write_text(assinatura, encoding="utf-8")


def _reexecutar_na_venv(argumentos: list[str]) -> None:
    """Troca este processo pelo mesmo script rodando com o Python da venv.

    `execv` substitui o processo em vez de criar um filho: assim Ctrl+C chega direto ao
    servidor, e não sobra um processo pai segurando o terminal.
    """
    os.execv(str(PYTHON_DA_VENV), [str(PYTHON_DA_VENV), str(Path(__file__).resolve()), *argumentos])


# --- as tarefas -------------------------------------------------------------

def servir() -> int:
    """Sobe o servidor e abre o navegador."""
    sys.path.insert(0, str(IMPLEMENTACAO))
    from siras.web import criar_app  # noqa: E402 — só existe depois da venv pronta

    endereco = f"http://{HOSPEDEIRO}:{PORTA}"
    print(f"\n  SIRAS no ar em {endereco}")
    print("  Roda local e offline. Ctrl+C encerra.\n")

    # Só abre o navegador no processo que de fato serve: com o reloader do Flask ligado,
    # o processo pai reinicia o filho a cada alteração e abriria uma aba por vez.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        import threading
        import webbrowser
        threading.Timer(1.2, lambda: webbrowser.open(endereco)).start()

    criar_app().run(host=HOSPEDEIRO, port=PORTA, debug=False)
    return 0


def _pytest(*argumentos: str) -> int:
    return subprocess.run(
        [sys.executable, "-m", "pytest", *argumentos], cwd=IMPLEMENTACAO
    ).returncode


def testes() -> int:
    return _pytest("-q")


def completa() -> int:
    return _pytest("-q", "--completa")


def validar() -> int:
    return subprocess.run(
        [sys.executable, "scripts/valida_base.py"], cwd=IMPLEMENTACAO
    ).returncode


def limpar() -> int:
    """Apaga tudo que é gerado. O próximo `run.py` reconstrói."""
    alvos = [VENV, RAIZ / ".pytest_cache", IMPLEMENTACAO / ".pytest_cache",
             IMPLEMENTACAO / "saida"]
    alvos += list(IMPLEMENTACAO.rglob("__pycache__"))

    resistiram = []
    for alvo in alvos:
        if not alvo.exists():
            continue
        shutil.rmtree(alvo, ignore_errors=True)
        # `ignore_errors` engole a falha, e dar por limpo um alvo meio removido é pior
        # que um erro: quebra o arranque seguinte sem dizer por quê. Conferir custa uma
        # linha, e foi assim que uma venv pela metade apareceu nesta própria máquina.
        if alvo.exists():
            resistiram.append(alvo)
        else:
            print(f"  removido: {alvo.relative_to(RAIZ)}")

    if resistiram:
        print("\nNão consegui remover — algum programa ainda os está usando:")
        for alvo in resistiram:
            print(f"  {alvo.relative_to(RAIZ)}")
        print("Feche o servidor e os terminais que usam o projeto, e rode de novo.")
        return 1

    print("Pronto. Rode `python run.py` para reconstruir.")
    return 0


def ajuda() -> int:
    print(__doc__)
    return 0


TAREFAS = {
    "servir": servir, "run": servir, "": servir,
    "ajuda": ajuda, "help": ajuda, "--help": ajuda, "-h": ajuda,
    "testes": testes, "test": testes,
    "completa": completa,
    "validar": validar,
    "limpar": limpar, "clean": limpar,
}


def main() -> int:
    _versao_minima()
    tarefa = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if tarefa not in TAREFAS:
        print(__doc__)
        return 2

    # Nem `ajuda` nem `limpar` precisam da venv — e `limpar` não pode rodar de dentro
    # da que ela apaga.
    if tarefa in ("ajuda", "help", "--help", "-h"):
        return ajuda()
    # `limpar` não pode rodar de dentro da venv que ela apaga: no Windows os arquivos
    # do interpretador em execução ficam travados e a remoção falha pela metade.
    #
    # A primeira versão deste guard mandava o usuário "rodar com o Python do sistema", e
    # era um conselho ruim: o lançador `py` honra VIRTUAL_ENV, então quem tivesse a venv
    # ativa na shell batia na mensagem mesmo tendo feito exatamente o que ela pedia.
    # `sys.base_prefix` aponta para o interpretador que criou a venv — dá para trocar
    # para ele sozinho, sem pedir nada.
    if tarefa in ("limpar", "clean"):
        if _dentro_da_venv():
            base = Path(sys.base_prefix) / _BIN / ("python.exe" if os.name == "nt" else "python3")
            if not base.exists():
                base = Path(sys.base_prefix) / ("python.exe" if os.name == "nt" else "bin/python3")
            if base.exists():
                os.execv(str(base), [str(base), str(Path(__file__).resolve()), "limpar"])
            sys.exit("Não achei o Python de fora da venv. Apague a pasta .venv/ à mão.")
        return limpar()

    if not _dentro_da_venv():
        _preparar_ambiente()
        _reexecutar_na_venv(sys.argv[1:])  # não retorna

    return TAREFAS[tarefa]()


if __name__ == "__main__":
    raise SystemExit(main())
