from app import db
from flask import Flask
from config import Config
#from app.extensions import db  # se você usa db em extensions
# ou: from app import db  (ajuste conforme seu projeto)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # init extensões
    db.init_app(app)

    # ✅ importa blueprints SÓ aqui dentro, UMA vez
    from app.routes import bp as main_bp
    from app.auth import auth_bp

    # ✅ registra uma vez cada
    app.register_blueprint(main_bp)      # sem prefixo
    app.register_blueprint(auth_bp)      # sem prefixo

    return app

