# backend/controllers/user_controller.py
# Rotas de gerenciamento do perfil do usuário autenticado

import json

from flask import Blueprint, request, jsonify

from database import db
from models import User
from services.auth_service import token_required
from services.user_service import parse_optional_profile_fields
from services.email_service import send_email, build_password_changed_email_html

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.get("/me")
@token_required
def get_current_user_profile(current_user):
    return jsonify(current_user.to_profile_dict())


@user_bp.put("/me")
@token_required
def update_user_profile(current_user):
    data = request.get_json(silent=True) or {}
    new_full_name = (data.get("full_name") or "").strip()
    new_username = (data.get("username") or "").strip()
    new_email = (data.get("email") or "").strip()
    new_password = data.get("password")

    if new_full_name:
        current_user.full_name = new_full_name

    if new_username:
        if User.query.filter(User.username == new_username, User.id != current_user.id).first():
            return jsonify({"error": "Nome de usuário em uso."}), 400
        current_user.username = new_username

    if new_email:
        if User.query.filter(User.email == new_email, User.id != current_user.id).first():
            return jsonify({"error": "E-mail em uso."}), 400
        current_user.email = new_email

    if new_password:
        current_user.set_password(new_password)
        send_email(
            current_user.email,
            "Sua senha foi alterada - AfiniPlay",
            build_password_changed_email_html(current_user.full_name or current_user.username),
        )

    profile_fields, error = parse_optional_profile_fields(data)
    if error:
        return jsonify({"error": error}), 400

    current_user.age = profile_fields["age"]
    current_user.birth_date = profile_fields["birth_date"]
    current_user.city = profile_fields["city"]
    current_user.country = profile_fields["country"]
    current_user.gender = profile_fields["gender"]
    current_user.streaming_platforms = (
        json.dumps(profile_fields["streaming_platforms"]) if profile_fields["streaming_platforms"] else None
    )
    current_user.streaming_other = profile_fields["streaming_other"]

    db.session.commit()
    return jsonify({"message": "Perfil atualizado com sucesso!", **current_user.to_profile_dict()})


@user_bp.delete("/me")
@token_required
def delete_user_account(current_user):
    db.session.delete(current_user)
    db.session.commit()
    return jsonify({"message": "Conta removida com sucesso."})
