from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomLoginForm
from django.db.models import Count
from .models import Registration, Vitals
from .forms import RegistrationForm, VitalsForm
from .service import (
    create_registration,
    update_registration,
    delete_registration,
    create_vitals,
    update_vitals,
    delete_vitals
)


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('tagnid:dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('tagnid:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'tagnid/login.html', {'form': form})


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('tagnid:login')


@login_required
def dashboard(request):
    """Dashboard with statistics"""
    # Total registrations
    total_registrations = Registration.objects.count()
    
    # Statistics by region
    region_stats = Registration.objects.values('region').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Statistics by auxiliary body
    auxiliary_body_stats = Registration.objects.values('auxiliary_body').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get display names for regions and auxiliary body
    region_data = []
    for stat in region_stats:
        region_data.append({
            'name': dict(Registration.REGION_CHOICES).get(stat['region'], stat['region']),
            'count': stat['count']
        })
    
    auxiliary_body_data = []
    for stat in auxiliary_body_stats:
        auxiliary_body_data.append({
            'name': dict(Registration.AUXILIARY_BODY_CHOICES).get(stat['auxiliary_body'], stat['auxiliary_body']),
            'count': stat['count']
        })
    
    return render(request, 'tagnid/dashboard.html', {
        'total_registrations': total_registrations,
        'region_stats': region_data,
        'auxiliary_body_stats': auxiliary_body_data,
    })


@login_required
def registration_list(request):
    """List all registrations"""
    registrations = Registration.objects.all()
    return render(request, 'tagnid/registration_list.html', {
        'registrations': registrations
    })


@login_required
def registration_create(request):
    """Create a new registration"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save()
            messages.success(request, f'Registration for {registration.first_name} {registration.last_name} created successfully!')
            return redirect('tagnid:registration_list')
    else:
        form = RegistrationForm()
    
    return render(request, 'tagnid/registration_form.html', {
        'form': form,
        'title': 'Create Registration'
    })


@login_required
def registration_update(request, pk):
    """Update an existing registration"""
    registration = get_object_or_404(Registration, pk=pk)
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST, instance=registration)
        if form.is_valid():
            registration = form.save()
            messages.success(request, f'Registration for {registration.first_name} {registration.last_name} updated successfully!')
            return redirect('tagnid:registration_list')
    else:
        form = RegistrationForm(instance=registration)
    
    return render(request, 'tagnid/registration_form.html', {
        'form': form,
        'registration': registration,
        'title': 'Update Registration'
    })


@login_required
def registration_delete(request, pk):
    """Delete a registration"""
    registration = get_object_or_404(Registration, pk=pk)
    
    if request.method == 'POST':
        registration.delete()
        messages.success(request, 'Registration deleted successfully!')
        return redirect('tagnid:registration_list')
    
    return render(request, 'tagnid/registration_confirm_delete.html', {
        'registration': registration
    })


@login_required
def registration_detail(request, pk):
    """View registration details"""
    registration = get_object_or_404(Registration, pk=pk)
    vitals = None
    try:
        vitals = registration.vitals
    except Vitals.DoesNotExist:
        pass
    
    return render(request, 'tagnid/registration_detail.html', {
        'registration': registration,
        'vitals': vitals
    })


@login_required
def vitals_create(request, registration_id):
    """Create vitals for a registration"""
    registration = get_object_or_404(Registration, pk=registration_id)
    
    if request.method == 'POST':
        form = VitalsForm(request.POST)
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.registration = registration
            vitals.save()
            messages.success(request, 'Vitals created successfully!')
            return redirect('tagnid:registration_detail', pk=registration_id)
    else:
        form = VitalsForm()
    
    return render(request, 'tagnid/vitals_form.html', {
        'form': form,
        'registration': registration,
        'title': 'Create Vitals'
    })


@login_required
def vitals_update(request, registration_id):
    """Update vitals for a registration"""
    registration = get_object_or_404(Registration, pk=registration_id)
    vitals = get_object_or_404(Vitals, registration=registration)
    
    if request.method == 'POST':
        form = VitalsForm(request.POST, instance=vitals)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vitals updated successfully!')
            return redirect('tagnid:registration_detail', pk=registration_id)
    else:
        form = VitalsForm(instance=vitals)
    
    return render(request, 'tagnid/vitals_form.html', {
        'form': form,
        'registration': registration,
        'vitals': vitals,
        'title': 'Update Vitals'
    })


@login_required
def vitals_delete(request, registration_id):
    """Delete vitals for a registration"""
    registration = get_object_or_404(Registration, pk=registration_id)
    vitals = get_object_or_404(Vitals, registration=registration)
    
    if request.method == 'POST':
        vitals.delete()
        messages.success(request, 'Vitals deleted successfully!')
        return redirect('tagnid:registration_detail', pk=registration_id)
    
    return render(request, 'tagnid/vitals_confirm_delete.html', {
        'registration': registration,
        'vitals': vitals
    })

