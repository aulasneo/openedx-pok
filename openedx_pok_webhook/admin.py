"""
Admin settings for POK certificate integration.
"""
import logging

from django.contrib import admin
from .models import PokCertificate, CertificateTemplate

logger = logging.getLogger(__name__)


@admin.register(PokCertificate)
class CertificatePokApiAdmin(admin.ModelAdmin):
    """Admin interface for PokCertificate model."""

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


@admin.register(CertificateTemplate)
class CourseTemplateAdmin(admin.ModelAdmin):
    """Admin interface for CertificateTemplate model."""

    list_display = ['course', 'template_id', 'emission_type', 'api_key','created', 'modified']
    search_fields = ['course__id', 'template_id']
    readonly_fields = ['created', 'modified']
