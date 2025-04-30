"""
POK certificate filter implementations.
"""
import json
import logging

from django.http import HttpResponse
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import (
    CertificateRenderStarted,
)

from django.template.loader import render_to_string

from .models import PokCertificate
from .client import PokApiClient

logger = logging.getLogger(__name__)



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

        pok_client = PokApiClient(course_id)
        
        if not pok_client.api_key:
            logger.warning("POK API key is not set. Skipping POK certificate rendering.")
            return {"context": context, "custom_template": custom_template}

        try:
            # Intenta obtener el certificado emitido
            certificate = PokCertificate.objects.get(
                user_id=user_id,
                course_id=course_id,
                state="emitted"
            )
            state = "emitted"
            logger.info("Found emitted POK certificate.")

        except PokCertificate.DoesNotExist:
            try:
                # Si no hay emitido, intenta obtener uno en procesamiento
                certificate = PokCertificate.objects.get(
                    user_id=user_id,
                    course_id=course_id,
                    state="processing"
                )
                logger.info("Found processing POK certificate.")

                # Verifica si ya fue emitido consultando la API
                pok_response = pok_client.get_credential_details(certificate.pok_certificate_id)
                content = pok_response.get("content", {})
                state = content.get("state", "processing")
                certificate.state = state
                certificate.save()
                logger.info(f"Updated processing certificate state to: {state}")

            except PokCertificate.DoesNotExist:
                # Si no hay ninguno, el estado es preview
                certificate = None
                state = "preview"
                logger.info("No existing POK certificate found. Using preview state.")


        logger.info(f"Certificate state from POK API: {state}")
        #logger.error(f"CONTEXT: {context}")
             


        if state == "emitted":
            try:
                response = pok_client.get_credential_details(certificate.pok_certificate_id, decrypted=True)

                if not response.get("success"):
                    raise Exception(f"POK API returned failure: {response.get('error')}")

                content = response.get("content", {})
                image_content = content.get("location")

                if not image_content:
                    raise Exception("POK response missing 'location' for decrypted image.")

                html_content = render_to_string("openedx_pok_webhook/certificate_pok.html", {
                    'document_title': context.get('document_title', 'Certificate'),
                    'logo_src': context.get('logo_src', ''),
                    'accomplishment_copy_name': context.get('accomplishment_copy_name', 'Student'),
                    'image_content': image_content,
                    'certificate_url': certificate.view_url,
                })

            except Exception as e:
                logger.error(f"Failed to render emitted certificate from POK: {str(e)}")

                html_content = render_to_string("openedx_pok_webhook/certificate_error.html", {
                    'document_title': context.get('document_title', 'Error'),
                    'error_message': "We couldn't render your certificate at this time. Please try again later.",
                    'course_id': course_id,
                    'user_id': user_id,
                })

                http_response = HttpResponse(
                    content=html_content,
                    content_type="text/html; charset=utf-8",
                    status=500
                )

                raise CertificateRenderStarted.RenderCustomResponse(
                    message="Error rendering POK certificate",
                    response=http_response
                )


        elif state == "processing":
            html_content = render_to_string("openedx_pok_webhook/certificate_processing.html", {
                'document_title': context.get('document_title', 'Certificate in process'),
                'course_id': course_id,
                'user_id': user_id,
            })
            
        elif state == "preview":
            logger.info("POK certificate in 'preview' state detected. Attempting to generate preview URL.")

            from django.contrib.auth import get_user_model
            User = get_user_model()
            user_id = context.get("accomplishment_user_id")

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User with id={user_id} not found in database.")
                return {"context": context, "custom_template": custom_template}

            logger.info(f"Building preview payload for user_id={user.id}, course_id={course_id}")

            preview_response = pok_client.get_template_preview(
                user=user,
                course_key=course_id,
                grade=context.get("certificate_data", {}).get("description", "N/A"),  # o usa otro campo si representa mejor la nota
                mode=context.get("course_mode", "honor"),
                platform=context.get("platform_name", "Open edX"),
                signatory_name=context.get("certificate_data", {}).get("signatories", [{}])[0].get("name", "Instructor"),
                organization=context.get("organization_long_name", "Organization"),
                course_title=context.get("certificate_data", {}).get("course_title", "Course")
            )

            if preview_response.get("success"):
                logger.info("POK preview request succeeded.")

                # Intentar extraer la URL de previsualización desde diferentes campos posibles
                preview_url = (
                    preview_response.get("preview_url") or
                    preview_response.get("preview", {}).get("previewUrl") or
                    preview_response.get("preview", {}).get("preview_url") or
                    preview_response.get("preview", {}).get("url") or
                    preview_response.get("preview", {}).get("location")
                )

                if not preview_url:
                    logger.error(f"POK preview URL not found in response: {json.dumps(preview_response, indent=2)}")
                    return {"context": context, "custom_template": custom_template}

                logger.info(f"Redirecting to POK certificate preview URL: {preview_url}")
                from django.http import HttpResponseRedirect
                raise CertificateRenderStarted.RenderCustomResponse(
                    message="Redirecting to certificate preview",
                    response=HttpResponseRedirect(preview_url)
                )

            else:
                logger.error(f"POK preview request failed: {preview_response.get('error')}")
                return {"context": context, "custom_template": custom_template}

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
