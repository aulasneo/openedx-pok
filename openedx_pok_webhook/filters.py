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

from .models import Certificate
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

        # Lookup stored POK certificate
        pok_client = PokApiClient()

        try:
            certificate = Certificate.objects.get(
                user_id=user_id,
                course_id=course_id,
                state="emitted"
            )
        except Certificate.DoesNotExist:
            certificate = Certificate.objects.get(
                user_id=user_id,
                course_id=course_id
            )
            pok_response = pok_client.get_credential_details(certificate.certificate_id)
            content = pok_response.get("content")
            certificate.state = content.get('state')
            certificate.save()

        if certificate.view_url:
            logger.info(f"Redirecting to POK certificate: {certificate.view_url}")
            response = pok_client.get_credential_details(certificate.certificate_id,
                                                           decrypted=True)

            if response.get("success"):
                image_response = response.get("content")
                image_content = image_response.get("location")
            else:
                image_content = certificate.view_url

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{context.get('document_title', 'Certificate')}</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: sans-serif;
                    }}
                    section {{
                        margin: 0;
                        padding: 20px;
                        text-align: center;
                    }}
                    .banner {{
                        background-color: #000;
                        color: #fff;
                        padding: 10px;
                    }}
                    img {{
                        max-width: 100%;
                        display: block;
                        margin: 0 auto;
                    }}
                    .certificate-section {{
                        padding: 20px 0;
                    }}
                    .info-section {{
                        display: flex;
                        justify-content: space-between;
                        max-width: 800px;
                        margin: 0 auto;
                        text-align: left;
                    }}
                    .info-column {{
                        width: 48%;
                    }}
                    footer {{
                        border-top: 1px solid #ddd;
                        padding: 10px;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <!-- Logo -->
                <section>
                    <img src="{context.get('logo_src', '')}" alt="Logo" style="height:30px;">
                </section>

                <!-- Banner de felicitación -->
                <section class="banner">
                    <p>{context.get('accomplishment_copy_name', 'Student')}, you earned a certificate!</p>
                    <p>Congratulations! This page summarizes what you accomplished.</p>
                    <button>Print Certificate</button>
                </section>

                <!-- Título -->
                <section>
                    <h2>My Open edX acknowledges the following student accomplishment</h2>
                </section>

                <!-- Certificado -->
                <section class="certificate-section">
                    <img src="{image_content}" alt="Certificate">
                </section>

                <!-- Información adicional -->
                <section>
                    <h3>More about {context.get('accomplishment_copy_name', 'Student')}'s accomplishment</h3>

                    <div class="info-section">
                        <div class="info-column">
                            <h4>About My Open edX</h4>
                            <p>My Open edX offers interactive online classes and MOOCs.</p>
                        </div>

                        <div class="info-column">
                            <h4>About My Open edX Accomplishments</h4>
                            <p>My Open edX acknowledges achievements through certificates.</p>
                        </div>
                    </div>
                </section>

                <!-- Footer -->
                <footer>
                    <p>© 2025 My Open edX. All rights reserved.</p>
                    <p>
                        <a href="/tos">Terms of Service</a> |
                        <a href="/privacy">Privacy Policy</a>
                    </p>
                </footer>
            </body>
            </html>
            """

            http_response = HttpResponse(
                content=html_content,
                content_type="text/html; charset=utf-8",
                status=200
            )

            raise CertificateRenderStarted.RenderCustomResponse(
                message="Embedding POK certificate",
                response=http_response
            )
        else:
            logger.warning(f"Found POK certificate record for {user_id} in {course_id} but URL is missing")


        # If no POK certificate found or any error, continue with normal rendering
        return {"context": context, "custom_template": custom_template}
