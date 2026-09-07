# backend/services/whatsapp_service.py
# Geração de links de convite via WhatsApp (wa.me) — não envia nada sozinho,
# apenas monta o link que abre o WhatsApp do próprio usuário com a mensagem pronta.

import re
from urllib.parse import quote


def build_whatsapp_link(phone, message):
    """Monta um link wa.me a partir de um telefone brasileiro em qualquer formato
    (com ou sem DDD/código do país, com parênteses, traços, espaços etc.)."""
    digits = re.sub(r"\D", "", phone or "")

    # Número com DDD mas sem código do país (10 ou 11 dígitos) -> assume Brasil (55)
    if len(digits) in (10, 11):
        digits = "55" + digits

    return f"https://wa.me/{digits}?text={quote(message)}"
