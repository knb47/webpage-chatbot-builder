# Generated by Django 5.0.7 on 2024-07-31 20:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_deployment_status_alter_deployment_config_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployment',
            name='chatbot_name',
            field=models.CharField(default='default_chatbot_name', max_length=255),
        ),
    ]
