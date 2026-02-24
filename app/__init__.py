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

    # blueprints (depois do schema garantido)
    from app.routes import bp as main_bp
    from app.auth import auth_bp

    app.register_blueprint(main_bp)
    # app.register_blueprint(auth_bp)

    return app


