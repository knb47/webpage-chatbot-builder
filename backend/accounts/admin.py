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
    list_display = ('id', 'user', 'config_file_name', 'endpoint', 'deployed_at', 'status')
    search_fields = ('user__username', 'endpoint')
    list_filter = ('status',)

    def config_file_name(self, obj):
        return obj.config_file.file.name
    config_file_name.short_description = 'Config File'

admin.site.register(CustomUser, CustomUserAdmin)
