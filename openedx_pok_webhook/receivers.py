"""
Open edX signal event handlers for POK certificate integration.
"""
import logging

from .models import PokCertificate
from .client import PokApiClient
from openedx.core.lib.courses import get_course_by_id # pylint: disable=import-error
from django.conf import settings
logger = logging.getLogger(__name__)


def _process_certificate_event(event_name, certificate, **kwargs):
    """
    Process certificate events and integrate with POK API.

    Args:
        event_name (str): Name of the event (e.g. CERTIFICATE_CREATED)
        certificate: Certificate object from Open edX
        **kwargs: Additional keyword arguments from the signal
    """
    logger.info(f"Processing {event_name} event for POK integration")
    course_instance = get_course_by_id(certificate.course.course_key)
    platform = getattr(settings, 'PLATFORM_NAME', "OpenedX")
    certificate_course_info = course_instance.certificates.get("certificates")[0]
    course_title = certificate_course_info.get("course_title")
    signatories = certificate_course_info.get("signatories")[0]
    signatory_name = signatories.get("name")
    organization = signatories.get("organization")
    course_id = certificate.course.course_key.__str__()
    user = certificate.user
    mode = certificate.mode
    logger.info(
        f"POK Certificate Creation Receiver: User: {user.id}, Course: {course_id}, Mode: {mode}"
    )

    pok_certificate, created = PokCertificate.objects.get_or_create(
        user_id=user.id,
        course_id=course_id,
    )

    pok_client = PokApiClient(course_id)
    if not pok_client.api_key:
        logger.warning("POK API key is not set. Skipping POK certificate creation.")
        return 

    if not pok_certificate.pok_certificate_id:
        pok_response = pok_client.request_certificate(user,
                                                      course_id,
                                                      certificate.grade,
                                                      mode,
                                                      platform,
                                                      signatory_name,
                                                      organization,
                                                      course_title
                                                     )
        is_success = pok_response.get("success")
        content = pok_response.get("content")

        if is_success:
            pok_certificate.pok_certificate_id = content.get('id')
            pok_certificate.state = content.get('state')
            pok_certificate.view_url = content.get('viewUrl')
            pok_certificate.emission_type = content.get('credential', {}).get('emissionType')
            pok_certificate.emission_date = content.get('credential', {}).get('emissionDate')
            pok_certificate.title = content.get('credential', {}).get('title')
            pok_certificate.emitter = content.get('credential', {}).get('emitter')
            pok_certificate.tags = content.get('credential', {}).get('tags', [])
            pok_certificate.receiver_email = content.get('receiver', {}).get('email')
            pok_certificate.receiver_name = content.get('receiver', {}).get('name')

            pok_certificate.save()
            logger.info(f"Created new POK certificate record for {user.id} in {course_id}")

        else:
            raise Exception(f"POK Certificate Creation when called client")

    else:
        pok_client.get_credential_details(pok_certificate.pok_certificate_id)
        logger.info(f"Getting existing POK certificate record for {user.id} in {course_id}")


def certificate_created_receiver(certificate, **kwargs):
    """
    Handle CERTIFICATE_CREATED signal.

    This function is triggered when a new certificate is created in Open edX.
    It processes the certificate data and sends it to the POK API.

    Args:
        certificate: Certificate object from Open edX
        **kwargs: Additional keyword arguments from the signal
    """
    logger.info(f"Processing CERTIFICATE_CREATED event for POK integration")
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
