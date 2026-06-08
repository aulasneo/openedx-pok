"""Tests for the POK API client."""
# pylint: disable=protected-access

from types import SimpleNamespace

from openedx_pok import client as client_module
from openedx_pok.client import PokApiClient


class FakeResponse:
    """Minimal requests response for client tests."""

    status_code = 202
    text = '{"id":"credential-123","state":"pending"}'

    def json(self):
        """Return a pending credential creation response."""
        return {"id": "credential-123", "state": "pending"}


def test_request_certificate_accepts_pending_response(monkeypatch, settings):
    """A 202 pending response from POK should not fail certificate creation."""
    settings.POK_DATE_FORMAT = "dd/MM/yyyy"

    api_client = PokApiClient.__new__(PokApiClient)
    api_client.base_url = "https://pok.example/api/"
    api_client.timeout = 10
    api_client.emission_type = "pok"
    api_client.page = ""
    api_client.template = "template-123"
    api_client._get_active_custom_parameters = lambda: {}
    api_client._get_headers = lambda is_preview=False: {}

    def fail_if_called(_credential_id, decrypted=None):
        raise AssertionError("pending credentials should not fetch details immediately")

    api_client.get_credential_details = fail_if_called

    monkeypatch.setattr(client_module.requests, "post", lambda *args, **kwargs: FakeResponse())
    monkeypatch.setattr(client_module, "resolve_language_tag", lambda user: "es-419")

    user = SimpleNamespace(
        id=11,
        email="andres@example.com",
        username="andres",
    )

    response = api_client.request_certificate(
        user=user,
        course_key="course-v1:CPIA+IAAGRO+2026",
        mode="honor",
        organization="CPIA",
        course_title="I.A. Aplicada al Agro",
    )

    assert response == {
        "success": True,
        "content": {
            "id": "credential-123",
            "state": "processing",
        },
    }
