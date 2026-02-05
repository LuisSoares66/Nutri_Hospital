"""
Arquivo mantido apenas para referência ou execução local rápida.
NÃO é usado pelo Flask no deploy.
O app oficial é criado em manage.py usando factory (create_app).
"""

from app import create_app

# Cria o app apenas se este arquivo for executado diretamente
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
