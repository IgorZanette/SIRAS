"""
Configuração da suíte: o que roda a cada alteração e o que roda antes de entregar.

A suíte completa passou de quatro minutos, e 84% desse tempo estava em duas bancadas —
61 culturas vezes dez cenários de solo, percorrendo cada estado que a tela oferece. Elas
são valiosas, e foi uma delas que achou o HTTP 500 da macieira e o "(None)" impresso no
laudo; mas rodá-las a cada ajuste de CSS transforma o teste em espera, e espera faz
ninguém rodar teste nenhum.

Duas camadas, então:

    python -m pytest              rápida: motor, conformidade, telas, laudo (~40 s)
    python -m pytest --completa   tudo, inclusive as bancadas lentas (~4 min)

A CONFORMIDADE DO CCAE FICA NA RÁPIDA, de propósito. É o oráculo do trabalho — a
verificação de que o motor classifica a aptidão como o caderno aprovado manda — e custa
12 segundos. Um ajuste que a quebrasse precisa ser visto na hora, e não na véspera da
entrega.

O que vai para a camada lenta é o que repete, em volume, o que a rápida já cobre por
amostra: os testes por grupo exercitam os seis despachos do motor, e as bancadas
exercitam as 61 culturas inteiras. Rode a completa antes de todo push e sempre que mexer
na base de conhecimento, no formulário ou no despacho de grupos.

Os testes lentos são RETIRADOS da coleta, e não marcados como pulados: dois mil e
setecentos "s" na saída esconderiam o pulo que importa, o que alguém marcou por um
motivo real.
"""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--completa",
        action="store_true",
        default=False,
        help="Roda também as bancadas lentas (61 culturas x 10 cenários). "
             "Use antes de push e ao mexer na base, no formulário ou no despacho.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "lenta: bancada ampla, rodada antes de entregar e não a cada alteração "
        "(ative com --completa)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--completa"):
        return

    mantidos, retirados = [], []
    for item in items:
        (retirados if "lenta" in item.keywords else mantidos).append(item)

    if retirados:
        config.hook.pytest_deselected(items=retirados)
        items[:] = mantidos
