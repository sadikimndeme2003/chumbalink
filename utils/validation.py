"""
Uthibitishaji wa taarifa upande wa SERVER -- frontend validation (HTML
required/min/max, JS) ni kwa ajili ya UX nzuri tu; mtu yeyote anaweza
kuipita kwa kutuma request moja kwa moja (curl, Postman, n.k), hivyo
kila kitu muhimu lazima kikaguliwe tena hapa.
"""

MAX_PRICE = 50_000_000      # TZS/mwezi -- kikomo cha juu cha busara
MAX_DISTANCE_KM = 500        # km -- hakuna chumba "karibu na chuo" kitakuwa mbali hivi
MAX_TEXT_LEN = 2000          # sifa/maelekezo/maelezo -- zuia maandishi marefu kupindukia


def validate_price(raw, required=True):
    """Inarudisha (thamani_float_au_None, ujumbe_wa_error_au_None)."""
    raw = (raw or "").strip()
    if not raw:
        if required:
            return None, "Bei inahitajika."
        return None, None
    try:
        value = float(raw)
    except ValueError:
        return None, "Bei si namba sahihi."
    if value <= 0:
        return None, "Bei lazima iwe zaidi ya sifuri."
    if value > MAX_PRICE:
        return None, f"Bei kubwa mno (kikomo ni TZS {MAX_PRICE:,.0f})."
    return value, None


def validate_distance(raw, required=False):
    """Inarudisha (thamani_float_au_None, ujumbe_wa_error_au_None)."""
    raw = (raw or "").strip()
    if not raw:
        if required:
            return None, "Umbali unahitajika."
        return None, None
    try:
        value = float(raw)
    except ValueError:
        return None, "Umbali si namba sahihi."
    if value < 0:
        return None, "Umbali hauwezi kuwa hasi."
    if value > MAX_DISTANCE_KM:
        return None, f"Umbali mkubwa mno (kikomo ni {MAX_DISTANCE_KM} km)."
    return value, None


def validate_text_len(raw, field_label, max_len=MAX_TEXT_LEN):
    """Inarudisha ujumbe wa error, au None kama sawa."""
    if raw and len(raw) > max_len:
        return f"{field_label} ni ndefu mno (kikomo ni herufi {max_len})."
    return None
