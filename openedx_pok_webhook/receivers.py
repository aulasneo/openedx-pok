"""
Open edX signal event handlers for POK certificate integration.
"""
import logging
from .models import Certificate
from .client import PokApiClient

logger = logging.getLogger(__name__)


def _process_certificate_event(event_name, certificate, **kwargs):
    """
    Process certificate events and integrate with POK API.

    Args:
        event_name (str): Name of the event (e.g. CERTIFICATE_CREATED)
        certificate: Certificate object from Open edX
        **kwargs: Additional keyword arguments from the signal
    """
    logger.info(f"================> Processing {event_name} event for POK integration")
    logger.info(
        f"POK Certificate Creation Filter: User: {certificate.user.id}, Course: {course_key}, Mode: {mode}"
    )

    certificate, created = Certificate.objects.get_or_create(
        user_id=user.id,
        course_id=str(course_key),
    )

    pok_client = PokApiClient()

    if not certificate.certificate_id:
        pok_response = pok_client.request_certificate(user, course_key, grade, mode)
        is_success = pok_response.get("success")
        content = pok_response.get("content")

        if is_success:
            certificate.certificate_id = content.get('id')
            certificate.state = content.get('state')
            certificate.view_url = content.get('viewUrl')
            certificate.emission_type = content.get('credential', {}).get('emissionType')
            certificate.emission_date = content.get('credential', {}).get('emissionDate')
            certificate.title = content.get('credential', {}).get('title')
            certificate.emitter = content.get('credential', {}).get('emitter')
            certificate.tags = content.get('credential', {}).get('tags', [])
            certificate.receiver_email = content.get('receiver', {}).get('email')
            certificate.receiver_name = content.get('receiver', {}).get('name')

            certificate.save()
            logger.info(f"Created new POK certificate record for {user.id} in {course_key}")

        else:
            raise Exception(f"POK Certificate Creation when called client")

    else:
        pok_client.get_credential_details(certificate.certificate_id)
        logger.info(f"Getting existing POK certificate record for {user.id} in {course_key}")


def certificate_created_receiver(certificate, **kwargs):
    """
    Handle CERTIFICATE_CREATED signal.

    This function is triggered when a new certificate is created in Open edX.
    It processes the certificate data and sends it to the POK API.

    Args:
        certificate: Certificate object from Open edX
        **kwargs: Additional keyword arguments from the signal
    """
    _process_certificate_event("CERTIFICATE_CREATED", certificate, **kwargs)


def certificate_changed_receiver(certificate, **kwargs):
    """
    Handle CERTIFICATE_CHANGED signal.

    This function is triggered when an existing certificate is updated in Open edX.
    It processes the updated certificate data and sends it to the POK API.

    Args:
        certificate: Certificate object from Open edX
        **kwargs: Additional keyword arguments from the signal
    """
    logger.info(f"================> Processing {'CERTIFICATE_CHANGED'} event for POK integration")


def certificate_revoked_receiver(certificate, **kwargs):
    """
    Handle CERTIFICATE_REVOKED signal.

    This function is triggered when a certificate is revoked in Open edX.
    It notifies the POK API about the revocation.

    Args:
        certificate: Certificate object from Open edX
        **kwargs: Additional keyword arguments from the signal
    """
    logger.info(f"Processing CERTIFICATE_REVOKED event for POK integration")

    # We may want to notify POK that the certificate has been revoked
    # For now, we'll just mark our local record as invalid
    #
    # user = certificate.user
    # course_key = certificate.course_id
    #
    # try:
    #     pok_certificate = Certificate.objects.get(
    #         user_id=user.id,
    #         course_id=str(course_key)
    #     )
    #
    #     pok_certificate.is_valid = False
    #     pok_certificate.save()
    #
    #     logger.info(f"Marked POK certificate as invalid for user {user.id} in course {course_key}")
    # except Certificate.DoesNotExist:
    #     logger.info(f"No POK certificate found for user {user.id} in course {course_key}")
    # except Exception as e:
    #     logger.exception(f"Error updating POK certificate status: {str(e)}")
