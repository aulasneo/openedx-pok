# Generated migration for mock course_overviews app

from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CourseOverview',
            fields=[
                ('id', CourseKeyField(primary_key=True, max_length=255, serialize=False)),
                ('display_name', models.CharField(default='Test Course', max_length=255)),
            ],
            options={
                'db_table': 'course_overviews_courseoverview',
            },
        ),
    ]
