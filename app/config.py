import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "Lincinha")

    # Render fornece DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # garante sslmode=require se a URL não tiver
    if SQLALCHEMY_DATABASE_URI and "sslmode=" not in SQLALCHEMY_DATABASE_URI:
        join = "&" if "?" in SQLALCHEMY_DATABASE_URI else "?"
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI + f"{join}sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Login do botão ADMIN
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "Cida1383@Anna11")
