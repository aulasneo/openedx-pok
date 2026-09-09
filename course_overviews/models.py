"""
Mock course_overviews.models module for pylint analysis.
"""

from django.db import models
from opaque_keys.edx.django.models import CourseKeyField


class CourseOverview(models.Model):
    """
    Mock CourseOverview model for pylint.
    """
    id = CourseKeyField(primary_key=True, max_length=255)
    display_name = models.CharField(max_length=255, default="Test Course")

    class Meta:
        app_label = 'course_overviews'

    def __str__(self):
        return f"CourseOverview: {self.id}"
