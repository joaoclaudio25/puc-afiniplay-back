# backend/controllers/recommendation_controller.py
# Rotas de indicação de filmes entre amigos

from flask import Blueprint, request, jsonify

from services.auth_service import token_required
from services.movie_service import MovieService
from services.friend_service import FriendService
from services.recommendation_service import RecommendationService

recommendation_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")


@recommendation_bp.get("")
@token_required
def list_received_recommendations(current_user):
    recs = RecommendationService.get_received_by_user(current_user.id)
    return jsonify([r.to_dict() for r in recs])


@recommendation_bp.post("")
@token_required
def create_recommendations(current_user):
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movie_id")
    friend_ids = data.get("friend_ids") or []

    if not movie_id or not isinstance(friend_ids, list) or not friend_ids:
        return jsonify({"error": "Selecione o filme e ao menos um amigo."}), 400

    movie = MovieService.get_by_id_and_user(movie_id, current_user.id)
    if not movie:
        return jsonify({"error": "Filme não encontrado."}), 404

    if not movie.watched:
        return jsonify({"error": "Só é possível indicar filmes já assistidos."}), 400

    friends = FriendService.get_registered_by_ids(current_user.id, friend_ids)
    to_user_ids = [f.linked_user_id for f in friends if f.linked_user_id]

    if not to_user_ids:
        return jsonify({"error": "Nenhum amigo cadastrado válido foi selecionado."}), 400

    created = RecommendationService.create_many(current_user.id, movie, to_user_ids)

    return jsonify({"message": f"Filme indicado para {len(created)} amigo(s)!"}), 201


@recommendation_bp.delete("/<int:rec_id>")
@token_required
def delete_recommendation(current_user, rec_id):
    ok = RecommendationService.delete_by_id_and_recipient(rec_id, current_user.id)
    if not ok:
        return jsonify({"error": "Indicação não encontrada."}), 404
    return jsonify({"message": "Indicação removida."})


@recommendation_bp.post("/<int:rec_id>/add-to-catalog")
@token_required
def add_recommendation_to_catalog(current_user, rec_id):
    rec = RecommendationService.get_received_by_id_and_recipient(rec_id, current_user.id)
    if not rec:
        return jsonify({"error": "Indicação não encontrada."}), 404

    movie, err = MovieService.create({
        "title": rec.movie_title,
        "year": rec.movie_year,
        "rating": rec.movie_rating,
        "genre": rec.movie_genre,
        "poster": rec.movie_poster,
        "plot": rec.movie_plot,
        "user_id": current_user.id,
    })

    # A indicação já foi "resolvida" (aceita) de qualquer forma — some da lista de
    # indicações pendentes tanto se o filme foi adicionado quanto se já estava no catálogo.
    RecommendationService.delete_by_id_and_recipient(rec_id, current_user.id)

    if err == "duplicate":
        return jsonify({"message": "Você já tinha esse filme no seu catálogo."})

    return jsonify({"message": "Filme adicionado ao seu catálogo!", "movie": movie.to_dict()}), 201
