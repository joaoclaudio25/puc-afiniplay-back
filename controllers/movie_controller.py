# backend/controllers/movie_controller.py
# Rotas do catálogo de filmes (isoladas por usuário autenticado)

from flask import Blueprint, request, jsonify

from services.auth_service import token_required
from services.movie_service import MovieService
from services.omdb_service import translate_to_portuguese

movie_bp = Blueprint("movies", __name__, url_prefix="/api/movies")


@movie_bp.get("")
@token_required
def list_movies(current_user):
    movies = MovieService.get_all_by_user(current_user.id)
    return jsonify([m.to_dict() for m in movies])


@movie_bp.post("")
@token_required
def create_movie(current_user):
    data = request.get_json(silent=True) or {}
    data["user_id"] = current_user.id

    movie, err = MovieService.create(data)
    if err == "duplicate":
        return jsonify({"errors": ["Esse filme já está no seu catálogo."]}), 400

    return jsonify(movie.to_dict()), 201


@movie_bp.put("/<int:movie_id>")
@token_required
def update_movie(current_user, movie_id):
    movie = MovieService.get_by_id_and_user(movie_id, current_user.id)
    if not movie:
        return jsonify({"error": "Filme não encontrado."}), 404

    data = request.get_json(silent=True) or {}
    updated = MovieService.update(movie_id, data)
    return jsonify(updated.to_dict())


@movie_bp.delete("/<int:movie_id>")
@token_required
def delete_movie(current_user, movie_id):
    ok = MovieService.delete_by_id_and_user(movie_id, current_user.id)
    if not ok:
        return jsonify({"error": "Filme não encontrado."}), 404
    return jsonify({"message": "Filme removido do catálogo."})


@movie_bp.post("/<int:movie_id>/translate-plot")
@token_required
def translate_movie_plot(current_user, movie_id):
    movie = MovieService.get_by_id_and_user(movie_id, current_user.id)
    if not movie:
        return jsonify({"error": "Filme não encontrado."}), 404

    if movie.plot_pt:
        return jsonify({"plot_pt": movie.plot_pt})

    if not movie.plot:
        return jsonify({"error": "Este filme não possui sinopse para traduzir."}), 400

    try:
        translated = translate_to_portuguese(movie.plot)
    except Exception:
        return jsonify({"error": "Erro ao comunicar com o serviço de tradução."}), 500

    if not translated:
        return jsonify({"error": "Não foi possível traduzir a sinopse."}), 502

    updated = MovieService.update(movie_id, {"plot_pt": translated})
    return jsonify({"plot_pt": updated.plot_pt})
