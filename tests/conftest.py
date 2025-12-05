#!/usr/bin/env python
"""
pytest configuration and fixtures for openedx-pok tests.
"""

import django
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from course_overviews.models import CourseOverview as MockCourseOverview

# Configure Django settings before importing models
if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'course_overviews',
            'openedx_pok',
        ],
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
        MIGRATION_MODULES={
            'course_overviews': 'course_overviews.migrations_not_used',
            'openedx_pok': 'openedx_pok.migrations_not_used',
        },
        # Disable migrations completely
        DISABLE_MIGRATIONS=True,
    )

django.setup()


@pytest.fixture
def mock_course_overview():
    """Create a mock CourseOverview instance."""
    return MockCourseOverview.objects.create(
        course_id="course-v1:test+Test+2023",
        display_name="Test Course"
    )


@pytest.fixture
def test_user():
    """Create a test user."""
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
