from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from app import models  # garante que os models sejam carregados

# ======================================================
# EXTENSÕES (instanciadas UMA ÚNICA VEZ)
# ======================================================
db = SQLAlchemy()
migrate = Migrate()


# ======================================================
# FACTORY DO APP
# ======================================================
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models  # <<< ADICIONE ISSO

    from app.routes import bp
    app.register_blueprint(bp)

    return app


