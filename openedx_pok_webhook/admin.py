"""
Admin settings for POK certificate integration.
"""
import logging

from django.contrib import admin
from .models import CertificatePokApi, CourseTemplate

logger = logging.getLogger(__name__)


@admin.register(CertificatePokApi)
class CertificatePokApiAdmin(admin.ModelAdmin):
    """Admin interface for CertificatePokApi model."""

    list_display = [
        'user_id',
        'course_id',
        'state',
        'view_url',
        'created',
        'modified',
    ]
    search_fields = [
        'user_id',
        'course_id',
        'certificate_id',
        'view_url',
        'title',
        'receiver_email',
        'receiver_name',
    ]
    list_filter = [
        'state',
        'emitter',
        'emission_type',
        'created',
        'modified',
    ]
    readonly_fields = ['created', 'modified']


@admin.register(CourseTemplate)
class CourseTemplateAdmin(admin.ModelAdmin):
    """Admin interface for CourseTemplate model."""

    list_display = ['course', 'template_id', 'created', 'modified']
    search_fields = ['course__id', 'template_id']
    readonly_fields = ['created', 'modified']
