import logging
import requests
from datetime import datetime

from openedx_filters.learning.filters import (
    CertificateRenderStarted
)
from openedx_filters.filters import PipelineStep
from openedx_pok.models import CertificatePok

log = logging.getLogger(__name__)

class CertificateCreationRequestedWebFilter(PipelineStep):
    def run_filter(self, context, pipeline):
        user = context.get("user")
        course = context.get("course")

        if not user or not course:
            log.warning("Contexto incompleto para creación de certificado.")
            return context

        payload = {
            "user": {
                "id": str(user.id),
                "email": user.email,
            },
            "course": {
                "id": str(course.id),
                "name": course.display_name,
            }
        }

        try:
            response = requests.post(
                "https://api.pok.tech/certificates",
                json=payload,
                headers={
                    "Authorization": "Bearer 4ff6a66b-2346-4d39-b4e9-b4818196ba8a",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            CertificatePok.objects.update_or_create(
                certificate_id=data["id"],
                defaults={
                    "user_id": str(user.id),
                    "course_id": str(course.id),
                    "issued_at": datetime.fromisoformat(data["issued_at"]),
                    "pok_url": data["url"],
                    "raw_response": data
                }
            )

        except Exception as e:
            log.exception("Error al crear certificado en PoK: %s", e)

        return context


class CertificateRenderStartedWebFilter(PipelineStep):
    def run_filter(self, context, pipeline):
        user = context.get("user")
        course = context.get("course")

        if not user or not course:
            log.warning("Contexto incompleto para renderizado de certificado.")
            return context

        try:
            cert = CertificatePok.objects.get(user_id=str(user.id), course_id=str(course.id))

            if cert.pok_url:
                log.info(f"Redirigiendo certificado a PoK: {cert.pok_url}")
                raise CertificateRenderStarted.RenderCustomResponse(cert.pok_url)

        except CertificatePok.DoesNotExist:
            log.warning("No se encontró un certificado emitido por PoK para este usuario/curso.")
        except Exception as e:
            log.exception("Error al intentar redirigir a certificado PoK: %s", e)

        return context
