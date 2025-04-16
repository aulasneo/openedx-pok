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



class CertificateRenderFilter(PipelineStep):
    """
    Process CertificateRenderStarted filter to redirect to POK certificate.

    This filter intercepts certificate render requests and redirects the user
    to the POK certificate page if available.
    """

    def run_filter(self, context, custom_template):  # pylint: disable=arguments-differ
        print("✅ --------------------------------------------------")
        """
        Execute the filter.

        Arguments:
            context (dict): context dictionary for certificate template.
            custom_template (CertificateTemplate): edxapp object representing custom web certificate template.
        """
        user_id = context.get('accomplishment_user_id')
        print("✅ USERRRRRRR", user_id)
        course_id = context.get('course_id')
        print("✅ COURSEEEEEE", course_id)
        if not user_id or not course_id:
            logger.warning("Missing user_id or course_id in certificate render context")
            return {"context": context, "custom_template": custom_template}

        logger.info(f"POK Certificate Render Filter: User: {user_id}, Course: {course_id}")

        pok_client = PokApiClient(course_id)
        print("✅ POK_CLIENT ---------------------------", pok_client)

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
