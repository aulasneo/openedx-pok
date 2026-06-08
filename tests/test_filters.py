"""Tests for POK certificate filters."""
# pylint: disable=protected-access

from types import SimpleNamespace

import pytest

from openedx_pok import filters as filters_module
from openedx_pok.filters import CertificateRenderFilter, CertificateRenderStarted, update_certificate_from_response
from openedx_pok.models import PokCertificate


@pytest.mark.django_db
def test_update_certificate_from_pending_response_preserves_required_metadata(test_user):
    """A minimal pending POK response should not null required local fields."""
    certificate = PokCertificate(
        user=test_user,
        course_id="course-v1:CPIA+IAAGRO+2026",
    )
    client = SimpleNamespace(emission_type="pok")

    update_certificate_from_response(
        certificate,
        {"id": "credential-123", "state": "pending"},
        client=client,
        course_title="I.A. Aplicada al Agro",
        organization="CPIA",
        user=test_user,
    )

    assert certificate.pok_certificate_id == "credential-123"
    assert certificate.state == "processing"
    assert certificate.emission_type == "pok"
    assert certificate.title == "I.A. Aplicada al Agro"
    assert certificate.emitter == "CPIA"
    assert certificate.receiver_email == "test@example.com"
    assert certificate.receiver_name == "testuser"


@pytest.mark.django_db
def test_processing_render_backfills_credential_metadata(monkeypatch, test_user):
    """Polling a processing certificate should backfill full POK metadata."""
    certificate = PokCertificate.objects.create(
        user=test_user,
        course_id="course-v1:CPIA+IAAGRO+2026",
        pok_certificate_id="credential-123",
        state="processing",
        emission_type="pok",
        title="Fallback title",
        emitter="Fallback emitter",
        receiver_email="fallback@example.com",
        receiver_name="Fallback User",
    )
    client = SimpleNamespace(
        emission_type="pok",
        get_credential_details=lambda _certificate_id: {
            "success": True,
            "content": {
                "id": "credential-123",
                "state": "emitted",
                "viewUrl": "https://pok.example/credential-123",
                "credential": {
                    "emissionType": "blockchain",
                    "title": "Backfilled title",
                    "emitter": "CPIA",
                    "tags": ["StudentId:11"],
                },
                "receiver": {
                    "email": "backfilled@example.com",
                },
            },
        },
    )
    monkeypatch.setattr(filters_module, "render_to_string", lambda *_args, **_kwargs: "<html></html>")
    render_filter = CertificateRenderFilter.__new__(CertificateRenderFilter)

    with pytest.raises(CertificateRenderStarted.RenderCustomResponse):
        render_filter._render_processing_certificate({}, certificate, client)

    certificate.refresh_from_db()
    assert certificate.state == "emitted"
    assert certificate.view_url == "https://pok.example/credential-123"
    assert certificate.emission_type == "blockchain"
    assert certificate.title == "Backfilled title"
    assert certificate.emitter == "CPIA"
    assert certificate.tags == ["StudentId:11"]
    assert certificate.receiver_email == "backfilled@example.com"
