# backend/models.py
import json
from datetime import datetime
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

VALID_STREAMING_PLATFORMS = {
    "netflix", "prime_video", "max", "disney_plus", "globoplay",
    "apple_tv", "youtube", "mercado_play", "tv_aberta", "outros",
}

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Aba 1 - Conta (obrigatórios)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Aba 2 - Perfil Pessoal (opcionais)
    age = db.Column(db.Integer, nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.String(30), nullable=True)

    # Aba 3 - Meus Streamings (opcionais)
    streaming_platforms = db.Column(db.Text, nullable=True)  # JSON: lista de chaves selecionadas
    streaming_other = db.Column(db.String(120), nullable=True)  # texto livre quando "Outros" é selecionado

    # Redefinição de senha ("Esqueci minha senha")
    reset_token_hash = db.Column(db.String(128), nullable=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)

    # Relacionamento 1:N com filmes (ao apagar o usuário, apaga os filmes dele)
    movies = db.relationship("Movie", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_streaming_platforms(self):
        if not self.streaming_platforms:
            return []
        try:
            return json.loads(self.streaming_platforms)
        except (TypeError, ValueError):
            return []

    def to_profile_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "email": self.email,
            "age": self.age,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "city": self.city,
            "country": self.country,
            "gender": self.gender,
            "streaming_platforms": self.get_streaming_platforms(),
            "streaming_other": self.streaming_other,
        }


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    year = db.Column(db.String(10), nullable=True)
    rating = db.Column(db.String(10), nullable=True)
    genre = db.Column(db.String(150), nullable=True)  # gêneros da OMDb, ex.: "Action, Adventure, Sci-Fi"
    poster = db.Column(db.String(255), nullable=True)
    watched = db.Column(db.Boolean, default=False)
    my_rating = db.Column(db.Integer, nullable=True)  # avaliação pessoal de 1 a 5 estrelas
    is_favorite = db.Column(db.Boolean, default=False)
    watched_on_platform = db.Column(db.String(120), nullable=True)  # streaming onde o usuário assistiu (opcional)
    plot = db.Column(db.Text, nullable=True)  # sinopse (OMDb, em inglês)
    plot_pt = db.Column(db.Text, nullable=True)  # sinopse traduzida para português (cache)
    comment = db.Column(db.Text, nullable=True)  # comentário pessoal do usuário (opcional)

    # Chave estrangeira para o usuário dono do filme
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "rating": self.rating,
            "genre": self.genre,
            "poster": self.poster,
            "watched": self.watched,
            "my_rating": self.my_rating,
            "is_favorite": self.is_favorite,
            "watched_on_platform": self.watched_on_platform,
            "plot": self.plot,
            "plot_pt": self.plot_pt,
            "comment": self.comment,
            "user_id": self.user_id
        }


class Friend(db.Model):
    """Um amigo cadastrado por um usuário para receber convite e, futuramente,
    indicações de filmes. status: 'pending' (convidado, ainda não tem conta) ou
    'registered' (já criou conta no AfiniPlay com o mesmo e-mail)."""
    __tablename__ = "friends"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)

    status = db.Column(db.String(20), default="pending", nullable=False)
    invited_via_email = db.Column(db.Boolean, default=False)
    invited_via_whatsapp = db.Column(db.Boolean, default=False)

    # Preenchido quando o amigo efetivamente cria a conta (mesmo e-mail do convite)
    linked_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User", foreign_keys=[owner_user_id])
    linked_user = db.relationship("User", foreign_keys=[linked_user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "invited_via_email": self.invited_via_email,
            "invited_via_whatsapp": self.invited_via_whatsapp,
        }


class MovieRecommendation(db.Model):
    """Indicação de um filme de um usuário para outro (amigo já cadastrado no AfiniPlay).
    Os dados do filme são copiados no momento da indicação, para não depender do filme
    continuar existindo no catálogo de quem indicou."""
    __tablename__ = "movie_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    movie_title = db.Column(db.String(120), nullable=False)
    movie_year = db.Column(db.String(10), nullable=True)
    movie_poster = db.Column(db.String(255), nullable=True)
    movie_rating = db.Column(db.String(10), nullable=True)
    movie_genre = db.Column(db.String(150), nullable=True)
    movie_plot = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "movie_title": self.movie_title,
            "movie_year": self.movie_year,
            "movie_poster": self.movie_poster,
            "movie_rating": self.movie_rating,
            "movie_genre": self.movie_genre,
            "movie_plot": self.movie_plot,
            "from_user_name": self.from_user.full_name or self.from_user.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }