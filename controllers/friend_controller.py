# backend/controllers/friend_controller.py
# Rotas de cadastro e convite de amigos

from flask import Blueprint, request, jsonify, current_app

from database import db
from services.auth_service import token_required
from services.friend_service import FriendService
from services.email_service import send_email, build_friend_invite_email_html
from services.whatsapp_service import build_whatsapp_link

friend_bp = Blueprint("friends", __name__, url_prefix="/api/friends")


@friend_bp.get("")
@token_required
def list_friends(current_user):
    friends = FriendService.get_all_by_owner(current_user.id)
    return jsonify([f.to_dict() for f in friends])


@friend_bp.post("")
@token_required
def create_friend(current_user):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    invite_via_email = bool(data.get("invite_via_email"))
    invite_via_whatsapp = bool(data.get("invite_via_whatsapp"))

    if not name or not email:
        return jsonify({"error": "Informe nome e e-mail do amigo."}), 400

    if invite_via_whatsapp and not phone:
        return jsonify({"error": "Informe o telefone para convidar por WhatsApp."}), 400

    friend, error = FriendService.create(current_user.id, name, email, phone)
    if error == "duplicate":
        return jsonify({"error": "Você já cadastrou um amigo com esse e-mail."}), 400

    inviter_name = current_user.full_name or current_user.username
    whatsapp_link = None
    register_link = f"{current_app.config['FRONTEND_URL']}/login.html?tab=register"

    if invite_via_email:
        send_email(
            email,
            f"{inviter_name} te convidou para o AfiniPlay!",
            build_friend_invite_email_html(name, inviter_name, register_link),
        )
        friend.invited_via_email = True

    if invite_via_whatsapp:
        message = (
            f"Oi {name}! {inviter_name} te convidou para o AfiniPlay, um app para organizar "
            f"filmes assistidos e trocar indicações com amigos. Cadastre-se: "
            f"{register_link}"
        )
        whatsapp_link = build_whatsapp_link(phone, message)
        friend.invited_via_whatsapp = True

    if invite_via_email or invite_via_whatsapp:
        db.session.commit()

    result = friend.to_dict()
    if whatsapp_link:
        result["whatsapp_link"] = whatsapp_link

    return jsonify(result), 201


@friend_bp.delete("/<int:friend_id>")
@token_required
def delete_friend(current_user, friend_id):
    ok = FriendService.delete_by_id_and_owner(friend_id, current_user.id)
    if not ok:
        return jsonify({"error": "Amigo não encontrado."}), 404
    return jsonify({"message": "Amigo removido."})
