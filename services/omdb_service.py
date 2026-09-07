# backend/services/omdb_service.py
# Integração com serviços externos: busca de filmes (OMDb) e tradução de sinopse (MyMemory).

import requests
from flask import current_app


def search_movie(title):
    """Busca um filme pelo título exato na OMDb. Retorna um dict com os dados
    normalizados, ou None se o filme não for encontrado."""
    api_key = current_app.config.get("OMDB_API_KEY")
    url = f"http://www.omdbapi.com/?apikey={api_key}&t={title}"

    response = requests.get(url, timeout=5)
    data = response.json()

    if data.get("Response") == "False":
        return None

    plot = data.get("Plot")
    genre = data.get("Genre")

    return {
        "title": data.get("Title"),
        "year": data.get("Year"),
        "rating": data.get("imdbRating"),
        # A OMDb retorna vários gêneros separados por vírgula, ex.: "Action, Adventure, Sci-Fi".
        "genre": None if not genre or genre == "N/A" else genre,
        "poster": data.get("Poster"),
        # A OMDb retorna a string literal "N/A" quando não tem sinopse (comum em títulos
        # dublados/traduzidos) — normalizamos para None para o frontend tratar como ausente.
        "plot": None if not plot or plot == "N/A" else plot,
    }


def translate_to_portuguese(text):
    """Traduz um texto de inglês para português via MyMemory (gratuita, sem chave).
    Retorna o texto traduzido, ou None se a tradução falhar."""
    response = requests.get(
        "https://api.mymemory.translated.net/get",
        params={"q": text, "langpair": "en|pt-br"},
        timeout=8,
    )
    data = response.json()
    return data.get("responseData", {}).get("translatedText")
