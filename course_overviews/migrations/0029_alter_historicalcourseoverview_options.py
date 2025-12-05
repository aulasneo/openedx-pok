# Placeholder migration to satisfy openedx_pok migration dependencies
# This migration number matches the Open edX course_overviews migration that
# openedx_pok depends on in production

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0001_initial'),
    ]

    operations = [
        # No operations needed - this is just a placeholder to satisfy dependencies
    ]
