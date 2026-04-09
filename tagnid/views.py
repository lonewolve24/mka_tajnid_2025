from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
import csv
from datetime import datetime
from django.contrib.auth.models import User
from .forms import CustomLoginForm, ProgramForm, RegistrationForm, UserCreateForm, UserEditForm, VitalsForm
from .models import Program, Registration, UserProfile, Vitals
from .service import (
    create_registration,
    update_registration,
    delete_registration,
    create_vitals,
    update_vitals,
    delete_vitals
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_user_profile(user):
    """Return UserProfile, creating a default one if it doesn't exist yet."""
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'male_data_entry'}
    )
    return profile


def get_active_program(request):
    """
    Resolve the active Program for the current request.

    Admin roles get None back (no restriction).
    Everyone else must have a default_program set on their profile.
    Returns (program_or_None, profile).
    """
    profile = get_user_profile(request.user)
    if profile.is_admin_role or request.user.is_superuser:
        return None, profile
    program_id = request.session.get('active_program_id')
    if program_id:
        try:
            return Program.objects.get(pk=program_id), profile
        except Program.DoesNotExist:
            pass
    # Fall back to profile default
    if profile.default_program:
        request.session['active_program_id'] = profile.default_program.pk
        return profile.default_program, profile
    return None, profile


def apply_role_scope(queryset, profile):
    """Apply gender filter based on role."""
    gender = profile.gender_scope
    if gender:
        queryset = queryset.filter(gender=gender)
    return queryset


