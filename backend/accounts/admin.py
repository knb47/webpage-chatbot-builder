from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UploadedFile, Deployment

class CustomUserAdmin(UserAdmin):
    model = CustomUser

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file', 'uploaded_at')
    search_fields = ('user__username', 'file')

@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'config_file', 'endpoint', 'deployed_at', 'status')
    search_fields = ('user__username', 'endpoint')
    list_filter = ('status',)

admin.site.register(CustomUser, CustomUserAdmin)