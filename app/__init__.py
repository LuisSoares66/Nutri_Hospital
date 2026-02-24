# app/__init__.py
from flask import Flask
from config import Config
from app.extensions import db, migrate
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # ✅ garante schema (antes de qualquer query)
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE hospitais ADD COLUMN IF NOT EXISTS data_visita DATE;"))
            db.session.execute(text("ALTER TABLE hospitais ADD COLUMN IF NOT EXISTS data_retorno DATE;"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # (opcional) teste de conexão
        try:
            db.session.execute(text("SELECT 1"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    # blueprints (depois do schema garantido)
    from app.routes import bp as main_bp
    from app.auth import auth_bp

    app.register_blueprint(main_bp)
    # app.register_blueprint(auth_bp)

    return app


