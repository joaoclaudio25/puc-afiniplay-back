import os


def _normalize_database_url(url):
    """Provedores de hospedagem (Render, Railway, etc.) costumam injetar DATABASE_URL
    como "postgres://..." ou "postgresql://...". Este projeto usa o driver pg8000
    (evita depender de compilar o psycopg2), então precisamos adaptar o esquema da
    URL para "postgresql+pg8000://..." antes de passar ao SQLAlchemy."""
    if not url:
        return "postgresql+pg8000://postgres:postgres@localhost:5433/afiniplay_db"
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+pg8000://" + url[len("postgresql://"):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "3d63571d45c6d098da4e18be15efd5b317a129699c80e9964e3fc326850fb215")

    # Usando o driver pg8000 em vez do psycopg2
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get("DATABASE_URL"))

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "7baf41a")

    # URL pública onde o FRONTEND (HTML/CSS/JS) está hospedado — o backend não serve
    # mais páginas, mas ainda precisa saber para onde apontar os links que manda por
    # e-mail/WhatsApp (redefinição de senha, convite de amigo). Sem barra no final.
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5500").rstrip("/")
    

