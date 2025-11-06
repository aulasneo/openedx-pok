from django.conf import settings
import logging

logger = logging.getLogger(__name__)

try:
    from django.utils.translation import get_language as django_get_language
except Exception:  # pragma: no cover
    def django_get_language():
        return None

# Intentar obtener la request actual (si crum está instalado en Open edX)
try:
    from crum import get_current_request
except Exception:  # pragma: no cover
    def get_current_request():
        return None

# Mapeo global de códigos a BCP 47
_MAPPING = {
    # Básicos
    "es": "es-ES", "es-es": "es-ES", "es_es": "es-ES",
    "en": "en-US", "en-us": "en-US", "en_us": "en-US",
    "pt": "pt-BR", "pt-br": "pt-BR", "pt_br": "pt-BR",
    "pt-pt": "pt-PT", "pt_pt": "pt-PT",

    # Español LATAM y variantes
    "es-419": "es-419", "es-ar": "es-AR", "es-cl": "es-CL",
    "es-co": "es-CO", "es-mx": "es-MX", "es-pe": "es-PE", "es-uy": "es-UY",

    # Inglés variantes
    "en-gb": "en-GB", "en-ca": "en-CA", "en-au": "en-AU", "en-in": "en-IN",

    # Francés, alemán, italiano, neerlandés, turco, ruso
    "fr": "fr-FR", "fr-ca": "fr-CA",
    "de": "de-DE", "it": "it-IT", "nl": "nl-NL", "tr": "tr-TR", "ru": "ru-RU",

    # Chino, japonés, coreano
    "zh": "zh-CN", "zh-cn": "zh-CN", "zh-tw": "zh-TW",
    "zh-hans": "zh-CN", "zh-hant": "zh-TW",
    "ja": "ja-JP", "ko": "ko-KR",

    # Árabe y hebreo
    "ar": "ar-SA", "he": "he-IL",

    # Nórdicos y cercanos
    "sv": "sv-SE", "fi": "fi-FI", "da": "da-DK",
    "no": "no-NO", "nb": "nb-NO",

    # Europa del Este
    "pl": "pl-PL", "cs": "cs-CZ", "sk": "sk-SK", "hu": "hu-HU",
    "ro": "ro-RO", "uk": "uk-UA", "bg": "bg-BG", "el": "el-GR",
    "sr": "sr-RS", "hr": "hr-HR", "sl": "sl-SI",
    "lt": "lt-LT", "lv": "lv-LV", "et": "et-EE",

    # Idiomas de España adicionales
    "ca": "ca-ES", "eu": "eu-ES", "gl": "gl-ES",

    # Asia y otros
    "vi": "vi-VN", "th": "th-TH", "id": "id-ID", "ms": "ms-MY", "fa": "fa-IR",

    # India
    "hi": "hi-IN", "bn": "bn-BD", "ta": "ta-IN", "te": "te-IN",
    "gu": "gu-IN", "mr": "mr-IN", "pa": "pa-IN",
}


def _normalize_lang(code):
    """
    Normaliza entradas como 'es', 'es-es', 'en_US', 'spanish' a un tag BCP 47 válido.
    Retorna None si no puede normalizar.
    """
    if not code:
        return None
    c = str(code).strip().lower().replace("_", "-")
    if c == "*":
        return None
    
    # Mapeo directo
    if c in _MAPPING:
        return _MAPPING[c]
    # Heurística simple: ll-CC
    parts = c.split("-")
    if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) in (2, 3):
        return f"{parts[0]}-{parts[1].upper()}"
    # Solo lenguaje de 2 letras sin región
    if len(parts) == 1 and len(parts[0]) == 2 and parts[0] in ("en", "es", "pt", "fr", "de", "it", "nl", "tr", "ru", "ja", "ko", "zh"):
        # Reintentar usando mapping base si existe
        base = parts[0]
        if base in _MAPPING:
            return _MAPPING[base]
    return None

def _parse_accept_language(header_value):
    """
    Devuelve una lista de códigos de idioma (en orden de preferencia) a partir de Accept-Language.
    Respeta q-values. No normaliza (eso lo hace resolve_language_tag).
    """
    if not header_value:
        return []
    items = []
    try:
        for part in header_value.split(","):
            part = part.strip()
            if not part:
                continue
            lang, q = part, 1.0
            if ";q=" in part:
                lang, qval = part.split(";q=", 1)
                try:
                    q = float(qval)
                except ValueError:
                    q = 1.0
            items.append((lang.strip(), q))
        # Ordenar por q desc y preservar orden estable para empates
        items.sort(key=lambda x: x[1], reverse=True)
        return [lang for lang, _ in items if lang]
    except Exception:  # pragma: no cover
        return []

def _get_user_profile_language(user):
    """
    Devuelve el idioma del usuario desde:
    1) user.profile.language
    2) Preferencias de usuario (Open edX): 'pref-lang' o 'language'
    """
    # 1) Perfil
    lang = getattr(getattr(user, "profile", None), "language", None)
    if lang:
        return lang

    # 2) Preferencias de usuario (API Open edX)
    try:
        from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
        for key in ("pref-lang", "language"):
            pref = get_user_preference(user, key)
            if pref:
                return pref
    except Exception:
        pass

    return None

def resolve_language_tag(user, default=None):
    """
    Resolve a BCP 47 language tag usando:
    1) Idioma de perfil/preferencias del usuario (Open edX)
    2) HTTP Accept-Language (si hay request actual)
    3) current thread language (Django)
    4) settings.LANGUAGE_CODE
    Fallback final: settings.LANGUAGE_CODE normalizado, luego settings.POK_DEFAULT_LANGUAGE_TAG o 'default'.
    """
    candidates = []

    # 1) Perfil / preferencias
    lang = _get_user_profile_language(user)
    logger.info(f"[POK] User profile/preference language: {lang}")
    if lang:
        candidates.append(lang)

    # 2) Accept-Language
    request = get_current_request()
    if request:
        header = request.META.get("HTTP_ACCEPT_LANGUAGE", "") or getattr(getattr(request, "headers", None), "get", lambda *_: "")("Accept-Language", "")
        langs = _parse_accept_language(header)
        candidates.extend(langs)

    # 3) Idioma activo de Django
    try:
        from django.utils import translation
        lang = translation.get_language()
        if lang:
            candidates.append(lang)
    except Exception:  # pragma: no cover
        pass

    # Intentar normalizar candidatos en orden
    for code in candidates:
        norm = _normalize_lang(code)
        if norm:
            return norm

    # 4) Fallback: LANGUAGE_CODE del sitio (normalizado)
    site_default = getattr(settings, "LANGUAGE_CODE", None)
    norm = _normalize_lang(site_default)
    if norm:
        return norm

