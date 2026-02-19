import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,        # testa conexão antes de usar
        "pool_recycle": 280,          # recicla antes do timeout comum
        "pool_timeout": 30,
        "pool_size": 5,
        "max_overflow": 2,
        "connect_args": {"sslmode": "require"},
    }


    # Login do botão ADMIN
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "Cida1383@Anna11")
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")

