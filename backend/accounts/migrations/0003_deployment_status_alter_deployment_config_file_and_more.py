# Generated by Django 5.0.7 on 2024-07-28 15:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_uploadedfile_file_deployment'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployment',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('marked_for_deletion', 'Marked for Deletion')], default='active', max_length=20),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='config_file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounts.uploadedfile'),
        ),
        migrations.AlterField(
            model_name='deployment',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
