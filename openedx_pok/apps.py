from django.apps import AppConfig
from edx_django_utils.plugins.constants import PluginURLs, PluginSettings

# signals = [
#     "CERTIFICATE_CREATED",
#     "CERTIFICATE_CHANGED",
# ]

class OpenedxPokConfig(AppConfig):
    name = 'openedx_pok'
    verbose_name = "POK"

    plugin_app = {
        PluginURLs.CONFIG: {
            'cms.djangoapp': {
                PluginURLs.NAMESPACE: 'openedx_pok',
                PluginURLs.REGEX: r'^api/pok/',
                PluginURLs.RELATIVE_PATH: 'urls',
            },
            'lms.djangoapp': {
                PluginURLs.NAMESPACE: 'openedx_pok',
                PluginURLs.REGEX: r'^api/pok/',
                PluginURLs.RELATIVE_PATH: 'urls',
            },
        },
        PluginSettings.CONFIG: {
            'cms.djangoapp': {
                'common': {
                    PluginSettings.RELATIVE_PATH: 'settings.common',
                },
            },
            'lms.djangoapp': {
                'common': {
                    PluginSettings.RELATIVE_PATH: 'settings.common',
                },
            },
        },
        # "signals_config": {
        #     "lms.djangoapp": {
        #         "relative_path": "receivers",
        #         "receivers": [
        #             {
        #                 "receiver_func_name": signal.lower() + "_receiver",
        #                 "signal_path": "openedx_events.learning.signals." + signal
        #             } for signal in signals
        #         ],
        #     }
        # },
    }
