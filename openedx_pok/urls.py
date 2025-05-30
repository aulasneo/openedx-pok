"""
URLs for openedx_pok.
"""
from django.urls import re_path  # pylint: disable=unused-import

from .views import CertificateImageDownloadView


urlpatterns = [
    #re_path(r'^settings/(?P<course_id>[^/]+)/$', CourseTemplateSettingsView.as_view(), name='pok-course-settings')
    re_path(r'^certificate$', CertificateImageDownloadView.as_view(), name='pok-certificate-download'),
]
