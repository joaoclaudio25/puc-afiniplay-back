from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate

from config import Config
from database import db

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)
migrate = Migrate(app, db)

from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.movie_controller import movie_bp
from controllers.search_controller import search_bp
from controllers.friend_controller import friend_bp
from controllers.recommendation_controller import recommendation_bp

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(movie_bp)
app.register_blueprint(search_bp)
app.register_blueprint(friend_bp)
app.register_blueprint(recommendation_bp)


@app.get("/")
def health_check():
    """Backend é API-only agora — o frontend (HTML/CSS/JS) vive em outro
    repositório/hospedagem separada. Esta rota só serve para checar se a
    API está no ar."""
    return jsonify({"status": "ok", "service": "AfiniPlay API"})


# --- INICIALIZAÇÃO ---
# O schema do banco agora é gerenciado pelo Alembic (Flask-Migrate).
# Rode "flask db upgrade" para aplicar as migrações mais recentes.

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
