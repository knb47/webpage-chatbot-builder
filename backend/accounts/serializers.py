from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import UploadedFile, Deployment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'password', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        return user
    
from .models import UploadedFile

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'uploaded_at']

class DeploymentSerializer(serializers.ModelSerializer):
    config_file = FileUploadSerializer()

    class Meta:
        model = Deployment
        fields = ['id', 'user', 'config_file', 'endpoint', 'deployed_at']