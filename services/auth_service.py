# backend/services/auth_service.py
# Regras de autenticação: geração/validação de JWT e tokens de redefinição de senha.

import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps

from flask import request, jsonify, current_app

from database import db
from models import User

RESET_TOKEN_TTL_HOURS = 1


def generate_token(user_id, hours=24):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=hours),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def hash_reset_token(raw_token):
    return hashlib.sha256(raw_token.encode()).hexdigest()


def token_required(f):
    """Decorador que exige um Bearer token JWT válido e injeta o usuário autenticado
    como primeiro argumento (current_user) da view."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token de autenticação ausente."}), 401

        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = db.session.get(User, data["user_id"])
            if not current_user:
                return jsonify({"error": "Usuário não encontrado."}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Sessão expirada. Faça login novamente."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido."}), 401

        return f(current_user, *args, **kwargs)

    return decorated
