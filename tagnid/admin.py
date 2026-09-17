from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Program, Registration, UserProfile, Vitals


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['default_program', 'role']


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'is_active', 'is_archived', 'created_at']
    list_filter = ['year', 'is_active', 'is_archived']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'default_program']
    list_filter = ['role', 'default_program']
    search_fields = ['user__username', 'user__email']


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['unique_code', 'program', 'first_name', 'last_name', 'gender', 'region', 'auxiliary_body', 'dob', 'age', 'created_at']
    list_filter = ['program', 'gender', 'region', 'auxiliary_body', 'created_at']
    search_fields = ['first_name', 'last_name', 'unique_code']
    readonly_fields = ['unique_code', 'age', 'created_at', 'updated_at']
    fieldsets = (
        ('Registration Code', {
            'fields': ('unique_code',)
        }),
        ('Personal Information', {
            'fields': ('program', 'first_name', 'last_name', 'dob', 'gender')
        }),
        ('Location & Organisation', {
            'fields': ('region', 'auxiliary_body')
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
