"""Internationalization utilities for POK certificate integration."""

import logging
from importlib import import_module
from typing import Iterable, List, Optional

from django.conf import settings
from django.utils import translation

try:
    from crum import get_current_request
except ImportError:  # pragma: no cover
    def get_current_request():  # type: ignore[return-type]
        """Return None when crum is not available."""
        return None

logger = logging.getLogger(__name__)

# Mapeo global de códigos a BCP 47
_MAPPING = {
    # Básicos
    "es": "es-ES",
    "es-es": "es-ES",
    "es_es": "es-ES",
    "en": "en-US",
    "en-us": "en-US",
    "en_us": "en-US",
    "pt": "pt-BR",
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
    "pt-pt": "pt-PT",
    "pt_pt": "pt-PT",
    # Español LATAM y variantes
    "es-419": "es-419",
    "es-ar": "es-AR",
    "es-cl": "es-CL",
    "es-co": "es-CO",
    "es-mx": "es-MX",
    "es-pe": "es-PE",
    "es-uy": "es-UY",
    # Inglés variantes
    "en-gb": "en-GB",
    "en-ca": "en-CA",
    "en-au": "en-AU",
    "en-in": "en-IN",
    # Francés, alemán, italiano, neerlandés, turco, ruso
    "fr": "fr-FR",
    "fr-ca": "fr-CA",
    "de": "de-DE",
    "it": "it-IT",
    "nl": "nl-NL",
    "tr": "tr-TR",
    "ru": "ru-RU",
    # Chino, japonés, coreano
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "zh-hans": "zh-CN",
    "zh-hant": "zh-TW",
    "ja": "ja-JP",
    "ko": "ko-KR",
    # Árabe y hebreo
    "ar": "ar-SA",
    "he": "he-IL",
    # Nórdicos y cercanos
    "sv": "sv-SE",
    "fi": "fi-FI",
    "da": "da-DK",
    "no": "no-NO",
    "nb": "nb-NO",
    # Europa del Este
    "pl": "pl-PL",
    "cs": "cs-CZ",
    "sk": "sk-SK",
    "hu": "hu-HU",
    "ro": "ro-RO",
    "uk": "uk-UA",
    "bg": "bg-BG",
    "el": "el-GR",
    "sr": "sr-RS",
    "hr": "hr-HR",
    "sl": "sl-SI",
    "lt": "lt-LT",
    "lv": "lv-LV",
    "et": "et-EE",
    # Idiomas de España adicionales
    "ca": "ca-ES",
    "eu": "eu-ES",
    "gl": "gl-ES",
    # Asia y otros
    "vi": "vi-VN",
    "th": "th-TH",
    "id": "id-ID",
    "ms": "ms-MY",
    "fa": "fa-IR",
    # India
    "hi": "hi-IN",
    "bn": "bn-BD",
    "ta": "ta-IN",
    "te": "te-IN",
    "gu": "gu-IN",
    "mr": "mr-IN",
    "pa": "pa-IN",
}

_BASE_LANGUAGE_FALLBACKS = {
    "en",
    "es",
    "pt",
    "fr",
    "de",
    "it",
    "nl",
    "tr",
    "ru",
    "ja",
    "ko",
    "zh",
}


def _normalize_lang(code: Optional[str]) -> Optional[str]:
    """
    Normalize language code entries to a valid BCP 47 tag.

    Returns None if normalization is not possible.
    """
    if not code:
        return None

    normalized = str(code).strip().lower().replace("_", "-")
    if normalized == "*":
        return None

    if normalized in _MAPPING:
        return _MAPPING[normalized]

    parts = normalized.split("-")
    if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) in (2, 3):
        return f"{parts[0]}-{parts[1].upper()}"

    if len(parts) == 1 and len(parts[0]) == 2 and parts[0] in _BASE_LANGUAGE_FALLBACKS:
        return _MAPPING.get(parts[0])

    return None


def _parse_accept_language(header_value: Optional[str]) -> List[str]:
    """
    Parse Accept-Language header and return language codes in preference order.

    Respects q-values. Does not normalize (that's done by resolve_language_tag).
    """
    if not header_value:
        return []

    items: List[tuple[str, float]] = []
    for part in header_value.split(","):
        trimmed = part.strip()
        if not trimmed:
            continue

        lang = trimmed
        weight = 1.0
        if ";q=" in trimmed:
            lang, q_value = trimmed.split(";q=", 1)
            try:
                weight = float(q_value)
            except (TypeError, ValueError):
                weight = 1.0

        items.append((lang.strip(), weight))

    items.sort(key=lambda entry: entry[1], reverse=True)
    return [lang for lang, _ in items if lang]


def _load_user_preference_callable():
    """Return get_user_preference function if available, otherwise None."""
    try:
        module = import_module("openedx.core.djangoapps.user_api.preferences.api")
    except ImportError:
        return None

    return getattr(module, "get_user_preference", None)


def _get_user_profile_language(user) -> Optional[str]:
    """
    Get user language from profile or preferences.

    Checks: 1) user.profile.language, 2) User preferences (Open edX): 'pref-lang' or 'language'.
    """
    profile_language = getattr(getattr(user, "profile", None), "language", None)
    if profile_language:
        return profile_language

    get_user_preference = _load_user_preference_callable()
    if not callable(get_user_preference):
        return None

    for key in ("pref-lang", "language"):
        preference = get_user_preference(user, key)
        if preference:
            return preference

    return None


def _extend_with_accept_language(candidates: List[str], request) -> None:
    """Append Accept-Language entries from the current request to candidates."""
    if not request:
        return

    meta_header = getattr(request, "META", {}).get("HTTP_ACCEPT_LANGUAGE", "")
    header = meta_header or getattr(getattr(request, "headers", None), "get", lambda *_: "")(
        "Accept-Language",
        "",
    )
    candidates.extend(_parse_accept_language(header))


def _extend_with_active_language(candidates: List[str]) -> None:
    """Append Django's currently active language, if available."""
    lang = translation.get_language()
    if lang:
        candidates.append(lang)


def _iter_normalized(candidates: Iterable[str]) -> Iterable[str]:
    """Yield normalized language tags."""
    for code in candidates:
        normalized = _normalize_lang(code)
        if normalized:
            yield normalized


def resolve_language_tag(user, default: Optional[str] = None) -> Optional[str]:
    """
    Resolve a BCP 47 language tag using multiple sources in cascade order.

    Order:
    1) User profile/preferences language (Open edX)
    2) HTTP Accept-Language (if current request available)
    3) Current thread language (Django)
    4) settings.LANGUAGE_CODE
    Final fallback: settings.POK_DEFAULT_LANGUAGE_TAG or the ``default`` parameter.
    """
    candidates: List[str] = []

    profile_language = _get_user_profile_language(user)
    logger.info("[POK] User profile/preference language: %s", profile_language)
    if profile_language:
        candidates.append(profile_language)

    _extend_with_accept_language(candidates, get_current_request())
    _extend_with_active_language(candidates)

    for normalized in _iter_normalized(candidates):
        return normalized

    site_default = _normalize_lang(getattr(settings, "LANGUAGE_CODE", None))
    if site_default:
        return site_default

    pok_default = _normalize_lang(getattr(settings, "POK_DEFAULT_LANGUAGE_TAG", None))
    if pok_default:
        return pok_default

    if default:
        return _normalize_lang(default) or default

    return None
