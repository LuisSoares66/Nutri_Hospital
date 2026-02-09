from flask import Flask
from config import Config
from . import db, migrate  # ou db/migrate definidos aqui

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import bp
    app.register_blueprint(bp)

    return app
