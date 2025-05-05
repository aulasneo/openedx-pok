"""
URLs for openedx_pok.
"""
from django.urls import re_path  # pylint: disable=unused-import
from django.views.generic import TemplateView  # pylint: disable=unused-import
from .views import CourseTemplateSettingsView

urlpatterns = [
    re_path(r'^settings/(?P<course_id>[^/]+)/$', CourseTemplateSettingsView.as_view(), name='pok-course-settings')
]
