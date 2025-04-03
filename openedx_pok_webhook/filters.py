"""
POK certificate filter implementations.
"""
import logging

from django.http import HttpResponse
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import (
    CertificateCreationRequested,
    CertificateRenderStarted,
    CourseAboutRenderStarted,
    DashboardRenderStarted
)

from django.template.loader import render_to_string

from .models import CertificatePokApi
from .client import PokApiClient

logger = logging.getLogger(__name__)


# class CertificateCreationFilter(PipelineStep):
#     """
#     Process CertificateCreationRequested filter to call POK API.
#
#     This filter intercepts certificate creation requests, calls the POK API,
#     and stores the response in the Certificate model.
#     """
#
#     def run_filter(self, user, course_key, mode, status, grade, generation_mode):  # pylint: disable=arguments-differ
#         """
#         Execute the filter.
#
#         Arguments:
#             user (User): is a Django User object.
#             course_key (CourseKey): course key associated with the certificate.
#             mode (str): mode of the certificate.
#             status (str): status of the certificate.
#             grade (CourseGrade): user's grade in this course run.
#             generation_mode (str): Options are "self" (implying the user generated the cert themselves)
#                                   and "batch" for everything else.
#         """
#         logger.info(
#             f"POK Certificate Creation Filter: User: {user.id}, Course: {course_key}, Mode: {mode}"
#         )
#
#         certificate, created = Certificate.objects.get_or_create(
#             user_id=user.id,
#             course_id=str(course_key),
#         )
#
#         pok_client = PokApiClient()
#
#         if not certificate.certificate_id:
#             pok_response = pok_client.request_certificate(user, course_key, grade, mode)
#             is_success = pok_response.get("success")
#             content = pok_response.get("content")
#
#             if is_success:
#                 certificate.certificate_id = content.get('id')
#                 certificate.state = content.get('state')
#                 certificate.view_url = content.get('viewUrl')
#                 certificate.emission_type = content.get('credential', {}).get('emissionType')
#                 certificate.emission_date = content.get('credential', {}).get('emissionDate')
#                 certificate.title = content.get('credential', {}).get('title')
#                 certificate.emitter = content.get('credential', {}).get('emitter')
#                 certificate.tags = content.get('credential', {}).get('tags', [])
#                 certificate.receiver_email = content.get('receiver', {}).get('email')
#                 certificate.receiver_name = content.get('receiver', {}).get('name')
#
#                 certificate.save()
#                 logger.info(f"Created new POK certificate record for {user.id} in {course_key}")
#
#             else:
#                 raise Exception(f"POK Certificate Creation when called client")
#
#         else:
#             pok_client.get_credential_details(certificate.certificate_id)
#             logger.info(f"Getting existing POK certificate record for {user.id} in {course_key}")
#
#
#         # Continue with normal certificate creation process
#         return {
#             "user": user,
#             "course_key": course_key,
#             "mode": mode,
#             "status": status,
#             "grade": grade,
#             "generation_mode": generation_mode,
#         }


class CertificateRenderFilter(PipelineStep):
    """
    Process CertificateRenderStarted filter to redirect to POK certificate.

    This filter intercepts certificate render requests and redirects the user
    to the POK certificate page if available.
    """

    def run_filter(self, context, custom_template):  # pylint: disable=arguments-differ
        """
        Execute the filter.

        Arguments:
            context (dict): context dictionary for certificate template.
            custom_template (CertificateTemplate): edxapp object representing custom web certificate template.
        """
        user_id = context.get('accomplishment_user_id')
        course_id = context.get('course_id')

        if not user_id or not course_id:
            logger.warning("Missing user_id or course_id in certificate render context")
            return {"context": context, "custom_template": custom_template}

        logger.info(f"POK Certificate Render Filter: User: {user_id}, Course: {course_id}")

        pok_client = PokApiClient()

        try:
            certificate = CertificatePokApi.objects.get(
                user_id=user_id,
                course_id=course_id,
                state="emitted"
            )
            state = certificate.state

        except CertificatePokApi.DoesNotExist:
            certificate = CertificatePokApi.objects.get(
                user_id=user_id,
                course_id=course_id
            )
            if certificate.state == "processing":
                pok_response = pok_client.get_credential_details(certificate.pok_certificate_id)
                content = pok_response.get("content", {})
                state = content.get('state')
                certificate.state = state
                certificate.save()
            else:
                state = certificate.state

        logger.info(f"Certificate state from POK API: {state}")

        if state == "emitted":
            response = pok_client.get_credential_details(certificate.pok_certificate_id, decrypted=True)
            image_content = response.get("content", {}).get("location", certificate.view_url)
            html_content = render_to_string("openedx_pok_webhook/certificate_pok.html", {
                'document_title': context.get('document_title', 'Certificate'),
                'logo_src': context.get('logo_src', ''),
                'accomplishment_copy_name': context.get('accomplishment_copy_name', 'Student'),
                'image_content': image_content,
                'certificate_url': certificate.view_url,
            })

        elif state == "processing":
            html_content = render_to_string("openedx_pok_webhook/certificate_processing.html", {
                'document_title': context.get('document_title', 'Certificate in process'),
                'course_id': course_id,
                'user_id': user_id,
            })

        else:
            html_content = render_to_string("openedx_pok_webhook/certificate_error.html", {
                'document_title': context.get('document_title', 'Error'),
                'error_message': f"The current state is '{state}'. Please try again later.",
                'course_id': course_id,
                'user_id': user_id,
            })

        http_response = HttpResponse(
            content=html_content,
            content_type="text/html; charset=utf-8",
            status=200
        )

        raise CertificateRenderStarted.RenderCustomResponse(
            message=f"Rendering certificate page (state={state})",
            response=http_response
    )