def require_admin(view_func):
    """Decorator that restricts a view to admin role or superuser only."""
    def wrapper(request, *args, **kwargs):
        profile = get_user_profile(request.user)
        if not (profile.is_admin_role or request.user.is_superuser):
            messages.error(request, 'You do not have permission to access that page.')
            return redirect('tagnid:dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def require_program(view_func):
    """
    Decorator that redirects to no_program if the user has no active program
    and is not admin/superuser.
    """
    def wrapper(request, *args, **kwargs):
        profile = get_user_profile(request.user)
        if not profile.is_admin_role and not request.user.is_superuser:
            program, _ = get_active_program(request)
            if not program:
                return redirect('tagnid:no_program')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('tagnid:dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Store active program in session immediately on login
            profile = get_user_profile(user)
            if profile.default_program:
                request.session['active_program_id'] = profile.default_program.pk
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('tagnid:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()

    return render(request, 'tagnid/login.html', {'form': form})


def logout_view(request):
    request.session.pop('active_program_id', None)
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('tagnid:login')


@login_required
def no_program(request):
    return render(request, 'tagnid/no_program.html')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
@require_program
def dashboard(request):
    active_program, profile = get_active_program(request)
    all_programs = Program.objects.order_by('-year', 'name')

    # Admin can pick a program via ?program=<id> to drill into its stats
    selected_program = active_program
    selected_program_id = ''
    if not active_program:
        selected_program_id = request.GET.get('program', '')
        if selected_program_id:
            try:
                selected_program = Program.objects.get(pk=selected_program_id)
            except Program.DoesNotExist:
                selected_program = None

    base_qs = Registration.objects.all()
    if selected_program:
        base_qs = base_qs.filter(program=selected_program)
    base_qs = apply_role_scope(base_qs, profile)

    total_registrations = base_qs.count()

    region_stats = base_qs.values('region').annotate(count=Count('id')).order_by('-count')
    auxiliary_body_stats = base_qs.values('auxiliary_body').annotate(count=Count('id')).order_by('-count')
    gender_stats = base_qs.values('gender').annotate(count=Count('id')).order_by('gender')

    region_data = [
        {'name': dict(Registration.REGION_CHOICES).get(s['region'], s['region']), 'count': s['count']}
        for s in region_stats
    ]
    auxiliary_body_data = [
        {'name': dict(Registration.AUXILIARY_BODY_CHOICES).get(s['auxiliary_body'], s['auxiliary_body']), 'count': s['count']}
        for s in auxiliary_body_stats
    ]

    program_stats = None
    if not active_program:
        program_stats = Program.objects.annotate(count=Count('registrations')).order_by('-year', 'name')

    return render(request, 'tagnid/dashboard.html', {
        'total_registrations': total_registrations,
        'region_stats': region_data,
        'auxiliary_body_stats': auxiliary_body_data,
        'gender_stats': gender_stats,
        'program_stats': program_stats,
        'active_program': active_program,
        'selected_program': selected_program,
        'selected_program_id': selected_program_id,
        'all_programs': all_programs if not active_program else [],
        'profile': profile,
    })


# ---------------------------------------------------------------------------
# Registration list / CRUD
# ---------------------------------------------------------------------------

@login_required
@require_program
def registration_list(request):
    active_program, profile = get_active_program(request)

    registrations = Registration.objects.select_related('vitals', 'program').all()
    if active_program:
        registrations = registrations.filter(program=active_program)
    registrations = apply_role_scope(registrations, profile)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        registrations = registrations.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(unique_code__icontains=search_query)
        )

    # Filters – admin/manager can filter by gender; role-restricted users cannot
    region_filter = request.GET.get('region', '')
    if region_filter:
        registrations = registrations.filter(region=region_filter)

    auxiliary_body_filter = request.GET.get('auxiliary_body', '')
    if auxiliary_body_filter:
        registrations = registrations.filter(auxiliary_body=auxiliary_body_filter)

    gender_filter = ''
    if not profile.gender_scope:
        gender_filter = request.GET.get('gender', '')
        if gender_filter:
            registrations = registrations.filter(gender=gender_filter)

    program_filter = ''
    if not active_program:
        program_filter = request.GET.get('program', '')
        if program_filter:
            registrations = registrations.filter(program_id=program_filter)

    registrations = registrations.order_by('-created_at')

    paginator = Paginator(registrations, 20)
    page = request.GET.get('page', 1)
    try:
        registrations_page = paginator.page(page)
    except PageNotAnInteger:
        registrations_page = paginator.page(1)
    except EmptyPage:
        registrations_page = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()

    # Build auxiliary body choices scoped to role
    if profile.gender_scope == 'Male':
        auxiliary_body_choices = [(v, l) for v, l in Registration.AUXILIARY_BODY_CHOICES
                                  if v in Registration.MALE_AUXILIARY_BODIES]
    elif profile.gender_scope == 'Female':
        auxiliary_body_choices = [(v, l) for v, l in Registration.AUXILIARY_BODY_CHOICES
                                  if v in Registration.FEMALE_AUXILIARY_BODIES]
    else:
        auxiliary_body_choices = Registration.AUXILIARY_BODY_CHOICES

    return render(request, 'tagnid/registration_list.html', {
        'registrations': registrations_page,
        'search_query': search_query,
        'region_filter': region_filter,
        'auxiliary_body_filter': auxiliary_body_filter,
        'gender_filter': gender_filter,
        'program_filter': program_filter,
        'region_choices': Registration.REGION_CHOICES,
        'auxiliary_body_choices': auxiliary_body_choices,
        'gender_choices': Registration.GENDER_CHOICES,
        'program_choices': Program.objects.filter(is_active=True).order_by('-year', 'name') if not active_program else [],
        'query_string': query_string,
        'active_program': active_program,
        'profile': profile,
    })


@login_required
@require_program
def registration_create(request):
    active_program, profile = get_active_program(request)
    is_admin = profile.is_admin_role or request.user.is_superuser

    if profile.is_read_only:
        messages.error(request, 'You do not have permission to create registrations.')
        return redirect('tagnid:registration_list')

    if request.method == 'POST':
        form = RegistrationForm(request.POST, profile=profile, is_admin=is_admin)
        if form.is_valid():
            registration = form.save(commit=False)
            if not is_admin:
                registration.program = active_program
            registration.save()
            messages.success(request, f'Registration for {registration.first_name} {registration.last_name} created successfully!')
            return redirect('tagnid:registration_list')
    else:
        form = RegistrationForm(profile=profile, is_admin=is_admin)

    return render(request, 'tagnid/registration_form.html', {
        'form': form,
        'title': 'Create Registration',
        'active_program': active_program,
        'is_admin': is_admin,
    })


@login_required
@require_program
def registration_update(request, pk):
    active_program, profile = get_active_program(request)
    is_admin = profile.is_admin_role or request.user.is_superuser

    if profile.is_read_only:
        messages.error(request, 'You do not have permission to edit registrations.')
        return redirect('tagnid:registration_list')

    registration = get_object_or_404(Registration, pk=pk)

    if active_program and registration.program != active_program:
        messages.error(request, 'You do not have access to this registration.')
        return redirect('tagnid:registration_list')

    if request.method == 'POST':
        form = RegistrationForm(request.POST, instance=registration, profile=profile, is_admin=is_admin)
        if form.is_valid():
            updated = form.save(commit=False)
            if not is_admin:
                updated.program = active_program
            updated.save()
            messages.success(request, f'Registration for {updated.first_name} {updated.last_name} updated successfully!')
            return redirect('tagnid:registration_list')
    else:
        form = RegistrationForm(instance=registration, profile=profile, is_admin=is_admin)

    return render(request, 'tagnid/registration_form.html', {
        'form': form,
        'registration': registration,
        'title': 'Update Registration',
        'active_program': active_program,
        'is_admin': is_admin,
    })


@login_required
@require_program
def registration_delete(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to delete registrations.')
        return redirect('tagnid:registration_list')

    active_program, profile = get_active_program(request)
    registration = get_object_or_404(Registration, pk=pk)

    if active_program and registration.program != active_program:
        messages.error(request, 'You do not have access to this registration.')
        return redirect('tagnid:registration_list')

    if request.method == 'POST':
        registration.delete()
        messages.success(request, 'Registration deleted successfully!')
        return redirect('tagnid:registration_list')

    return render(request, 'tagnid/registration_confirm_delete.html', {
        'registration': registration
    })


@login_required
@require_program
def registration_detail(request, pk):
    active_program, profile = get_active_program(request)
    registration = get_object_or_404(Registration, pk=pk)

    if active_program and registration.program != active_program:
        messages.error(request, 'You do not have access to this registration.')
        return redirect('tagnid:registration_list')

    vitals = None
    try:
        vitals = registration.vitals
    except Vitals.DoesNotExist:
        pass

    return render(request, 'tagnid/registration_detail.html', {
        'registration': registration,
        'vitals': vitals,
        'profile': profile,
    })


# ---------------------------------------------------------------------------
# Vitals
# ---------------------------------------------------------------------------

@login_required
@require_program
def vitals_create(request, registration_id):
    active_program, profile = get_active_program(request)
    registration = get_object_or_404(Registration, pk=registration_id)

    if active_program and registration.program != active_program:
        messages.error(request, 'You do not have access to this registration.')
        return redirect('tagnid:registration_list')

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
@require_program
def vitals_update(request, registration_id):
    active_program, profile = get_active_program(request)
    registration = get_object_or_404(Registration, pk=registration_id)
    vitals = get_object_or_404(Vitals, registration=registration)

    if active_program and registration.program != active_program:
        messages.error(request, 'You do not have access to this registration.')
        return redirect('tagnid:registration_list')

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
@require_program
def vitals_delete(request, registration_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to delete vitals.')
        return redirect('tagnid:registration_list')

    active_program, profile = get_active_program(request)
    registration = get_object_or_404(Registration, pk=registration_id)
    vitals = get_object_or_404(Vitals, registration=registration)

    if active_program and registration.program != active_program:
        messages.error(request, 'You do not have access to this registration.')
        return redirect('tagnid:registration_list')

    if request.method == 'POST':
        vitals.delete()
        messages.success(request, 'Vitals deleted successfully!')
        return redirect('tagnid:registration_detail', pk=registration_id)

    return render(request, 'tagnid/vitals_confirm_delete.html', {
        'registration': registration,
        'vitals': vitals
    })


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

@login_required
@require_program
def export_registrations(request):
    active_program, profile = get_active_program(request)
    registrations = _get_filtered_registrations(request, active_program, profile)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="registrations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    writer = csv.writer(response)

    writer.writerow([
        'Unique Code', 'Program', 'Program Year',
        'First Name', 'Last Name', 'Gender',
        'Date of Birth', 'Age', 'Region', 'Auxiliary Body',
        'Blood Group', 'Height (cm)', 'Created At', 'Updated At'
    ])

    for registration in registrations:
        vitals = None
        try:
            vitals = registration.vitals
        except Vitals.DoesNotExist:
            pass

        writer.writerow([
            registration.unique_code or '',
            registration.program.name if registration.program else '',
            registration.program.year if registration.program else '',
            registration.first_name,
            registration.last_name,
            registration.get_gender_display(),
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


def _get_filtered_registrations(request, active_program, profile):
    registrations = Registration.objects.select_related('vitals', 'program').all()
    if active_program:
        registrations = registrations.filter(program=active_program)
    registrations = apply_role_scope(registrations, profile)

    search_query = request.GET.get('search', '')
    if search_query:
        registrations = registrations.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(unique_code__icontains=search_query)
        )

    region_filter = request.GET.get('region', '')
    if region_filter:
        registrations = registrations.filter(region=region_filter)

    auxiliary_body_filter = request.GET.get('auxiliary_body', '')
    if auxiliary_body_filter:
        registrations = registrations.filter(auxiliary_body=auxiliary_body_filter)

    if not profile.gender_scope:
        gender_filter = request.GET.get('gender', '')
        if gender_filter:
            registrations = registrations.filter(gender=gender_filter)

    if not active_program:
        program_filter = request.GET.get('program', '')
        if program_filter:
            registrations = registrations.filter(program_id=program_filter)

    return registrations.order_by('-created_at')


@login_required
@require_program
def export_registrations_pdf(request, preview=False):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        messages.error(request, 'PDF generation library not installed. Please install reportlab.')
        return redirect('tagnid:registration_list')

    active_program, profile = get_active_program(request)
    registrations = _get_filtered_registrations(request, active_program, profile)

    response = HttpResponse(content_type='application/pdf')
    if not preview:
        response['Content-Disposition'] = f'attachment; filename="registrations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    else:
        response['Content-Disposition'] = 'inline; filename="registrations_preview.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#000000'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    program_label = str(active_program) if active_program else 'All Programs'
    title = Paragraph(
        f"Ahmadiyya Muslim Jamaat The Gambia Data System<br/>{program_label}",
        title_style
    )
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))

    summary_text = f"Total Registrations: {registrations.count()}<br/>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    data = [['Unique Code', 'Program', 'Name', 'Gender', 'Region', 'Auxiliary Body', 'DOB', 'Age', 'Blood', 'Height']]

    for reg in registrations:
        vitals = None
        try:
            vitals = reg.vitals
        except Vitals.DoesNotExist:
            pass

        data.append([
            reg.unique_code or 'N/A',
            str(reg.program) if reg.program else 'N/A',
            f"{reg.first_name} {reg.last_name}",
            reg.get_gender_display(),
            reg.get_region_display(),
            reg.get_auxiliary_body_display(),
            reg.dob.strftime('%Y-%m-%d') if reg.dob else 'N/A',
            str(reg.age) if reg.age else 'N/A',
            vitals.blood_group if vitals and vitals.blood_group else 'N/A',
            f"{vitals.height} cm" if vitals and vitals.height else 'N/A',
        ])

    col_widths = [0.8 * inch, 1.1 * inch, 1.1 * inch, 0.55 * inch, 0.65 * inch,
                  0.85 * inch, 0.75 * inch, 0.35 * inch, 0.5 * inch, 0.55 * inch]
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
    doc.build(story)
    return response


@login_required
@require_program
def export_registrations_pdf_preview(request):
    return export_registrations_pdf(request, preview=True)


# ---------------------------------------------------------------------------
# Programs overview (all users – read-only program browser)
# ---------------------------------------------------------------------------

@login_required
@require_program
def programs_overview(request):
    """Tab that lists active programs. Admin sees all incl. archived toggle."""
    active_program, profile = get_active_program(request)
    show_archived = request.GET.get('archived') == '1'

    if profile.is_admin_role or request.user.is_superuser:
        programs = Program.objects.all()
        if not show_archived:
            programs = programs.filter(is_archived=False)
    else:
        programs = Program.objects.filter(is_active=True, is_archived=False)

    programs = programs.annotate(count=Count('registrations')).order_by('-year', 'name')

    return render(request, 'tagnid/programs_overview.html', {
        'programs': programs,
        'active_program': active_program,
        'profile': profile,
        'show_archived': show_archived,
    })


# ---------------------------------------------------------------------------
# Settings – User management (admin only)
# ---------------------------------------------------------------------------

@login_required
@require_admin
def settings_users(request):
    users = User.objects.select_related('profile', 'profile__default_program').order_by('username')
    return render(request, 'tagnid/settings_users.html', {
        'users': users,
        'active_program': None,
        'profile': get_user_profile(request.user),
    })


@login_required
@require_admin
def settings_user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            profile = UserProfile.objects.create(
                user=user,
                role=form.cleaned_data['role'],
                default_program=form.cleaned_data.get('default_program'),
            )
            if profile.default_program:
                # Pre-store so session is ready on first login
                pass
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('tagnid:settings_users')
    else:
        form = UserCreateForm()

    return render(request, 'tagnid/user_form.html', {
        'form': form,
        'title': 'Create User',
        'active_program': None,
        'profile': get_user_profile(request.user),
    })


@login_required
@require_admin
def settings_user_edit(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    target_profile = get_user_profile(target_user)

    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            target_profile.role = form.cleaned_data['role']
            target_profile.default_program = form.cleaned_data.get('default_program')
            target_profile.save()
            target_user.is_active = form.cleaned_data.get('is_active', True)
            target_user.save()
            messages.success(request, f'User "{target_user.username}" updated.')
            return redirect('tagnid:settings_users')
    else:
        form = UserEditForm(initial={
            'role': target_profile.role,
            'default_program': target_profile.default_program,
            'is_active': target_user.is_active,
        })

    return render(request, 'tagnid/user_form.html', {
        'form': form,
        'title': f'Edit User: {target_user.username}',
        'target_user': target_user,
        'active_program': None,
        'profile': get_user_profile(request.user),
    })


# ---------------------------------------------------------------------------
# Settings – Program management (admin only)
# ---------------------------------------------------------------------------

@login_required
@require_admin
def settings_programs(request):
    programs = Program.objects.annotate(count=Count('registrations')).order_by('-year', 'name')
    return render(request, 'tagnid/settings_programs.html', {
        'programs': programs,
        'active_program': None,
        'profile': get_user_profile(request.user),
    })


@login_required
@require_admin
def settings_program_create(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            messages.success(request, f'Program "{program}" created successfully.')
            return redirect('tagnid:settings_programs')
    else:
        form = ProgramForm()

    return render(request, 'tagnid/program_form.html', {
        'form': form,
        'title': 'Create Program',
        'active_program': None,
        'profile': get_user_profile(request.user),
    })


@login_required
@require_admin
def settings_program_edit(request, program_id):
    program = get_object_or_404(Program, pk=program_id)

    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, f'Program "{program}" updated.')
            return redirect('tagnid:settings_programs')
    else:
        form = ProgramForm(instance=program)

    return render(request, 'tagnid/program_form.html', {
        'form': form,
        'title': f'Edit Program: {program}',
        'program': program,
        'active_program': None,
        'profile': get_user_profile(request.user),
    })
