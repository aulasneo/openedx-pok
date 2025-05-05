# coding=utf-8
"""
Common settings for openedx_pok.
"""
import logging

logger = logging.getLogger(__name__)

def plugin_settings(settings):
    """
    Defines POK webhook settings for Open edX environments.
    """

    # POK API config
    settings.POK_API_URL = 'https://api.pok.tech/'
    settings.POK_TIMEOUT = 60
    settings.POK_TEMPLATE_ID = ""
    settings.POK_API_KEY = ""

    # Log inicio de configuración
    logger.info("[POK] Applying plugin_settings for openedx_pok...")

    # Ensure OPEN_EDX_FILTERS_CONFIG exists
    if not hasattr(settings, "OPEN_EDX_FILTERS_CONFIG"):
        settings.OPEN_EDX_FILTERS_CONFIG = {}

    # ----------------------------
    # Certificate Render Filter
    # ----------------------------
    render_filter_key = "org.openedx.learning.certificate.render.started.v1"
    render_pipeline = settings.OPEN_EDX_FILTERS_CONFIG.get(render_filter_key, {
        "fail_silently": False,
        "pipeline": []
    })

    if "openedx_pok.filters.CertificateRenderFilter" not in render_pipeline["pipeline"]:
        render_pipeline["pipeline"].append("openedx_pok.filters.CertificateRenderFilter")
        logger.info("[POK] Added CertificateRenderFilter to render.started.v1 pipeline")

    settings.OPEN_EDX_FILTERS_CONFIG[render_filter_key] = render_pipeline

    # ----------------------------
    # Certificate Created Filter
    # ----------------------------
    created_filter_key = "org.openedx.learning.certificate.creation.requested.v1"
    created_pipeline = settings.OPEN_EDX_FILTERS_CONFIG.get(created_filter_key, {
        "fail_silently": False,
        "pipeline": []
    })

    if "openedx_pok.filters.CertificateCreatedFilter" not in created_pipeline["pipeline"]:
        created_pipeline["pipeline"].append("openedx_pok.filters.CertificateCreatedFilter")
        logger.info("[POK] Added CertificateCreatedFilter to creation.requested.v1 pipeline")

    settings.OPEN_EDX_FILTERS_CONFIG[created_filter_key] = created_pipeline

    logger.info("[POK] Plugin filters configured successfully.")
