import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Render costuma fornecer DATABASE_URL no formato postgres://...
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url or "sqlite:///local.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pasta onde ficam os xlsx
    DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
