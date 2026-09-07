# backend/controllers/auth_controller.py
# Rotas de autenticação e recuperação de senha

import json
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, current_app

from database import db
from models import User
from services.auth_service import generate_token, hash_reset_token, RESET_TOKEN_TTL_HOURS
from services.user_service import parse_optional_profile_fields
from services.friend_service import FriendService
from services.email_service import (
    send_email,
    build_password_reset_email_html,
    build_password_changed_email_html,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    # --- Aba 1 - Conta (obrigatórios) ---
    full_name = (data.get("full_name") or "").strip()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password")

    if not full_name or not username or not email or not password:
        return jsonify({"error": "Preencha nome completo, usuário, e-mail e senha."}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Usuário ou e-mail já cadastrado."}), 400

    profile_fields, error = parse_optional_profile_fields(data)
    if error:
        return jsonify({"error": error}), 400

    user = User(
        full_name=full_name,
        username=username,
        email=email,
        age=profile_fields["age"],
        birth_date=profile_fields["birth_date"],
        city=profile_fields["city"],
        country=profile_fields["country"],
        gender=profile_fields["gender"],
        streaming_platforms=json.dumps(profile_fields["streaming_platforms"]) if profile_fields["streaming_platforms"] else None,
        streaming_other=profile_fields["streaming_other"],
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Se alguém já tinha convidado este e-mail como amigo, vincula o convite à nova conta
    # e avisa quem convidou.
    FriendService.link_registered_friends_to_new_user(user)

    return jsonify({"message": "Conta criada com sucesso!"}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username_or_email = (data.get("username") or "").strip()
    password = data.get("password")

    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciais inválidas."}), 401

    token = generate_token(user.id)

    return jsonify({
        "token": token,
        "username": user.username,
        "user_id": user.id
    })


@auth_bp.post("/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()

    if not email:
        return jsonify({"error": "Informe o e-mail cadastrado."}), 400

    generic_message = {
        "message": "Se este e-mail estiver cadastrado, enviamos um link para redefinição de senha."
    }

    user = User.query.filter_by(email=email).first()
    if user:
        raw_token = secrets.token_urlsafe(32)
        user.reset_token_hash = hash_reset_token(raw_token)
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_TTL_HOURS)
        db.session.commit()

        reset_link = f"{current_app.config['FRONTEND_URL']}/reset_password.html?token={raw_token}"
        send_email(
            user.email,
            "Redefinição de senha - AfiniPlay",
            build_password_reset_email_html(user.full_name or user.username, reset_link),
        )

    return jsonify(generic_message)


@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    password = data.get("password")

    if not token or not password:
        return jsonify({"error": "Token e nova senha são obrigatórios."}), 400

    user = User.query.filter_by(reset_token_hash=hash_reset_token(token)).first()

    if not user or not user.reset_token_expires_at or user.reset_token_expires_at < datetime.utcnow():
        return jsonify({"error": "Link inválido ou expirado. Solicite um novo."}), 400

    user.set_password(password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.session.commit()

    send_email(
        user.email,
        "Sua senha foi alterada - AfiniPlay",
        build_password_changed_email_html(user.full_name or user.username),
    )

    return jsonify({"message": "Senha redefinida com sucesso! Faça login com sua nova senha."})
