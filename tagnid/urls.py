from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'tagnid'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='tagnid:login', permanent=False), name='root'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('no-program/', views.no_program, name='no_program'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Programs overview (tab)
    path('programs/', views.programs_overview, name='programs_overview'),

    # Registration URLs
    path('registrations/', views.registration_list, name='registration_list'),
    path('registrations/export/', views.export_registrations, name='export_registrations'),
    path('registrations/export/pdf/', views.export_registrations_pdf, name='export_registrations_pdf'),
    path('registrations/export/pdf/preview/', views.export_registrations_pdf_preview, name='export_registrations_pdf_preview'),
    path('registration/create/', views.registration_create, name='registration_create'),
    path('registration/<int:pk>/', views.registration_detail, name='registration_detail'),
    path('registration/<int:pk>/update/', views.registration_update, name='registration_update'),
    path('registration/<int:pk>/delete/', views.registration_delete, name='registration_delete'),

    # Vitals URLs
    path('registration/<int:registration_id>/vitals/create/', views.vitals_create, name='vitals_create'),
    path('registration/<int:registration_id>/vitals/update/', views.vitals_update, name='vitals_update'),
    path('registration/<int:registration_id>/vitals/delete/', views.vitals_delete, name='vitals_delete'),

    # Settings – Users (admin only)
    path('settings/users/', views.settings_users, name='settings_users'),
    path('settings/users/create/', views.settings_user_create, name='settings_user_create'),
    path('settings/users/<int:user_id>/edit/', views.settings_user_edit, name='settings_user_edit'),

    # Settings – Programs (admin only)
    path('settings/programs/', views.settings_programs, name='settings_programs'),
    path('settings/programs/create/', views.settings_program_create, name='settings_program_create'),
    path('settings/programs/<int:program_id>/edit/', views.settings_program_edit, name='settings_program_edit'),
]
