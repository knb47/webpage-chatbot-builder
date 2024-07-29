# Generated by Django 5.0.7 on 2024-07-27 22:37

import backend.accounts.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='file',
            field=models.FileField(upload_to=backend.accounts.models.PathAndRename('uploads')),
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.URLField()),
                ('deployed_at', models.DateTimeField(auto_now_add=True)),
                ('config_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.uploadedfile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
