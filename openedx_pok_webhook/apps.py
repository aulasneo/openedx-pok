"""
openedx_pok_webhook Django application initialization.
"""

from django.apps import AppConfig
from edx_django_utils.plugins.constants import PluginURLs, PluginSettings


signals = [
    "CERTIFICATE_CREATED",
    "CERTIFICATE_CHANGED",
]

class OpenedxPokWebhookConfig(AppConfig):
    """
    Configuration for the openedx_pok_webhook Django application.
    """

    name = 'openedx_pok_webhook'

    plugin_app = {
        # PluginURLs.CONFIG: {
        #     'cms.djangoapp': {
        #         PluginURLs.NAMESPACE: 'get_permissions',
        #         PluginURLs.REGEX: r'^api/v1/',
        #         PluginURLs.RELATIVE_PATH: 'urls',
        #     }
        # },

        PluginSettings.CONFIG: {
            'lms.djangoapp': {
                'common': {
                    PluginSettings.RELATIVE_PATH: 'settings.common',
                },
            },
            'cms.djangoapp': {
                'common': {
                    PluginSettings.RELATIVE_PATH: 'settings.common',
                },
            }
        },
        "signals_config": {
            "lms.djangoapp": {
                "relative_path": "receivers",
                "receivers": [
                    {
                        "receiver_func_name": signal.lower() + "_receiver",
                        "signal_path": "openedx_events.learning.signals." + signal
                    } for signal in signals
                ],
            }
        },
    }
