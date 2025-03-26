"""
openedx_webhooks Django application initialization.
"""
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

signals = [
    "STUDENT_REGISTRATION_COMPLETED",
    "SESSION_LOGIN_COMPLETED",
    "COURSE_ENROLLMENT_CREATED",
    "COURSE_ENROLLMENT_CHANGED",
    "COURSE_UNENROLLMENT_COMPLETED",
    "CERTIFICATE_CREATED",
    "CERTIFICATE_CHANGED",
    "CERTIFICATE_REVOKED",
    "COHORT_MEMBERSHIP_CHANGED",
    "COURSE_DISCUSSIONS_CHANGED"
]

class OpenedxPokConfig(AppConfig):
    """
    Configuration for the pok Django application.
    """
    name = 'openedx_pok'

    plugin_app = {
        "settings_config": {
            "lms.djangoapp": {
                "common": {"relative_path": "settings.common"},
                "test": {"relative_path": "settings.test"},
            },
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

    logger.info("Signals registerd")


logger.info("Calling pok app")
