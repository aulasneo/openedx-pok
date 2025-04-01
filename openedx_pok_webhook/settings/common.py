# coding=utf-8
"""
Common settings for openedx_pok_webhook.
"""

def plugin_settings(settings):
    """
    Defines POK webhook settings for Open edX environments.
    """
    # POK API settings
    # settings.POK_API_BASE_URL = getattr(settings, 'ENV_TOKENS', {}).get(
    #     'POK_API_BASE_URL',
    #     'https://pok.example.com/api/'
    # )
    # settings.POK_API_KEY = getattr(settings, 'AUTH_TOKENS', {}).get(
    #     'POK_API_KEY',
    #     ''
    # )
    settings.POK_API_TIMEOUT = getattr(settings, 'ENV_TOKENS', {}).get(
        'POK_API_TIMEOUT',
        10
    )

    # Configure filters
    settings.OPEN_EDX_FILTERS_CONFIG = getattr(settings, 'OPEN_EDX_FILTERS_CONFIG', {})

    # Filter for certificate creation
    certificate_creation_filter = settings.OPEN_EDX_FILTERS_CONFIG.get(
        "org.openedx.learning.certificate.creation.requested.v1",
        {"fail_silently": False, "pipeline": []}
    )
    #
    # if "openedx_pok_webhook.filters.CertificateCreationFilter" not in certificate_creation_filter["pipeline"]:
    #     certificate_creation_filter["pipeline"].append(
    #         "openedx_pok_webhook.filters.CertificateCreationFilter"
    #     )

    settings.OPEN_EDX_FILTERS_CONFIG["org.openedx.learning.certificate.creation.requested.v1"] = certificate_creation_filter

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
