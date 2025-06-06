# Generated by Django 4.2.20 on 2025-04-29 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openedx_pok', '0007_remove_coursetemplate_api_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursetemplate',
            name='emission_type',
            field=models.CharField(blank=True, choices=[('pok', 'POK'), ('blockchain', 'Blockchain')], default='pok', help_text='Type of emission (blockchain or pok)', max_length=50, null=True),
        ),
    ]
