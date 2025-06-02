"""
POK certificate filter implementations.
"""

import json
import logging
import six

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import quote
from django.urls import reverse

from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.courses import get_course_by_id
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
from organizations import api as organizations_api
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import (
    CertificateRenderStarted, CertificateCreationRequested
)

from .models import CertificateTemplate, PokCertificate
from .client import PokApiClient

logger = logging.getLogger(__name__)

# .. toggle_name: module_pok.enable
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_description: Enables use of the module_pok plugin for Open edX.
# .. toggle_default: False
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2024-04-03
# .. toggle_expiration_date: 2025-08-12
# .. toggle_will_remain_in_codebase: True
# .. toggle_tickets: none
# .. toggle_status: supported
ENABLE_POK_COURSE_FLAG = CourseWaffleFlag('module_pok.enable', __name__)

# Check if the POK module is enabled for the course
def is_pok_enabled(course_key: CourseKey | None = None) -> bool:
    """
    Returns True if the POK module is enabled for the given course.
    """
    return ENABLE_POK_COURSE_FLAG.is_enabled(course_key)


# === Helper Functions ===

def _get_signatory_data(course_cert_data):
    """
    Extracts signatory information (name, title, organization) from the course certificate data.
    """
    signatory = course_cert_data.get("signatories", [{}])[0]
    return {
        "signatory_name": signatory.get("name", ""),
        "signatory_title": signatory.get("title", ""),
        "signatory_organization": signatory.get("organization", "")
    }

def _get_custom_params(course_key):
    """
    Builds a dictionary with custom parameters to send to the POK API.
    Includes platform name and signatory info.
    """
    course = get_course_by_id(course_key)
    cert_data = course.certificates.get("certificates")[0]
    params = {
        "platform": getattr(settings, 'PLATFORM_NAME', ""),
        **_get_signatory_data(cert_data),
    }
    return params

def _get_org_name(course_key):
    """
    Returns the organization name for the course, using either display_organization
    or the organizations API fallback.
    """
    course = get_course_by_id(course_key)
    if course.display_organization:
        return course.display_organization

    organizations = organizations_api.get_course_organizations(course_key=course_key)
    if organizations:
        return organizations[0].get('name', organizations[0].get('short_name'))
    return ""

def build_social_links(view_url, image_content, course_title, platform_name, twitter_account=None):
    """
    Build social share links using the certificate view_url and image_content.
    """
    tweet_text = f"¡Obtuve mi certificado '{course_title}' en {platform_name}! {image_content}"

    return {
        'facebook': f"https://www.facebook.com/sharer/sharer.php?u={quote(image_content)}",
        'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={quote(image_content)}",
        'twitter': f"https://twitter.com/intent/tweet?text={quote(tweet_text)}",
        'image_content': image_content
    }

# === Certificate Creation Filter ===

