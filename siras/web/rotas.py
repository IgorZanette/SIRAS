"""Rotas do SIRAS.

Mapa previsto (PLANO-FRONTEND §9.1), implementado por etapas:

    /                  landing                        — etapa 7, hoje um provisório
    /analise           etapa 1, escolha da cultura    — etapa 5
    /analise/dados     etapa 2, análise de solo       — etapa 2
    /analise/laudo     etapa 3, laudo                 — etapa 2
    /api/interpretar   POST, leitura ao vivo          — etapa 4

Cada rota, quando existir, monta AnaliseSolo e Contexto e chama gerar_laudo(). Nenhuma
interpretação acontece aqui nem em JavaScript: fonte única de verdade é o motor Python
(PLANO-FRONTEND §9.4, opção B).
"""

from __future__ import annotations

from flask import Blueprint, render_template

bp = Blueprint("siras", __name__)


@bp.get("/")
def inicio():
    """Provisório até a etapa 7 (landing).

    Existe para que a casca — tema, fontes auto-hospedadas, sprite de ícones e macros —
    seja verificável desde já, com a rede desligada.
    """
    return render_template("inicio.html")
