# coding=utf-8
"""
Common settings for openedx_pok_webhook.
"""

def plugin_settings(settings):
    """
    Defines POK webhook settings for Open edX environments.
    """
    # POK API settings
    settings.POK_API_URL = 'https://api.pok.tech/'
    settings.POK_TIMEOUT = 20
    settings.POK_TEMPLATE_ID = ""
    settings.POK_API_KEY = ""

    # Configure filters
    settings.OPEN_EDX_FILTERS_CONFIG = getattr(settings, 'OPEN_EDX_FILTERS_CONFIG', {})

    # Filter for certificate rendering
    certificate_render_filter = settings.OPEN_EDX_FILTERS_CONFIG.get(
        "org.openedx.learning.certificate.render.started.v1",
        {"fail_silently": False, "pipeline": []}
    )

    if "openedx_pok_webhook.filters.CertificateRenderFilter" not in certificate_render_filter["pipeline"]:
        certificate_render_filter["pipeline"].append(
            "openedx_pok_webhook.filters.CertificateRenderFilter"
        )

    settings.OPEN_EDX_FILTERS_CONFIG["org.openedx.learning.certificate.render.started.v1"] = certificate_render_filter