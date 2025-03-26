# coding=utf-8
"""
Common Pluggable Django App settings.

"""


def plugin_settings(settings):
    """
    Inject local settings into django settings.
    """

    settings.OPEN_EDX_FILTERS_CONFIG = {
        "org.openedx.learning.certificate.creation.requested.v1": {
            "fail_silently": False,
            "pipeline": [
                "openedx_pok.filters.CertificateCreationRequestedWebFilter"
            ]
        },
        "org.openedx.learning.certificate.render.started.v1": {
            "fail_silently": False,
            "pipeline": [
                "openedx_pok.filters.CertificateRenderStartedWebFilter"
            ]
        }
    }
