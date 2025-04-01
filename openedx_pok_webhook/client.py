"""
POK API client for certificate issuance.
"""
import json
import logging
from datetime import datetime
from urllib.parse import urljoin

import requests
from django.conf import settings

from openedx_pok_webhook.utils import split_name

logger = logging.getLogger(__name__)


class PokApiClient:
    """Client for POK API."""

    def __init__(self):
        """Initialize the POK API client."""
        self.base_url = getattr(settings, 'POK_API_BASE_URL', 'https://api.pok.tech/')
        self.api_key = getattr(settings, 'POK_API_KEY', 'd4769662-7173-4162-8bf6-ae175ed02076')
        self.timeout = getattr(settings, 'POK_API_TIMEOUT', 10)
        self.template = getattr(settings, 'POK_TEMPLATE', "949ae2a7-7434-492d-82c3-980caf07e1e7")

    def _get_headers(self):
        """Get the common headers for API requests."""
        return {
            'Authorization': f'ApiKey {self.api_key}',
            'Accept': 'application/json',
            # 'Content-Type': 'application/json',
        }

    def get_organization_details(self):
        """
        Retrieve details of the organization which owns the provided API key.

        Returns:
            dict: Organization details including wallet, name, available credits, etc.
        """
        endpoint = urljoin(self.base_url, 'organization/me')

        try:
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching organization details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_templates(self):
        """
        Retrieve available certificate templates.

        Returns:
            dict: Available templates for the organization
        """
        endpoint = urljoin(self.base_url, 'templates')

        try:
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching templates: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def request_certificate(self, user, course_key, grade, mode):
        """
        Request a certificate from POK.

        Args:
            user: User object
            course_key: Course key string
            grade: Grade value as string or number
            mode: Certificate mode string

        Returns:
            dict: POK API response
        """
        endpoint = urljoin(self.base_url, 'credential/')
        email = user.pii.email if hasattr(user, 'pii') else user.email

        if hasattr(user, 'pii'):
            first_name, last_name = split_name(user.pii.name)
        else:
             first_name = user.first_name
             last_name = user.last_name

        payload = {
            "credential": {
                "tags": [
                    f"StudentId:{user.id}",
                    f"CourseId:{course_key}",
                    f"Mode:{mode}"
                ],
                "skipAcceptance": True,
                "emissionType": "pok",
                "dateFormat": "dd/MM/yyyy",
                "emissionDate": datetime.now().isoformat(),
                "title": f"Certificate for {course_key}",
                "emitter": "Open edX"
            },
            "receiver": {
                "languageTag": "es-ES",
                "identification": str(user.id),
                "email": email,
                "lastName": last_name,
                "firstName": first_name
            },
            "customization": {
                "template": {
                    "customParameters": {"grade": grade},
                    "id": self.template,
                }
            }
        }

        try:
            logger.info(f"Sending certificate request to POK for user {user.id} in course {course_key}")
            logger.debug(f"POK API request payload: {json.dumps(payload)}")

            header = self._get_headers()
            response = requests.post(
                endpoint,
                json=payload,
                headers=header,
            )
            response.raise_for_status()
            return_data = response.json()

            if response.status_code != 200:
                raise requests.exceptions.RequestException("Error creating certificate with POK")

            credential_id = return_data.get("id")

            return self.get_credential_details(credential_id)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting certificate from POK: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.exception(f"Unexpected error in POK API client: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_credential_details(self, certificate_id, decrypted=None):
        """
        Get details for a specific credential.

        Args:
            certificate_id: ID of the credential to retrieve
            decrypted: Optional decrypted data

        Returns:
            dict: Credential details
        """
        endpoint = urljoin(self.base_url, f'credential/{certificate_id}/')

        if decrypted:
            endpoint = urljoin(endpoint, "decrypted-image/")

        try:
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return {"success": True, "content": response.json()}

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching credential details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def resend_approval_request(self, credential_id):
        """
        Resend an approval request for a certificate.

        Args:
            credential_id: ID of the credential

        Returns:
            dict: Response from the API
        """
        endpoint = urljoin(self.base_url, f'credentials/{credential_id}/resend-approval')

        try:
            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error resending approval request: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
