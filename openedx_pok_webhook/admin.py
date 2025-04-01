"""
Admin settings for POK certificate integration.
"""
import logging

from django.contrib import admin

from .models import CertificatePokApi

logger = logging.getLogger(__name__)


class CertificatePokApiAdmin(admin.ModelAdmin):
    """Admin interface for Certificate model."""

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

    readonly_fields = [
        'created',
        'modified',
    ]


logger.debug("Registering Certificate")
admin.site.register(CertificatePokApi, CertificatePokApiAdmin)
