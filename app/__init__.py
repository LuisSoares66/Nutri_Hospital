from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # importa models depois do db existir
    from app import models  # noqa: F401

    # Blueprints
    from app.routes import bp
    app.register_blueprint(bp)

    return app
