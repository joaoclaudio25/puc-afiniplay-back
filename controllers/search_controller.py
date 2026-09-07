# backend/controllers/search_controller.py
# Rota de busca de filmes na OMDb

from flask import Blueprint, request, jsonify

from services.auth_service import token_required
from services.omdb_service import search_movie

search_bp = Blueprint("search", __name__, url_prefix="/api/search")


@search_bp.get("")
@token_required
def search_omdb(current_user):
    title = request.args.get("title", "").strip()
    if not title:
        return jsonify({"error": "Informe o título para busca."}), 400

    try:
        result = search_movie(title)
    except Exception:
        return jsonify({"error": "Erro ao comunicar com o serviço de busca."}), 500

    if result is None:
        return jsonify({"error": "Filme não encontrado na API OMDb."}), 404

    return jsonify(result)
