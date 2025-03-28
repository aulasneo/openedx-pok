import hmac
import hashlib
import base64
import time

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.encoding import force_bytes

# Claves compartidas (ajusta con los valores reales de PoK)
WEBHOOK_SIGNING_KEY = b'd6bb7dc8-5731-439e-83ae-4d9c77d0d55e'
WEBHOOK_BASIC_AUTH_SECRET = '14283a0d-c9c1-4969-a75c-e59214057819'

TOLERANCE_MS = 5 * 60 * 1000  # 5 minutos

class PoKWebhookView(APIView):
    authentication_classes = []  # si no usas autenticación de DRF aquí
    permission_classes = []

    def post(self, request):
        raw_body = request.body.decode('utf-8')
        timestamp = request.headers.get('X-Pok-Request-Timestamp')
        signature = request.headers.get('X-Pok-Signature')
        auth_header = request.headers.get('Authorization')

        # Validar header Authorization
        expected_auth = 'Basic ' + base64.b64encode(f'pok:{WEBHOOK_BASIC_AUTH_SECRET}'.encode()).decode()
        if auth_header != expected_auth:
            return Response({'detail': 'Invalid Authorization header'}, status=status.HTTP_401_UNAUTHORIZED)

        # Validar timestamp
        if not timestamp or not self._is_within_timeframe(timestamp):
            return Response({'detail': 'Request timestamp outside tolerance'}, status=status.HTTP_400_BAD_REQUEST)

        # Validar firma
        if not signature or not self._verify_signature(timestamp, raw_body, signature):
            return Response({'detail': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        # Si todo está bien, procesa el webhook
        print("✅ Webhook recibido y validado:")
        print(request.data)

        return Response(status=status.HTTP_200_OK)

    def _verify_signature(self, timestamp: str, body: str, sent_signature: str) -> bool:
        message = f'{timestamp}.{body}'
        computed_hmac = hmac.new(WEBHOOK_SIGNING_KEY, message.encode('utf-8'), hashlib.sha512).hexdigest()
        return hmac.compare_digest(computed_hmac, sent_signature)

    def _is_within_timeframe(self, timestamp: str) -> bool:
        try:
            sent_time = int(timestamp)
            current_time = int(time.time() * 1000)
            return (sent_time + TOLERANCE_MS) >= current_time
        except ValueError:
            return False
