from django.contrib import admin
from .models import Registration, Vitals


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'region', 'majilis', 'dob', 'age', 'created_at']
    list_filter = ['region', 'majilis', 'created_at']
    search_fields = ['first_name', 'last_name']
    readonly_fields = ['age', 'created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'dob')
        }),
        ('Location & Organization', {
            'fields': ('region', 'majilis')
        }),
        ('Additional Information', {
            'fields': ('age', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = ['registration', 'blood_group', 'height', 'created_at']
    list_filter = ['blood_group', 'created_at']
    search_fields = ['registration__first_name', 'registration__last_name']
    readonly_fields = ['created_at', 'updated_at']

