from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.deconstruct import deconstructible

@deconstructible
class PathAndRename:
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
        return f'{self.path}/user_{instance.user.id}/{filename}'

class CustomUser(AbstractUser):
    pass

class UploadedFile(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    file = models.FileField(upload_to=PathAndRename('uploads'))
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Deployment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('marked_for_deletion', 'Marked for Deletion'),
    ]

    user = models.ForeignKey(get_user_model(), null=True, on_delete=models.SET_NULL)
    config_file = models.ForeignKey(UploadedFile, on_delete=models.PROTECT)
    endpoint = models.URLField()
    deployed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')