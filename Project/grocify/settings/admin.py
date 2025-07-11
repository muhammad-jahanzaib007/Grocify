from django.contrib import admin
from .models import ConfigSetting

class ConfigSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    search_fields = ['key', 'description']

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.groups.filter(name='Managers').exists()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.groups.filter(name='Managers').exists()

admin.site.register(ConfigSetting, ConfigSettingAdmin)