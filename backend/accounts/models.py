from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    pass

class UploadedFile(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)