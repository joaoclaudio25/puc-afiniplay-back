# backend/services/user_service.py
# Regras de negócio de perfil de usuário (Aba 2 - Perfil Pessoal e Aba 3 - Meus Streamings).

from datetime import date

from models import VALID_STREAMING_PLATFORMS


def parse_optional_profile_fields(data):
    """Extrai e valida os campos opcionais de perfil (Aba 2 - Perfil Pessoal e Aba 3 - Meus Streamings).
    Retorna (dict_de_campos, mensagem_de_erro). Em caso de erro, dict_de_campos é None."""
    age = data.get("age")
    if age not in (None, ""):
        try:
            age = int(age)
        except (TypeError, ValueError):
            return None, "Idade inválida."
    else:
        age = None

    birth_date_raw = (data.get("birth_date") or "").strip()
    birth_date = None
    if birth_date_raw:
        try:
            birth_date = date.fromisoformat(birth_date_raw)
        except ValueError:
            return None, "Data de nascimento inválida."

    city = (data.get("city") or "").strip() or None
    country = (data.get("country") or "").strip() or None
    gender = (data.get("gender") or "").strip() or None

    streaming_platforms = data.get("streaming_platforms") or []
    if not isinstance(streaming_platforms, list):
        return None, "Streamings selecionados em formato inválido."
    streaming_platforms = [p for p in streaming_platforms if p in VALID_STREAMING_PLATFORMS]

    streaming_other = (data.get("streaming_other") or "").strip() or None
    if "outros" not in streaming_platforms:
        streaming_other = None

    return {
        "age": age,
        "birth_date": birth_date,
        "city": city,
        "country": country,
        "gender": gender,
        "streaming_platforms": streaming_platforms,
        "streaming_other": streaming_other,
    }, None
