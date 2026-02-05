from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

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

    # Configurações
    app.config.from_object(Config)

    # Inicializa extensões com o app
    db.init_app(app)
    migrate.init_app(app, db)

    # Blueprints / rotas
    from app.routes import bp
    app.register_blueprint(bp)

    return app
