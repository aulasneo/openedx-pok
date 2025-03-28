import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)
from edx_django_utils.plugins.constants import PluginURLs, PluginSettings

class OpenedxPokConfig(AppConfig):
    name = 'openedx_pok'
    verbose_name = "Open edX PoK Integration"

    plugin_app = {
        PluginURLs.CONFIG: {
            'cms.djangoapp': {
                PluginURLs.NAMESPACE: 'pok',
                PluginURLs.REGEX: r'^api/v1/',
                PluginURLs.RELATIVE_PATH: 'urls',
            }
        },

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
        }
    }

