# views POK

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, Http404
from .models import PokCertificate
from .client import PokApiClient
from opaque_keys.edx.keys import CourseKey
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

class CertificateImageDownloadView(APIView):
    #permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Descarga la imagen del certificado como JPG usando query params.
        El image_content se obtiene del campo 'location' en 'content' de la respuesta del cliente POK,
        igual que en el filter CertificateRenderFilter.
        """
        course_id = request.query_params.get("course_id")  # Usar como string
        user_id = request.query_params.get("user_id")

        # Normalizar course_id: reemplazar espacios por '+'
        if course_id:
            course_id = course_id.replace(" ", "+")

        logger.info(f"Recibido course_id={course_id}, user_id={user_id}")

        if not course_id or not user_id:
            logger.info("Faltan parámetros course_id o user_id.")
            return Response({"detail": "Faltan parámetros course_id o user_id."}, status=400)

        # Buscar el certificado usando el string directamente
        certificate = PokCertificate.objects.filter(user_id=user_id, course_id=course_id).first()
        logger.info(f"Certificado encontrado: {certificate.pok_certificate_id if certificate else None}")

        if not certificate or not certificate.pok_certificate_id:
            logger.info("Certificado no encontrado o pok_certificate_id vacío.")
            raise Http404("Certificado no encontrado.")

        # Obtener la URL de la imagen usando el cliente POK
        client = PokApiClient(course_id)
        response = client.get_credential_details(certificate.pok_certificate_id, decrypted=True)
        logger.info(f"Respuesta de get_credential_details: {response}")

        content = response.get("content", {})
        image_content = content.get("location")
        logger.info(f"image_content (URL de la imagen): {image_content}")

        if not image_content or not isinstance(image_content, str):
            logger.info("Imagen del certificado no disponible.")
            raise Http404("Imagen del certificado no disponible.")

        # Descargar la imagen
        img_response = requests.get(image_content)
        logger.info(f"Status de descarga de imagen: {img_response.status_code}")

        if img_response.status_code != 200:
            logger.info("No se pudo descargar la imagen.")
            raise Http404("No se pudo descargar la imagen.")

        # Preparar la respuesta para descargar como JPG
        filename = f"certificado_{user_id}_{course_id}.jpg"
        logger.info(f"Nombre de archivo para descarga: {filename}")
        return HttpResponse(
            img_response.content,
            content_type="image/jpeg",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )