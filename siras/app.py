"""Ponto de entrada da aplicacao web do SIRAS.

Mantido intencionalmente fino: toda a logica agronomica vive em siras/motor/, que nao
importa Flask e pode ser executado e testado isoladamente. Ver docs/especificacao/arquitetura.md.

Uso preferencial, da RAIZ do repositorio:

    py run.py              # cria a venv, instala tudo e sobe em http://127.0.0.1:5000

`run.py` existe porque a demonstracao nao pode depender de o ambiente estar preparado na
maquina onde ela acontece. Este arquivo continua valendo para quem ja tem a venv ativa e
quer o reloader do Flask ligado:

    cd siras && python app.py
"""

from siras.web import criar_app

app = criar_app()

if __name__ == "__main__":
    # host fixo em 127.0.0.1: o sistema roda local e offline, e nao deve ficar
    # acessivel na rede da maquina (proposta de TCC - sem banco, sem autenticacao).
    app.run(host="127.0.0.1", port=5000, debug=True)