class CertificateCreatedFilter(PipelineStep):
    """
    Triggered when a certificate is issued.
    Handles generation and storage of a POK certificate.
    """

    def run_filter(self, **kwargs):
        """
        Handles the full process of creating a POK certificate.
        - Checks if certificate already exists.
        - If not, requests one via POK API.
        - Stores metadata returned by the API into the PokCertificate model.
        """
        if not is_pok_enabled(kwargs.get("course_key")):
            logger.info("[POK] POK module is not enabled for this course, skipping certificate creation.")
            return

        user = kwargs.get("user")
        course_key = kwargs.get("course_key")
        grade = kwargs.get("grade")
        enrollment_mode = kwargs.get("enrollment_mode")

        if not user or not course_key:
            raise CertificateCreationRequested.PreventCertificateCreation("[POK] Missing required context to create certificate.")

        course_id = str(course_key)
        user_name = getattr(user.profile, "name", "") or user.username
        custom_params = _get_custom_params(course_key)
        if grade and hasattr(grade, "percent"):
            custom_params["grade"] = str(round(grade.percent * 100))

        try:
            pok_certificate, _ = PokCertificate.objects.get_or_create(user_id=user.id, course_id=course_id)

            if pok_certificate.pok_certificate_id:
                logger.info(f"[POK] Certificate already exists for user={user.id}, course={course_id}")
                return kwargs

            course = get_course_by_id(course_key)
            course_cert_data = course.certificates.get("certificates")[0]
            course_title = course_cert_data.get("course_title") or course.display_name
            
            try:
                template = CertificateTemplate.objects.get(course=course_key)
            except CertificateTemplate.DoesNotExist:
                template = None

            client = PokApiClient(course_id)
            response = client.request_certificate(
                user=user,
                course_key=course_id,
                mode=enrollment_mode,
                organization=_get_org_name(course_key),
                course_title=course_title,
                **custom_params
            )

            if not response.get("success"):
                raise CertificateCreationRequested.PreventCertificateCreation(
                    message=f"[POK] Certificate API failed: {response.get('error')}"
                )

            content = response["content"]
            credential = content.get("credential", {})
            receiver = content.get("receiver", {})

            pok_certificate.pok_certificate_id = content.get("id")
            pok_certificate.state = content.get("state")
            pok_certificate.view_url = content.get("viewUrl")
            pok_certificate.emission_type = credential.get("emissionType")
            pok_certificate.emission_date = credential.get("emissionDate")
            pok_certificate.title = credential.get("title")
            pok_certificate.emitter = credential.get("emitter")
            pok_certificate.tags = credential.get("tags", [])
            pok_certificate.page = template.page_id if template and template.page_id is not None else settings.POK_PAGE_ID
            pok_certificate.receiver_email = receiver.get("email")
            pok_certificate.receiver_name = user_name
            pok_certificate.save()

            logger.info(f"[POK] Certificate created for user={user.id}, course={course_id}")

        except Exception as e:
            logger.exception("[POK] Unexpected error during certificate creation: %s", str(e))
            raise CertificateCreationRequested.PreventCertificateCreation(
                message=f"[POK] Unexpected error: {str(e)}"
            )

        return kwargs

# === Certificate Render Filter ===

