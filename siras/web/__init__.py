"""Camada web do SIRAS: fábrica da aplicação Flask.

Flask é casca. Nenhuma regra agronômica mora aqui — as rotas montam AnaliseSolo e
Contexto a partir do formulário, chamam gerar_laudo() e renderizam o resultado
(docs/ARQUITETURA.md). É por isso que siras/motor/ e siras/dominio/ continuam rodando
por linha de comando, sem Flask instalado no caminho.

Fábrica em vez de `app` global: os testes criam a aplicação em modo de teste sem
depender de import de módulo, e a aplicação nunca é instanciada só por alguém importar
o pacote.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Flask


def criar_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """Cria a aplicação Flask do SIRAS.

    Args:
        config: sobrescritas de configuração (usado pelos testes)

    Returns:
        Flask pronta para servir em localhost. Sem banco, sem autenticação e sem
        chamada de rede — requisito da proposta de TCC.
    """
    app = Flask(__name__)

    # trim_blocks/lstrip_blocks: as macros de componente geram HTML sem as linhas em
    # branco e a indentação de bloco do Jinja, que poluiriam o HTML do laudo impresso.
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    if config:
        app.config.update(config)

    from siras.web.rotas import bp

    app.register_blueprint(bp)
    return app


__all__ = ["criar_app"]
