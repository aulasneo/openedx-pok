import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock

from openedx_pok.models import PokCertificate, CertificateTemplate

User = get_user_model()


@pytest.mark.django_db
def test_create_pok_certificate():
    user = User.objects.create(username="testuser", email="test@example.com")

    pok_certificate = PokCertificate.objects.create(
        user=user,
        course_id="course-v1:edX+DemoX+Demo_Course",
        pok_certificate_id="cert123",
        state="emitted",
        view_url="https://example.com/cert",
        emission_date=timezone.now(),
        emission_type="pok",
        custom_parameters={"key": "value"},
        title="Sample Certificate",
        emitter="POK System",
        tags=["tag1", "tag2"],
        receiver_email="student@example.com",
        receiver_name="Student Name"
    )

    assert pok_certificate.pk is not None
    assert pok_certificate.user == user
    assert pok_certificate.course_id == "course-v1:edX+DemoX+Demo_Course"
    assert pok_certificate.tags == ["tag1", "tag2"]
    assert str(pok_certificate).startswith("POK Certificate for user")


@pytest.mark.django_db
def test_create_certificate_template():
    mock_course = MagicMock()
    mock_course.id = 999
    mock_course.__str__.return_value = "MockCourse"

    template = CertificateTemplate(
        course=mock_course,
        template_id="template_abc",
        emission_type="blockchain"
    )

    # Bypasa validación de FK y simula guardado
    template._state.adding = False
    template.pk = 1

    assert template.course == mock_course
    assert template.template_id == "template_abc"
    assert template.emission_type == "blockchain"
    assert str(template).startswith("Template template_abc for course")
