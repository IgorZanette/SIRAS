#!/usr/bin/env python3
"""Põe o SIRAS no ar com um comando.

    py run.py              Windows
    python3 run.py         Linux e macOS

Cria a venv, instala as dependências, sobe o servidor e abre o navegador. Não pede
ativação de venv nem `make` — que não vem instalado no Windows.

    py run.py              sobe o servidor
    py run.py testes       bancada rápida
    py run.py completa     bancada completa
    py run.py validar      confere a base de conhecimento contra os schemas
    py run.py parar        encerra o servidor (quando o Ctrl+C não chega)
    py run.py limpar       apaga .venv, caches e saídas geradas
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import venv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
IMPLEMENTACAO = RAIZ / "siras"
VENV = RAIZ / ".venv"
REQUISITOS = IMPLEMENTACAO / "requirements.txt"

#: Onde cada sistema põe os executáveis da venv.
_BIN = "Scripts" if os.name == "nt" else "bin"
PYTHON_DA_VENV = VENV / _BIN / ("python.exe" if os.name == "nt" else "python")

#: Assinatura do requirements.txt já instalado: evita reinstalar a cada execução.
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


def _venv_sadia() -> bool:
    """A venv existe e está íntegra?

    Sem `pyvenv.cfg` o python da pasta existe e morre com "failed to locate
    pyvenv.cfg". Acontece quando uma remoção é interrompida — um servidor no ar
    segurando o executável deixa a casca da pasta. Conferir aqui refaz em silêncio.
    """
    return PYTHON_DA_VENV.exists() and (VENV / "pyvenv.cfg").exists()


def _site_packages() -> Path:
    """Onde a venv guarda os pacotes instalados."""
    if os.name == "nt":
        return VENV / "Lib" / "site-packages"
    return next((VENV / "lib").glob("python*/site-packages"))


def _ativar() -> None:
    """Usa os pacotes da venv NESTE processo, em vez de reexecutar noutro.

    É a correção do Ctrl+C, e vale explicar porque não é óbvia.

    A versão anterior fazia `os.execv` para `.venv/Scripts/python.exe`. Esse
    executável não é o interpretador: é o **venvlauncher** do Windows, que lança o
    Python real como processo FILHO. Medido nesta máquina com um script que só dorme:
    pelo python do sistema, um processo; pelo da venv, dois. O terminal controla o
    launcher, e o servidor vive no filho — e um Ctrl+C que não alcança o filho devolve
    o prompt deixando a página no ar, que foi exatamente o relato.

    Pôr o `site-packages` da venv no `sys.path` resolve pela raiz: um processo só, o
    mesmo que o terminal controla. O interpretador é o que criou a venv, então a versão
    e a ABI batem com as rodas instaladas lá.

    `PYTHONPATH` acompanha para os processos filhos legítimos — o pytest das tarefas de
    teste, que precisa enxergar os mesmos pacotes.
    """
    pacotes = str(_site_packages())
    if pacotes not in sys.path:
        sys.path.insert(0, pacotes)
    anterior = os.environ.get("PYTHONPATH", "")
    if pacotes not in anterior.split(os.pathsep):
        os.environ["PYTHONPATH"] = pacotes + (os.pathsep + anterior if anterior else "")
    os.environ["VIRTUAL_ENV"] = str(VENV)


def _preparar_ambiente() -> None:
    """Cria a venv e instala o que falta. Idempotente, e refaz o que estiver quebrado."""
    if VENV.exists() and not _venv_sadia():
        print(f"[1/2] O ambiente em {VENV.name}/ está incompleto; refazendo ...")
        shutil.rmtree(VENV, ignore_errors=True)
    if not _venv_sadia():
        print(f"[1/2] Criando o ambiente virtual em {VENV.name}/ ...")
        try:
            venv.EnvBuilder(with_pip=True, clear=True).create(VENV)
        except OSError as erro:
            # Acontece de verdade: um servidor esquecido no ar segura o executável da
            # venv e o `clear` falha no meio. Sem esta mensagem o usuário recebe um
            # traceback de dentro da biblioteca padrão, que não diz o que fazer.
            sys.exit(
                f"Não consegui preparar {VENV.name}/: {erro}\n"
                "Normalmente é um servidor do SIRAS ainda rodando. Feche-o e tente de novo."
            )
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


# --- as tarefas -------------------------------------------------------------

def _encerrar(_sinal=None, _quadro=None) -> None:
    """Sai na hora, sem esperar thread nenhuma.

    `os._exit` pula o encerramento ordenado do interpretador — e é esse o ponto. Um
    servidor local não tem nada a gravar, e qualquer thread ainda viva aqui só serviria
    para atrasar a saída que o usuário acabou de pedir.
    """
    print("\n  Encerrado.")
    sys.stdout.flush()
    os._exit(0)


def servir() -> int:
    """Sobe o servidor e abre o navegador."""
    sys.path.insert(0, str(IMPLEMENTACAO))
    from siras.web import criar_app  # noqa: E402 — só existe depois da venv pronta

    # Ctrl+C precisa encerrar na primeira vez. Duas coisas o impediam:
    #
    #  1. O `threading.Timer` abaixo nasce NÃO-daemon, e uma thread não-daemon pendente
    #     segura o interpretador mesmo depois de a main sair — medido: o processo
    #     sobrevivia ao KeyboardInterrupt e ao sys.exit(0). Agora é daemon.
    #  2. Mesmo sem ela, depender de o KeyboardInterrupt subir limpo pela pilha do
    #     Werkzeug deixa a saída à mercê de qualquer thread que o servidor tenha criado.
    #     O handler explícito tira isso do caminho.
    signal.signal(signal.SIGINT, _encerrar)
    if hasattr(signal, "SIGBREAK"):  # Windows: Ctrl+Break
        signal.signal(signal.SIGBREAK, _encerrar)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _encerrar)

    endereco = f"http://{HOSPEDEIRO}:{PORTA}"
    print(f"\n  SIRAS no ar em {endereco}")
    print("  Roda local e offline. Ctrl+C encerra;")
    print("  se o terminal não encerrar, rode noutra janela:  py run.py parar\n")

    # Só no processo que de fato serve: com o reloader ligado, o pai abriria uma aba
    # a cada reinício.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        import threading
        import webbrowser
        abrir = threading.Timer(1.2, lambda: webbrowser.open(endereco))
        abrir.daemon = True
        abrir.start()

    try:
        # `use_reloader=False` explicito, e nao herdado de `debug`: o reloader forka um
        # processo filho, e dois processos com o mesmo nome e a mesma linha de comando
        # sao o que sobra no gerenciador de tarefas quando algo falha em encerrar.
        # Recarregar ao editar nao serve a quem so quer usar o sistema.
        criar_app().run(host=HOSPEDEIRO, port=PORTA, debug=False,
                        use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        _encerrar()
    return 0


def parar() -> int:
    """Encerra o servidor sem depender de o terminal entregar o Ctrl+C.

    Existe porque o Ctrl+C nem sempre chega. No Git Bash (MinTTY) o sinal costuma não
    ser entregue a programas nativos do Windows, e um terminal que herdou "ignorar
    Ctrl+C" repassa esse estado a tudo que lança. Em nenhum desses casos há correção
    possível do lado do Python — o processo simplesmente nunca é avisado.

    Então aqui não se pede nada ao processo: acha-se quem está escutando na porta e
    encerra-se. Funciona em qualquer terminal, e é o que destrava a demonstração.
    """
    achados = _quem_escuta(PORTA)
    if not achados:
        print(f"  Nada escutando na porta {PORTA}.")
        return 0
    for pid in achados:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                               capture_output=True, check=False)
            else:
                os.kill(pid, signal.SIGTERM)
            print(f"  Encerrado o processo {pid}.")
        except OSError as erro:
            print(f"  Não consegui encerrar {pid}: {erro}")
            return 1
    return 0


def _quem_escuta(porta: int) -> list[int]:
    """PIDs escutando na porta, por `netstat` — sem dependência externa."""
    try:
        saida = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
    except OSError:
        return []
    pids = []
    for linha in saida.splitlines():
        partes = linha.split()
        if len(partes) >= 5 and partes[0].upper().startswith("TCP") \
                and partes[1].endswith(f":{porta}") and "LISTEN" in partes[3].upper():
            try:
                pids.append(int(partes[-1]))
            except ValueError:
                pass
    return sorted(set(pids))


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
        # `ignore_errors` engole a falha, e dar por limpo um alvo meio removido quebra
        # o arranque seguinte sem dizer por quê.
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
    "parar": parar, "stop": parar,
}


def main() -> int:
    _versao_minima()
    tarefa = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if tarefa not in TAREFAS:
        print(__doc__)
        return 2

    # `ajuda` e `limpar` não precisam da venv — e `limpar` apaga justamente a pasta
    # cujos pacotes `_ativar()` colocaria no caminho.
    if tarefa in ("ajuda", "help", "--help", "-h"):
        return ajuda()
    if tarefa in ("limpar", "clean"):
        return limpar()
    if tarefa in ("parar", "stop"):
        return parar()
    _preparar_ambiente()
    _ativar()

    return TAREFAS[tarefa]()


if __name__ == "__main__":
    raise SystemExit(main())
