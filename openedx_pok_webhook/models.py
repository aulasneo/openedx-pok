"""
Database models for openedx_pok_webhook.
"""

from django.db import models
from model_utils.models import TimeStampedModel
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.contrib.auth import get_user_model

User = get_user_model()

class CertificatePokApi(TimeStampedModel):
    """
    Model for storing POK certificate data.
    .. no_pii:
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    course_id = models.CharField(
        max_length=255,
        help_text="Course ID associated with the certificate",
        blank=False,
        null=False
    )
    pok_certificate_id = models.CharField(
        max_length=255,
        help_text="Certificate ID in the Open edX platform",
        blank=True,
        null=True
    )
    state = models.CharField(
        max_length=50,
        help_text="State of the POK certificate (e.g., 'emitted')",
        blank=True,
        null=True
    )
    view_url = models.URLField(
        max_length=255,
        help_text="URL to view the POK certificate",
        blank=True,
        null=True
    )
    emission_date = models.DateTimeField(
        help_text="Date when the certificate was emitted",
        blank=True,
        null=True
    )
    emission_type = models.CharField(
        max_length=50,
        help_text="Type of emission (e.g., 'pok')",
        blank=True,
        default="pok"
    )
    custom_parameters = models.JSONField(
        help_text="Custom parameters associated with the certificate",
        blank=True,
        null=True,)
    
    title = models.CharField(
        max_length=255,
        help_text="Title of the POK certificate",
        blank=True,
        null=True
    )
    emitter = models.CharField(
        max_length=255,
        help_text="Emitter of the POK certificate",
        blank=True,
        null=True
    )
    tags = models.JSONField(
        help_text="Tags associated with the certificate",
        blank=True,
        null=True,
        default=list
    )
    receiver_email = models.EmailField(
        max_length=255,
        help_text="Email of the certificate receiver",
        blank=True,
        null=True
    )
    receiver_name = models.CharField(
        max_length=255,
        help_text="Name of the certificate receiver",
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ('user_id', 'course_id')

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return f'POK Certificate for user {self.user_id} in course {self.course_id}'

class CourseTemplate(TimeStampedModel):
    """
    Model for linking a course with a template.
    """
    course = models.ForeignKey(
        CourseOverview,
        on_delete=models.CASCADE,
        help_text="Course ID associated with the template",
    )
    template_id = models.TextField(
        help_text="Template ID associated with the course",
        blank=False,
        null=False
    )
    
    emission_type = models.CharField(
        max_length=50,
        help_text="Type of emission (blockchain or pok)",
        blank=True,
        null=True,
        default="pok",
        choices=[
            ('pok', 'POK'),
            ('blockchain', 'Blockchain')
        ]
    )
    
    

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return f'Template {self.template_id} for course {self.course_id}'