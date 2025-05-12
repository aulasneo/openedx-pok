""
"""
POK certificate filter implementations.
"""
import json
import logging

from django.http import HttpResponse, HttpResponseRedirect
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import (
    CertificateRenderStarted, CertificateCreationRequested
)

from django.template.loader import render_to_string

from .models import PokCertificate
from .client import PokApiClient
from openedx.core.lib.courses import get_course_by_id
from organizations import api as organizations_api
from django.conf import settings
from opaque_keys.edx.keys import CourseKey

logger = logging.getLogger(__name__)

def _get_custom_params(course_key):

    platform = getattr(settings, 'PLATFORM_NAME', "")
    course_instance = get_course_by_id(course_key)
    course_cert_data = course_instance.certificates.get("certificates")[0]
    signatory = course_cert_data.get("signatories", [{}])[0]
    signatory_name = signatory.get("name", "")
    signatory_title = signatory.get("title", "")
    signatory_organization = signatory.get("organization", "")

    return {
        "platform": platform,
        "signatory_name": signatory_name,
        "signatory_title": signatory_title,
        "signatory_organization": signatory_organization,
    }

def _get_org_name(course_key) -> str:
    course_instance = get_course_by_id(course_key)

    course_org_display = course_instance.display_organization
    if course_org_display:
        return course_org_display

    organizations = organizations_api.get_course_organizations(course_key=course_key)
    if organizations:
        organization = organizations[0]
        org = organization.get('short_name')
        return organization.get('name', org)


class CertificateCreatedFilter(PipelineStep):
    """
    Filter to handle the creation of POK certificates when a certificate is issued.
    """

    def run_filter(self, **kwargs):
        logger.info(f"[POK] CertificateCreatedFilter kwargs context: {json.dumps({k: str(v) for k, v in kwargs.items()}, indent=2)}")

        user = kwargs.get("user")
        course_key = kwargs.get("course_key")
        grade_obj = kwargs.get("grade")
        enrollment_mode = kwargs.get("enrollment_mode")

        if not user or not course_key:
            logger.error("[POK] Missing user or course_key in certificate creation context.")
            raise CertificateCreationRequested.PreventCertificateCreation(
                message="[POK] Missing required context to create certificate."
            )

        course_id_str = str(course_key)

        try:
            logger.info(f"[POK] Triggered CertificateCreatedFilter for user={user.id}, course={course_id_str}")
            course_instance = get_course_by_id(course_key)
            course_cert_data = course_instance.certificates.get("certificates")[0]
            course_title = course_cert_data.get("course_title")

            if not course_title:
                course_title = getattr(course_instance, "display_name", "")
                logger.info(f"[POK] course_title was empty, fallback to course_instance.display_name: {course_title}")

            user_name = getattr(user.profile, "name")
            if not user_name:
                user_name = user.username

            custom_params = _get_custom_params(course_key)
            custom_params["grade"] = str(round(grade_obj.percent * 100)) if grade_obj and hasattr(grade_obj, "percent") else ""

            pok_certificate, _ = PokCertificate.objects.get_or_create(
                user_id=user.id,
                course_id=course_id_str,
            )

            pok_client = PokApiClient(course_id_str)

            if not pok_certificate.pok_certificate_id:
                response = pok_client.request_certificate(
                    user=user,
                    course_key=course_id_str,
                    mode=enrollment_mode,
                    organization=_get_org_name(course_key),
                    course_title=course_title,
                    **custom_params,
                )

                if response.get("success"):
                    data = response["content"]

                    pok_certificate.pok_certificate_id = data.get("id")
                    pok_certificate.state = data.get("state")
                    pok_certificate.view_url = data.get("viewUrl")
                    pok_certificate.emission_type = data.get("credential", {}).get("emissionType")
                    pok_certificate.emission_date = data.get("credential", {}).get("emissionDate")
                    pok_certificate.title = data.get("credential", {}).get("title")
                    pok_certificate.emitter = data.get("credential", {}).get("emitter")
                    pok_certificate.tags = data.get("credential", {}).get("tags", [])
                    pok_certificate.receiver_email = data.get("receiver", {}).get("email")
                    pok_certificate.receiver_name = user_name
                    pok_certificate.save()

                    logger.info(f"[POK] Certificate created and stored for user={user.id}, course={course_id_str}")
                else:
                    error_msg = f"[POK] API certificate request failed: {response.get('error')}"
                    logger.error(error_msg)
                    raise CertificateCreationRequested.PreventCertificateCreation(message=error_msg)
            else:
                logger.info(f"[POK] Existing certificate already found for user={user.id}, course={course_id_str}")

        except Exception as e:
            logger.exception(f"[POK] Unexpected error in CertificateCreatedFilter: {str(e)}")
            raise CertificateCreationRequested.PreventCertificateCreation(
                message=f"[POK] Unhandled exception during certificate creation: {str(e)}"
            )

        return kwargs


