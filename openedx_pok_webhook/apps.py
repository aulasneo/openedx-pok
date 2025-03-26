"""
openedx_pok_webhook Django application initialization.
"""

from django.apps import AppConfig


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
        }
    }
