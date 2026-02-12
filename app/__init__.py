# app/__init__.py
from flask import Flask
from config import Config
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # blueprints
    from app.routes import bp as main_bp
    from app.auth import auth_bp

    app.register_blueprint(main_bp)       # sem prefixo
    #app.register_blueprint(auth_bp)       # ou url_prefix="/auth"

    return app


