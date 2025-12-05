"""App configuration for the openedx_pok plugin."""

from django.apps import AppConfig
from edx_django_utils.plugins.constants import PluginSettings, PluginURLs


class OpenedxPokConfig(AppConfig):
    """Configuration for the openedx_pok Django application."""

    name = 'openedx_pok'
    verbose_name = "POK"
    default_auto_field = 'django.db.models.BigAutoField'

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
