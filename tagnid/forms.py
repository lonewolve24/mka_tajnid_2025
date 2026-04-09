from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Program, Registration, UserProfile, Vitals


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )


class RegistrationForm(forms.ModelForm):
    """
    Registration form scoped to the user's role.

    Pass profile=<UserProfile> so the form can:
    - Show program picker for admin/superuser (no active program)
    - Lock gender for data-entry roles (one-choice select)
    - Show only appropriate auxiliary body choices
    - Validate gender ↔ auxiliary body server-side
    """

    class Meta:
        model = Registration
        fields = ['program', 'first_name', 'last_name', 'dob', 'gender', 'region', 'auxiliary_body']
        widgets = {
            'program': forms.Select(attrs={
                'class': 'form-control'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'dob': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Select date of birth'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_gender'
            }),
            'region': forms.Select(attrs={
                'class': 'form-control'
            }),
            'auxiliary_body': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_auxiliary_body'
            }),
        }
        labels = {
            'dob': 'Date of Birth',
        }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        self.is_admin = kwargs.pop('is_admin', False)
        super().__init__(*args, **kwargs)

        self.fields['dob'].required = False
        self.fields['gender'].required = True
        self.fields['auxiliary_body'].required = True

        if self.is_admin:
            # Admin/superuser: show program picker, all gender + auxiliary choices
            self.fields['program'].queryset = Program.objects.filter(
                is_active=True, is_archived=False
            ).order_by('-year', 'name')
            self.fields['program'].required = True
            self.fields['program'].empty_label = '— Select programme —'
        else:
            # Regular roles: program is hidden/auto-set by view
            del self.fields['program']

        gender_scope = self.profile.gender_scope if self.profile else None

        if gender_scope == 'Male':
            self.fields['gender'].choices = [('Male', 'Male')]
            self.fields['gender'].initial = 'Male'
            self.fields['gender'].widget.attrs['class'] = 'form-control bg-light'
            self.fields['auxiliary_body'].choices = [
                (v, l) for v, l in Registration.AUXILIARY_BODY_CHOICES
                if v in Registration.MALE_AUXILIARY_BODIES
            ]
        elif gender_scope == 'Female':
            self.fields['gender'].choices = [('Female', 'Female')]
            self.fields['gender'].initial = 'Female'
            self.fields['gender'].widget.attrs['class'] = 'form-control bg-light'
            self.fields['auxiliary_body'].choices = [
                (v, l) for v, l in Registration.AUXILIARY_BODY_CHOICES
                if v in Registration.FEMALE_AUXILIARY_BODIES
            ]
        # else: admin/manager sees all choices; JS handles dynamic filtering

    def clean(self):
        cleaned_data = super().clean()
        gender = cleaned_data.get('gender')
        auxiliary_body = cleaned_data.get('auxiliary_body')

        if self.profile and self.profile.gender_scope:
            gender = self.profile.gender_scope
            cleaned_data['gender'] = gender

        if gender and auxiliary_body:
            if gender == 'Male' and auxiliary_body in Registration.FEMALE_ONLY_AUXILIARY_BODIES:
                self.add_error(
                    'auxiliary_body',
                    f'"{auxiliary_body}" is a female auxiliary body and cannot be selected for a Male registration.'
                )
            elif gender == 'Female' and auxiliary_body in Registration.MALE_ONLY_AUXILIARY_BODIES:
                self.add_error(
                    'auxiliary_body',
                    f'"{auxiliary_body}" is a male auxiliary body and cannot be selected for a Female registration.'
                )

        return cleaned_data


class UserCreateForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    default_program = forms.ModelChoiceField(
        queryset=Program.objects.filter(is_active=True, is_archived=False).order_by('-year', 'name'),
        required=False,
        empty_label='No program (admin only)',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with that username already exists.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        if password:
            try:
                validate_password(password)
            except forms.ValidationError as e:
                self.add_error('password', e)
        return cleaned_data


class UserEditForm(forms.Form):
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    default_program = forms.ModelChoiceField(
        queryset=Program.objects.filter(is_active=True, is_archived=False).order_by('-year', 'name'),
        required=False,
        empty_label='No program (admin only)',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'year', 'is_active', 'is_archived']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tajnid 2026'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2026', 'min': '2000', 'max': '2100'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_archived': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': 'Active (visible to users)',
            'is_archived': 'Archived (read-only, hidden from users)',
        }


class VitalsForm(forms.ModelForm):
    class Meta:
        model = Vitals
        fields = ['blood_group', 'height']
        widgets = {
            'blood_group': forms.Select(attrs={
                'class': 'form-control'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Height in cm',
                'step': '0.01',
                'min': '0',
                'max': '300'
            }),
        }
        labels = {
            'blood_group': 'Blood Group',
            'height': 'Height (cm)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['blood_group'].required = False
        self.fields['height'].required = False
