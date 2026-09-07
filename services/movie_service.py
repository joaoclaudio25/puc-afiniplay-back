# Regras de negócio (criar, listar, atualizar, excluir)
# backend/services/movie_service.py

from database import db
from models import Movie

class MovieService:
    @staticmethod
    def get_all_by_user(user_id):
        """Retorna todos os filmes pertencentes a um usuário específico."""
        return Movie.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_by_id_and_user(movie_id, user_id):
        """Retorna um filme específico de um usuário, se ele for o dono."""
        return Movie.query.filter_by(id=movie_id, user_id=user_id).first()

    @staticmethod
    def create(data):
        """Cria um novo filme no catálogo de um usuário."""
        # Evita duplicidade de título para o mesmo usuário
        existing = Movie.query.filter_by(title=data["title"], user_id=data["user_id"]).first()
        if existing:
            return None, "duplicate"

        movie = Movie(
            title=data.get("title"),
            year=data.get("year"),
            rating=data.get("rating"),
            genre=data.get("genre"),
            poster=data.get("poster"),
            watched=data.get("watched", False),
            my_rating=data.get("my_rating"),
            is_favorite=data.get("is_favorite", False),
            watched_on_platform=data.get("watched_on_platform"),
            plot=data.get("plot"),
            user_id=data.get("user_id")
        )
        db.session.add(movie)
        db.session.commit()
        return movie, None

    @staticmethod
    def update(movie_id, data):
        """Atualiza os dados de um filme (não precisa verificar user_id aqui pois o app.py já faz)."""
        movie = db.session.get(Movie, movie_id) # Usando Session.get() moderno
        if not movie:
            return None

        if "title" in data:
            movie.title = data["title"]
        if "year" in data:
            movie.year = data["year"]
        if "rating" in data:
            movie.rating = data["rating"]
        if "genre" in data:
            movie.genre = data["genre"]
        if "poster" in data:
            movie.poster = data["poster"]
        if "watched" in data:
            movie.watched = data["watched"]
        if "my_rating" in data:
            movie.my_rating = data["my_rating"]
        if "is_favorite" in data:
            movie.is_favorite = data["is_favorite"]
        if "watched_on_platform" in data:
            movie.watched_on_platform = data["watched_on_platform"]
        if "plot" in data:
            movie.plot = data["plot"]
        if "plot_pt" in data:
            movie.plot_pt = data["plot_pt"]
        if "comment" in data:
            movie.comment = data["comment"]

        db.session.commit()
        return movie

    @staticmethod
    def delete_by_id_and_user(movie_id, user_id):
        """Remove um filme do banco se o usuário for o dono."""
        movie = MovieService.get_by_id_and_user(movie_id, user_id)
        if not movie:
            return False
        db.session.delete(movie)
        db.session.commit()
        return True