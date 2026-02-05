import os


class Config:
    # ======================================================
    # CONFIGURAÇÕES BÁSICAS
    # ======================================================
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # ======================================================
    # BANCO DE DADOS (Render / PostgreSQL)
    # ======================================================
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///local.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ======================================================
    # FLASK
    # ======================================================
    TEMPLATES_AUTO_RELOAD = True

