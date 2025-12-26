from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Q
import csv
from datetime import datetime
from .forms import CustomLoginForm
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
    """List all registrations with search and filter"""
    registrations = Registration.objects.select_related('vitals').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        registrations = registrations.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(unique_code__icontains=search_query)
        )
    
    # Filter by region
    region_filter = request.GET.get('region', '')
    if region_filter:
        registrations = registrations.filter(region=region_filter)
    
    # Filter by auxiliary body
    auxiliary_body_filter = request.GET.get('auxiliary_body', '')
    if auxiliary_body_filter:
        registrations = registrations.filter(auxiliary_body=auxiliary_body_filter)
    
    # Order by creation date (newest first)
    registrations = registrations.order_by('-created_at')
    
    return render(request, 'tagnid/registration_list.html', {
        'registrations': registrations,
        'search_query': search_query,
        'region_filter': region_filter,
        'auxiliary_body_filter': auxiliary_body_filter,
        'region_choices': Registration.REGION_CHOICES,
        'auxiliary_body_choices': Registration.AUXILIARY_BODY_CHOICES,
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
    """Delete a registration - Only staff/superusers can delete"""
    # Check if user has permission to delete (staff or superuser)
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to delete registrations.')
        return redirect('tagnid:registration_list')
    
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
    """Delete vitals for a registration - Only staff/superusers can delete"""
    # Check if user has permission to delete (staff or superuser)
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to delete vitals.')
        return redirect('tagnid:registration_detail', pk=registration_id)
    
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


@login_required
def export_registrations(request):
    """Export all registrations to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="registrations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Unique Code',
        'First Name',
        'Last Name',
        'Date of Birth',
        'Age',
        'Region',
        'Auxiliary Body',
        'Blood Group',
        'Height (cm)',
        'Created At',
        'Updated At'
    ])
    
    # Get filtered registrations (same filters as list view)
    registrations = _get_filtered_registrations(request)
    
    for registration in registrations:
        vitals = None
        try:
            vitals = registration.vitals
        except Vitals.DoesNotExist:
            pass
        
        writer.writerow([
            registration.unique_code or '',
            registration.first_name,
            registration.last_name,
            registration.dob.strftime('%Y-%m-%d') if registration.dob else '',
            registration.age if registration.age else '',
            registration.get_region_display(),
            registration.get_auxiliary_body_display(),
            vitals.blood_group if vitals and vitals.blood_group else '',
            vitals.height if vitals and vitals.height else '',
            registration.created_at.strftime('%Y-%m-%d %H:%M:%S') if registration.created_at else '',
            registration.updated_at.strftime('%Y-%m-%d %H:%M:%S') if registration.updated_at else '',
        ])
    
    return response


def _get_filtered_registrations(request):
    """Helper function to get filtered registrations based on request parameters"""
    registrations = Registration.objects.select_related('vitals').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        registrations = registrations.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(unique_code__icontains=search_query)
        )
    
    # Filter by region
    region_filter = request.GET.get('region', '')
    if region_filter:
        registrations = registrations.filter(region=region_filter)
    
    # Filter by auxiliary body
    auxiliary_body_filter = request.GET.get('auxiliary_body', '')
    if auxiliary_body_filter:
        registrations = registrations.filter(auxiliary_body=auxiliary_body_filter)
    
    return registrations.order_by('-created_at')


@login_required
def export_registrations_pdf(request, preview=False):
    """Export registrations to PDF with optional preview"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        messages.error(request, 'PDF generation library not installed. Please install reportlab.')
        return redirect('tagnid:registration_list')
    
    # Get filtered registrations
    registrations = _get_filtered_registrations(request)
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    if not preview:
        response['Content-Disposition'] = f'attachment; filename="registrations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    else:
        response['Content-Disposition'] = 'inline; filename="registrations_preview.pdf"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#000000'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#000000'),
        spaceAfter=12
    )
    
    # Title
    title = Paragraph("Majilis Khuddamul Ahmadiyya The Gambia<br/>National Registration Tajnid 2025", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Summary info
    summary_text = f"Total Registrations: {registrations.count()}<br/>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if request.GET.get('search'):
        summary_text += f"<br/>Search: {request.GET.get('search')}"
    if request.GET.get('region'):
        summary_text += f"<br/>Region: {dict(Registration.REGION_CHOICES).get(request.GET.get('region'), '')}"
    if request.GET.get('auxiliary_body'):
        summary_text += f"<br/>Auxiliary Body: {dict(Registration.AUXILIARY_BODY_CHOICES).get(request.GET.get('auxiliary_body'), '')}"
    
    summary = Paragraph(summary_text, styles['Normal'])
    story.append(summary)
    story.append(Spacer(1, 0.3*inch))
    
    # Prepare table data
    data = [['Unique Code', 'Name', 'Region', 'Auxiliary Body', 'DOB', 'Age', 'Blood Group', 'Height']]
    
    for registration in registrations:
        vitals = None
        try:
            vitals = registration.vitals
        except Vitals.DoesNotExist:
            pass
        
        name = f"{registration.first_name} {registration.last_name}"
        dob_str = registration.dob.strftime('%Y-%m-%d') if registration.dob else 'N/A'
        age_str = str(registration.age) if registration.age else 'N/A'
        blood_group = vitals.blood_group if vitals and vitals.blood_group else 'N/A'
        height = f"{vitals.height} cm" if vitals and vitals.height else 'N/A'
        
        data.append([
            registration.unique_code or 'N/A',
            name,
            registration.get_region_display(),
            registration.get_auxiliary_body_display(),
            dob_str,
            age_str,
            blood_group,
            height
        ])
    
    # Create table with column widths
    col_widths = [0.8*inch, 1.2*inch, 0.8*inch, 0.9*inch, 0.8*inch, 0.4*inch, 0.6*inch, 0.6*inch]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#bab148')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fdf4e3')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fdf4e3')]),
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)
    
    return response


@login_required
def export_registrations_pdf_preview(request):
    """Preview PDF export"""
    return export_registrations_pdf(request, preview=True)

