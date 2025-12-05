# Generated migration for mock course_overviews app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CourseOverview',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('course_id', models.CharField(max_length=255, unique=True)),
                ('display_name', models.CharField(default='Test Course', max_length=255)),
            ],
            options={
                'db_table': 'course_overviews_courseoverview',
            },
        ),
    ]
