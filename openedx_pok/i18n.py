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

def resolve_language_tag(user, default=None):
    """
    Resolve a BCP 47 language tag using:
    1) user.profile.language
    2) HTTP Accept-Language (si hay request actual)
    3) current thread language (Django)
    4) settings.LANGUAGE_CODE
    Fallback (final): settings.LANGUAGE_CODE normalizado, luego settings.POK_DEFAULT_LANGUAGE_TAG,
    o 'default' provisto.
    """
    candidates = []

    # 1) Preferencia de usuario (perfil)
    lang = getattr(getattr(user, "profile", None), "language", None)
    if lang:
        candidates.append(lang)

    # 2) Accept-Language de la request actual (si disponible)
    try:
        request = get_current_request()
        if request:
            header = request.META.get("HTTP_ACCEPT_LANGUAGE") or request.headers.get("Accept-Language", "")
            candidates.extend(_parse_accept_language(header))
    except Exception:
        pass

    # 3) Idioma activo del hilo
    try:
        current = django_get_language()
    except Exception:
        current = None
    if current:
        candidates.append(current)

    # 4) Idioma por defecto de la plataforma
    candidates.append(getattr(settings, "LANGUAGE_CODE", None))

    # Normalización a BCP 47
    mapping = {
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

    for code in candidates:
        if not code:
            continue
        c = str(code).strip().lower().replace("_", "-")
        if c in mapping:
            return mapping[c]
        parts = c.split("-")
        if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) in (2, 3):
            return f"{parts[0]}-{parts[1].upper()}"

    # Fallback: intentar con el LANGUAGE_CODE de Django (normalizado)
    site_default = getattr(settings, "LANGUAGE_CODE", None)
    if site_default:
        c = str(site_default).strip().lower().replace("_", "-")
        if c in mapping:
            return mapping[c]
        parts = c.split("-")
        if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) in (2, 3):
            return f"{parts[0]}-{parts[1].upper()}"

