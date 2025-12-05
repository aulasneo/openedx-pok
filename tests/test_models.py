#!/usr/bin/env python
"""
Tests for the `openedx-pok-webhook` models module.
"""

import pytest
from django.contrib.auth import get_user_model

from openedx_pok.models import CertificateTemplate, PokCertificate

User = get_user_model()


@pytest.mark.django_db
def test_pok_certificate_creation(test_user):
    """
    Test creating a PokCertificate instance.
    """
    certificate = PokCertificate.objects.create(
        user=test_user,
        course_id="course-v1:test+Test+2023",
        pok_certificate_id="cert-123",
        state="emitted",
        view_url="https://example.com/cert/123",
        emission_type="pok",
        title="Test Certificate",
        emitter="Test Emitter",
        receiver_email="test@example.com",
        receiver_name="Test User"
    )

    assert certificate.user == test_user
    assert certificate.course_id == "course-v1:test+Test+2023"
    assert certificate.pok_certificate_id == "cert-123"
    assert certificate.state == "emitted"
    assert certificate.emission_type == "pok"


@pytest.mark.django_db
def test_certificate_template_creation(mock_course_overview):
    """
    Test creating a CertificateTemplate instance.
    """
    template = CertificateTemplate.objects.create(
        course=mock_course_overview,
        template_id="template-123",
        emission_type="pok",
        page_id="page-456"
    )

    assert template.course == mock_course_overview
    assert template.template_id == "template-123"
    assert template.emission_type == "pok"
    assert template.page_id == "page-456"


@pytest.mark.django_db
def test_pok_certificate_str_representation(test_user):
    """
    Test string representation of PokCertificate.
    """
    certificate = PokCertificate.objects.create(
        user=test_user,
        course_id="course-v1:test+Test+2023"
    )

    expected = 'POK Certificate for user 1 in course course-v1:test+Test+2023'
    assert str(certificate) == expected


@pytest.mark.django_db
def test_certificate_template_str_representation(mock_course_overview):
    """
    Test string representation of CertificateTemplate.
    """
    template = CertificateTemplate.objects.create(
        course=mock_course_overview,
        template_id="template-123"
    )

    expected = 'Template template-123 for course 1'
    assert str(template) == expected


@pytest.mark.django_db
def test_pok_certificate_unique_constraint(test_user):
    """
    Test that user and course_id combination is unique.
    """
    PokCertificate.objects.create(
        user=test_user,
        course_id="course-v1:test+Test+2023"
    )

    # Attempting to create duplicate should raise IntegrityError
    with pytest.raises(Exception):  # IntegrityError
        PokCertificate.objects.create(
            user=test_user,
            course_id="course-v1:test+Test+2023"
        )