class CertificateRenderFilter(PipelineStep):
    """
    Process CertificateRenderStarted filter to redirect to POK certificate.

    This filter intercepts certificate render requests and redirects the user
    to the POK certificate page if available.
    """

    def run_filter(self, context, custom_template):  # pylint: disable=arguments-differ
        user_id = context.get('accomplishment_user_id')
        course_id = context.get('course_id')

        if not user_id or not course_id:
            logger.warning("Missing user_id or course_id in certificate render context")
            return {"context": context, "custom_template": custom_template}

        pok_client = PokApiClient(course_id)

        if not pok_client.api_key:
            logger.warning("POK API key is not set. Skipping POK certificate rendering.")
            return {"context": context, "custom_template": custom_template}

        try:
            certificate = PokCertificate.objects.get(
                user_id=user_id,
                course_id=course_id,
                state="emitted"
            )
            state = "emitted"
        except PokCertificate.DoesNotExist:
            try:
                certificate = PokCertificate.objects.get(
                    user_id=user_id,
                    course_id=course_id,
                    state="processing"
                )
                pok_response = pok_client.get_credential_details(certificate.pok_certificate_id)
                content = pok_response.get("content", {})
                state = content.get("state", "processing")
                certificate.state = state
                certificate.save()
            except PokCertificate.DoesNotExist:
                certificate = None
                state = "preview"

        if state == "emitted":
            try:
                response = pok_client.get_credential_details(certificate.pok_certificate_id, decrypted=True)

                if not response.get("success"):
                    raise Exception(f"POK API returned failure: {response.get('error')}")

                content = response.get("content", {})
                image_content = content.get("location")

                if not image_content:
                    raise Exception("POK response missing 'location' for decrypted image.")

                html_content = render_to_string("openedx_pok/certificate_pok.html", {
                    'document_title': context.get('document_title', 'Certificate'),
                    'logo_src': context.get('logo_src', ''),
                    'accomplishment_copy_name': context.get('accomplishment_copy_name', 'Student'),
                    'image_content': image_content,
                    'certificate_url': certificate.view_url
                })

            except Exception as e:
                logger.error(f"Failed to render emitted certificate from POK: {str(e)}")
                html_content = render_to_string("openedx_pok/certificate_error.html", {
                    'document_title': context.get('document_title', 'Error'),
                    'error_message': "We couldn't render your certificate at this time. Please try again later.",
                    'course_id': course_id,
                    'user_id': user_id,
                })
                raise CertificateRenderStarted.RenderCustomResponse(
                    message="Error rendering POK certificate",
                    response=HttpResponse(
                        content=html_content,
                        content_type="text/html; charset=utf-8",
                        status=500
                    )
                )

        elif state == "processing":
            html_content = render_to_string("openedx_pok/certificate_processing.html", {
                'document_title': context.get('document_title', 'Certificate in process'),
                'course_id': course_id,
                'user_id': user_id,
            })

        elif state == "preview":
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User with id={user_id} not found in database.")
                return {"context": context, "custom_template": custom_template}

            course_key = CourseKey.from_string(course_id)
            custom_params = _get_custom_params(course_key)
            custom_params['grade'] = "N/A"
            organization = _get_org_name(course_key)

            preview_response = pok_client.get_template_preview(
                user=user,
                organization=organization,
                course_title=context.get("certificate_data", {}).get("course_title") or context.get("accomplishment_copy_course_name"),
                **custom_params
            )

            if preview_response.get("success"):
                preview_url = preview_response.get("preview_url")
                if not preview_url:
                    logger.error(f"POK preview URL not found in response: {json.dumps(preview_response, indent=2)}")
                    return {"context": context, "custom_template": custom_template}

                html_content = render_to_string("openedx_pok/certificate_preview.html", {
                    'document_title': "Certificate Preview",
                    'preview_url': preview_url,
                    'user_id': user_id,
                    'course_id': course_id,
                    'logo_src': context.get('logo_src', ''),
                    'learning_microfrontend_url': f"{settings.LEARNING_MICROFRONTEND_URL}/course/{course_id}/progress",
                })

                raise CertificateRenderStarted.RenderCustomResponse(
                    message="Rendering certificate preview",
                    response=HttpResponse(html_content)
                )
            else:
                logger.error(f"POK preview request failed: {preview_response.get('error')}")
                return {"context": context, "custom_template": custom_template}


        else:
            html_content = render_to_string("openedx_pok/certificate_error.html", {
                'document_title': context.get('document_title', 'Error'),
                'error_message': f"The current state is '{state}'. Please try again later.",
                'course_id': course_id,
                'user_id': user_id,
                'learning_microfrontend_url': f"{settings.LEARNING_MICROFRONTEND_URL}/course/{course_id}/progress",
            })

        raise CertificateRenderStarted.RenderCustomResponse(
            message=f"Rendering certificate page (state={state})",
            response=HttpResponse(
                content=html_content,
                content_type="text/html; charset=utf-8",
                status=200
            )
        )
