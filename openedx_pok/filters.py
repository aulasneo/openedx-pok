import logging
import requests
from datetime import datetime

from openedx_filters.learning.filters import CertificateCreationRequested
from openedx_filters.pipeline import PipelineStep
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

        # Enviar solicitud a PoK
        try:
            response = requests.post(
                "https://api.pok.tech/certificates",  # endpoint real
                json=payload,
                headers={
                    "Authorization": f"Bearer b3567f4e-5716-46b1-8ad9-1f8713061b82",
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
