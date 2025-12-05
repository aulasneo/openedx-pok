"""
Mock course_overviews.models module for pylint analysis.
"""

from django.db import models


class CourseOverview(models.Model):
    """
    Mock CourseOverview model for pylint.
    """
    id = models.AutoField(primary_key=True)
    course_id = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, default="Test Course")

    class Meta:
        app_label = 'course_overviews'

    def __str__(self):
        return f"CourseOverview: {self.course_id}"
