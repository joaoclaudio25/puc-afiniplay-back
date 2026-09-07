# backend/services/recommendation_service.py
# Regras de negócio de indicação de filmes entre amigos

from database import db
from models import MovieRecommendation


class RecommendationService:
    @staticmethod
    def create_many(from_user_id, movie, to_user_ids):
        """Cria uma indicação para cada destinatário, copiando os dados do filme
        (independe do filme continuar existindo no catálogo de quem indicou)."""
        created = []
        for to_user_id in to_user_ids:
            rec = MovieRecommendation(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                movie_title=movie.title,
                movie_year=movie.year,
                movie_poster=movie.poster,
                movie_rating=movie.rating,
                movie_genre=movie.genre,
                movie_plot=movie.plot,
            )
            db.session.add(rec)
            created.append(rec)

        db.session.commit()
        return created

    @staticmethod
    def get_received_by_user(user_id):
        return MovieRecommendation.query.filter_by(to_user_id=user_id).order_by(
            MovieRecommendation.created_at.desc()
        ).all()

    @staticmethod
    def get_received_by_id_and_recipient(rec_id, user_id):
        return MovieRecommendation.query.filter_by(id=rec_id, to_user_id=user_id).first()

    @staticmethod
    def delete_by_id_and_recipient(rec_id, user_id):
        rec = MovieRecommendation.query.filter_by(id=rec_id, to_user_id=user_id).first()
        if not rec:
            return False
        db.session.delete(rec)
        db.session.commit()
        return True
