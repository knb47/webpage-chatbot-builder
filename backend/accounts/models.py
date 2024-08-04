# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.deconstruct import deconstructible
from django.utils import timezone

@deconstructible
class PathAndRename:
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        return f'{self.path}/user_{instance.user.id}/{filename}'

# Define custom user model
class CustomUser(AbstractUser):
    pass

# Model for uploaded files
class UploadedFile(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    file_name = models.CharField(max_length=255)
    chat_configuration_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    has_deployment = models.BooleanField(default=False)

    def __str__(self):
        return self.file_name

# Model for deployments
class Deployment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('marked_for_deletion', 'Marked for Deletion'),
    ]
    user = models.ForeignKey(get_user_model(), null=True, on_delete=models.SET_NULL)
    config_file = models.ForeignKey(UploadedFile, null=True, blank=True, on_delete=models.SET_NULL, related_name='deployments')
    chatbot_name = models.CharField(max_length=255)
    config_file_path = models.CharField(max_length=255)
    config_file_name = models.CharField(max_length=255)
    endpoint = models.URLField()
    deployed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    resource_name = models.CharField(max_length=511, blank=True, editable=False)

    def __str__(self):
        return self.chatbot_name

class EmailLog(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    success = models.BooleanField()
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Email to {self.recipient} at {self.sent_at} - {'Success' if self.success else 'Failed'}"
