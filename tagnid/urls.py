from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'tagnid'

urlpatterns = [
    # Root redirect to login (will redirect to dashboard if already logged in)
    path('', RedirectView.as_view(pattern_name='tagnid:login', permanent=False), name='root'),
    
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Registration URLs
    path('registrations/', views.registration_list, name='registration_list'),
    path('registration/create/', views.registration_create, name='registration_create'),
    path('registration/<int:pk>/', views.registration_detail, name='registration_detail'),
    path('registration/<int:pk>/update/', views.registration_update, name='registration_update'),
    path('registration/<int:pk>/delete/', views.registration_delete, name='registration_delete'),
    
    # Vitals URLs
    path('registration/<int:registration_id>/vitals/create/', views.vitals_create, name='vitals_create'),
    path('registration/<int:registration_id>/vitals/update/', views.vitals_update, name='vitals_update'),
    path('registration/<int:registration_id>/vitals/delete/', views.vitals_delete, name='vitals_delete'),
]