class CertificateRenderFilter(PipelineStep):
    """
    Renders or previews the certificate when a user views it.
    """
    def run_filter(self, context, custom_template):  # pylint: disable=arguments-differ
        """
        Entry point for the filter.
        Determines whether to show a preview (for unissued certs) or render an issued certificate.
        """
        course_id = context.get("course_id")
        course_key = CourseKey.from_string(course_id)
        
        if not is_pok_enabled(course_key):
            logger.info("[POK] POK module is not enabled for this course, skipping certificate rendering.")
            return 
        
        user_id = context.get("accomplishment_user_id")

        if not user_id or not course_id:
            logger.warning("[POK] Missing user_id or course_id in render context")
            return {"context": context, "custom_template": custom_template}

        client = PokApiClient(course_id)

        if not PokCertificate.objects.filter(user_id=user_id, course_id=course_id).exists():
            return self._render_preview(context, user_id, course_id, client)

        return self._render_issued_certificate(context, user_id, course_id, client)

    def _render_preview(self, context, user_id, course_id, client):
        """
        Renders a certificate preview using the POK API.
        This is typically shown in Studio or in cases where no certificate exists yet.
        """
        try:
            User = get_user_model()
            user = User.objects.get(id=user_id)
            course_key = CourseKey.from_string(course_id)
            custom_params = _get_custom_params(course_key)

            response = client.get_template_preview(
                user=user,
                organization=_get_org_name(course_key),
                course_title=context.get("certificate_data", {}).get("course_title") or context.get("accomplishment_copy_course_name"),
                **custom_params
            )

            if not response.get("success"):
                logger.error(f"[POK] Preview API failed: {response.get('error')}")
                return

            preview_url = response["preview_url"]
            authoring_url = settings.LEARNING_MICROFRONTEND_URL.rstrip('/').replace('/learning', '/authoring').replace(':2000', ':2001')

            html = render_to_string("openedx_pok/certificate_preview.html", {
                "document_title": "Certificate Preview",
                "preview_url": preview_url,
                "user_id": user_id,
                "course_id": course_id,
                "authoring_microfrontend_url": f"{authoring_url}/course/{course_id}/certificates",
                "logo_src": context.get("logo_src", "")
            })

            raise CertificateRenderStarted.RenderCustomResponse(
                "Rendering certificate preview",
                HttpResponse(html, content_type="text/html; charset=utf-8", status=200)
            )

        except CertificateRenderStarted.RenderCustomResponse as r:
            raise r
        except Exception as e:
            logger.exception(f"[POK] Error rendering preview: {str(e)}")

    def _render_issued_certificate(self, context, user_id, course_id, client):
        """
        Determines the current certificate state and routes rendering accordingly.
        Supports 'emitted' and 'processing' states, or shows an error if no cert is found.
        """

        try:
            certificate = PokCertificate.objects.filter(user_id=user_id, course_id=course_id).first()
            if not certificate:
                raise ValueError("No certificate record found")

            if certificate.state == "emitted":
                return self._render_emitted_certificate(context, certificate, user_id, client)
            elif certificate.state == "processing":
                return self._render_processing_certificate(context, certificate, client)
            else:
                return self._render_error_page(context, "Invalid certificate state", course_id, user_id)

        except CertificateRenderStarted.RenderCustomResponse as r:
            raise r
        except Exception as e:
            logger.exception("[POK] Error rendering issued certificate: %s", str(e))
            return self._render_error_page(context, str(e), course_id, user_id)

    def _render_emitted_certificate(self, context, certificate, user_id, client):
        """
        Renders the final issued certificate with full image and metadata.
        Uses decrypted data from the POK API.
        """

        try:
            response = client.get_credential_details(certificate.pok_certificate_id, decrypted=True)
            if not response.get("success"):
                raise Exception(f"Failed to fetch credential details: {response.get('error')}")

            image_content = response["content"].get("location")
            if not image_content:
                raise Exception("Missing certificate image URL")
            
            authoring_url = settings.LEARNING_MICROFRONTEND_URL.rstrip('/').replace('/learning', '/authoring').replace(':2000', ':2001')
            
            mfe_config = getattr(settings, "MFE_CONFIG", None)
            lms_base_url = mfe_config.get("LMS_BASE_URL")


            social_links = build_social_links(
                view_url=certificate.view_url,
                course_title=certificate.title,
                platform_name=getattr(settings, 'PLATFORM_NAME', ''),
                twitter_account=getattr(settings, 'PLATFORM_TWITTER_ACCOUNT', None),
                image_content=image_content
            )

            html = render_to_string("openedx_pok/certificate_pok.html", {
                "document_title": context.get("document_title", "Certificate"),
                "logo_src": context.get("logo_src", ""),
                "accomplishment_copy_name": context.get("accomplishment_copy_name", "Student"),
                "image_content": image_content,
                "certificate_url": certificate.view_url,
                "authoring_microfrontend_url": f"{authoring_url}/course/{certificate.course_id}/certificates",
                "social_links": social_links,
                "user_id": user_id,
                "course_id": certificate.course_id,
                "lms_base_url": lms_base_url,
            })

            raise CertificateRenderStarted.RenderCustomResponse(
                "Rendering emitted certificate",
                HttpResponse(html, content_type="text/html; charset=utf-8", status=200)
            )

        except CertificateRenderStarted.RenderCustomResponse as r:
            raise r
        except Exception as e:
            logger.error("[POK] Failed to render emitted certificate: %s", str(e))
            return self._render_error_page(context, str(e), certificate.course_id, certificate.user_id)

    def _render_processing_certificate(self, context, certificate, client):
        """
        Renders a 'processing' status page for certificates that haven't been emitted yet.
        Also updates the certificate state if the POK API returns new status.
        """
        try:
            response = client.get_credential_details(certificate.pok_certificate_id)
            state = response.get("content", {}).get("state", "processing")
            certificate.state = state
            certificate.save()

            html = render_to_string("openedx_pok/certificate_processing.html", {
                "document_title": context.get("document_title", "Certificate in process"),
                "course_id": certificate.course_id,
                "user_id": certificate.user_id
            })

            raise CertificateRenderStarted.RenderCustomResponse(
                "Rendering processing certificate",
                HttpResponse(html, content_type="text/html; charset=utf-8", status=200)
            )

        except CertificateRenderStarted.RenderCustomResponse as r:
            raise r
        except Exception as e:
            logger.exception("[POK] Failed to render processing certificate: %s", str(e))
            return self._render_error_page(context, str(e), certificate.course_id, certificate.user_id)

    def _render_error_page(self, context, error_message, course_id, user_id):
        """
        Renders a generic error page with a user-friendly message when rendering fails.
        """
        html = render_to_string("openedx_pok/certificate_error.html", {
            "document_title": context.get("document_title", "Error"),
            "error_message": error_message,
            "course_id": course_id,
            "user_id": user_id
        })

        raise CertificateRenderStarted.RenderCustomResponse(
            f"Rendering error page: {error_message}",
            HttpResponse(html, content_type="text/html; charset=utf-8", status=500)
        )
