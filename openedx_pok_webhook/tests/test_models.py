from django.test import TestCase
from django.contrib.auth import get_user_model
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx_pok_webhook.models import CertificatePokApi, CourseTemplate
from datetime import datetime

User = get_user_model()

class CertificatePokApiTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", email="testuser@example.com")
        self.certificate = CertificatePokApi.objects.create(
            user=self.user,
            course_id="course-v1:edX+DemoX+Demo_Course",
            pok_certificate_id="12345",
            state="emitted",
            view_url="http://example.com/certificate/12345",
            emission_date=datetime.now(),
            emission_type="pok",
            custom_parameters={"key": "value"},
            title="Certificate Title",
            emitter="Certificate Emitter",
            tags=["tag1", "tag2"],
            receiver_email="receiver@example.com",
            receiver_name="Receiver Name"
        )

    def test_certificate_creation(self):
        self.assertEqual(self.certificate.user, self.user)
        self.assertEqual(self.certificate.course_id, "course-v1:edX+DemoX+Demo_Course")
        self.assertEqual(self.certificate.pok_certificate_id, "12345")
        self.assertEqual(self.certificate.state, "emitted")
        self.assertEqual(self.certificate.view_url, "http://example.com/certificate/12345")
        self.assertEqual(self.certificate.emission_type, "pok")
        self.assertEqual(self.certificate.custom_parameters, {"key": "value"})
        self.assertEqual(self.certificate.title, "Certificate Title")
        self.assertEqual(self.certificate.emitter, "Certificate Emitter")
        self.assertEqual(self.certificate.tags, ["tag1", "tag2"])
        self.assertEqual(self.certificate.receiver_email, "receiver@example.com")
        self.assertEqual(self.certificate.receiver_name, "Receiver Name")

    def test_certificate_str(self):
        self.assertEqual(
            str(self.certificate),
            f'POK Certificate for user {self.user.id} in course course-v1:edX+DemoX+Demo_Course'
        )

class CourseTemplateTestCase(TestCase):
    def setUp(self):
        self.course = CourseOverview.objects.create(
            id="course-v1:edX+DemoX+Demo_Course",
            display_name="Demo Course"
        )
        self.template = CourseTemplate.objects.create(
            course=self.course,
            template_id="template123",
            emission_type="pok"
        )

    def test_template_creation(self):
        self.assertEqual(self.template.course, self.course)
        self.assertEqual(self.template.template_id, "template123")
        self.assertEqual(self.template.emission_type, "pok")

    def test_template_str(self):
        self.assertEqual(
            str(self.template),
            f'Template template123 for course {self.course.id}'
        )
