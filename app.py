"""Ponto de entrada da aplicacao web do SIRAS.

Mantido intencionalmente fino: toda a logica agronomica vive em siras/motor/, que nao
importa Flask e pode ser executado e testado isoladamente. Ver docs/ARQUITETURA.md.

Uso:
    python app.py          # sobe em http://127.0.0.1:5000
"""

from siras.web import criar_app

app = criar_app()

if __name__ == "__main__":
    # host fixo em 127.0.0.1: o sistema roda local e offline, e nao deve ficar
    # acessivel na rede da maquina (proposta de TCC - sem banco, sem autenticacao).
    app.run(host="127.0.0.1", port=5000, debug=True)
