from django.apps import AppConfig
from edx_django_utils.plugins.constants import PluginURLs, PluginSettings

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
    }
