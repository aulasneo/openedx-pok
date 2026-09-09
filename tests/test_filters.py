"""Tests for POK certificate filters."""
# pylint: disable=protected-access

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from opaque_keys.edx.keys import CourseKey
from openedx_filters.learning.filters import CertificateCreationRequested

from openedx_pok import filters as filters_module
from openedx_pok.filters import CertificateRenderFilter, CertificateRenderStarted, update_certificate_from_response
from openedx_pok.models import PokCertificate
from openedx_pok.settings.common import plugin_settings


@pytest.fixture
def configured_filters(settings):
    """Register POK steps in the installed openedx-filters pipeline."""
    settings.OPEN_EDX_FILTERS_CONFIG = {}
    plugin_settings(settings)
    settings.COURSE_AUTHORING_MICROFRONTEND_URL = "https://studio.example.org/authoring/"
    settings.LMS_ROOT_URL = "https://lms.example.org/"
    settings.MFE_CONFIG = {}


@pytest.mark.django_db
@pytest.mark.usefixtures("configured_filters")
@pytest.mark.parametrize("grade", [SimpleNamespace(percent=0.875), 0.875])
def test_creation_pipeline_preserves_context_and_sends_grade(
    monkeypatch, test_user, mock_course_overview, grade,
):
    """Accept platform grade objects and preserve all six creation hook arguments."""
    course_key = CourseKey.from_string(str(mock_course_overview.pk))
    course = SimpleNamespace(
        certificates={"certificates": [{"signatories": [{"name": "Signer"}]}]},
        display_name="Test Course",
        display_organization="Test Organization",
    )
    client = Mock(emission_type="pok")
    client.request_certificate.return_value = {
        "success": True, "content": {"id": "credential-123", "state": "pending"},
    }
    monkeypatch.setattr(filters_module, "is_pok_enabled", lambda _key: True)
    monkeypatch.setattr(filters_module, "get_course_by_id", lambda _key: course)
    monkeypatch.setattr(filters_module, "PokApiClient", lambda _key: client)

    result = CertificateCreationRequested.run_filter(
        user=test_user, course_key=course_key, mode="honor", status="downloadable",
        grade=grade, generation_mode="self",
    )

    assert result == (test_user, course_key, "honor", "downloadable", grade, "self")
    assert client.request_certificate.call_args.kwargs["grade"] == "88"
    assert PokCertificate.objects.get(user=test_user, course_id=str(course_key)).state == "processing"


@pytest.mark.django_db
@pytest.mark.usefixtures("configured_filters")
def test_creation_pipeline_propagates_api_failure(monkeypatch, test_user):
    """POK errors must reach Open edX as PreventCertificateCreation."""
    monkeypatch.setattr(filters_module, "is_pok_enabled", lambda _key: True)
    monkeypatch.setattr(filters_module, "_get_custom_params", lambda _key: {})
    monkeypatch.setattr(filters_module, "_get_org_name", lambda _key: "Test Organization")
    monkeypatch.setattr(filters_module, "get_course_by_id", lambda _key: SimpleNamespace(
        certificates={"certificates": [{}]}, display_name="Test Course",
    ))
    client = Mock()
    client.request_certificate.return_value = {"success": False, "error": "unavailable"}
    monkeypatch.setattr(filters_module, "PokApiClient", lambda _key: client)

    with pytest.raises(CertificateCreationRequested.PreventCertificateCreation, match="unavailable"):
        CertificateCreationRequested.run_filter(
            user=test_user, course_key=CourseKey.from_string("course-v1:test+Test+2023"),
            mode="honor", status=None, grade=None, generation_mode="self",
        )


@pytest.mark.django_db
@pytest.mark.usefixtures("configured_filters")
@pytest.mark.parametrize("issued", [False, True])
def test_render_pipeline_uses_platform_urls(
    monkeypatch, test_user, issued,
):
    """Preview and issued pages use explicit URLs and the real response exception."""
    course_id = "course-v1:test+Test+2023"
    if issued:
        PokCertificate.objects.create(
            user=test_user, course_id=course_id, pok_certificate_id="credential-123",
            state="emitted", title="Test Course", view_url="https://pok.example/credential-123",
        )
    client = Mock()
    client.get_template_preview.return_value = {"success": True, "preview_url": "https://pok.example/preview"}
    client.get_credential_details.return_value = {"success": True, "content": {"location": "https://pok.example/image"}}
    monkeypatch.setattr(filters_module, "is_pok_enabled", lambda _key: True)
    monkeypatch.setattr(filters_module, "_get_custom_params", lambda _key: {})
    monkeypatch.setattr(filters_module, "_get_org_name", lambda _key: "Test Organization")
    monkeypatch.setattr(filters_module, "PokApiClient", lambda _key: client)
    renderer = Mock(return_value="<html>Certificate</html>")
    monkeypatch.setattr(filters_module, "render_to_string", renderer)

    with pytest.raises(CertificateRenderStarted.RenderCustomResponse) as exc:
        CertificateRenderStarted.run_filter(context={
            "course_id": course_id,
            "accomplishment_user_id": test_user.id,
            "accomplishment_copy_course_name": "Test Course",
            "user_certificate": object(),  # Additional context supplied in Verawood.
        }, custom_template=None)

    assert exc.value.response.status_code == 200
    assert exc.value.response.content == b"<html>Certificate</html>"
    render_context = renderer.call_args.args[1]
    assert render_context["authoring_microfrontend_url"] == (
        f"https://studio.example.org/authoring/course/{course_id}/certificates"
    )
    if issued:
        assert render_context["lms_base_url"] == "https://lms.example.org"


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
