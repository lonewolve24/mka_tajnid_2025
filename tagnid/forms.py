from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Registration, Vitals


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
    class Meta:
        model = Registration
        fields = ['first_name', 'last_name', 'dob', 'region', 'auxiliary_body']
        widgets = {
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
            'region': forms.Select(attrs={
                'class': 'form-control'
            }),
            'auxiliary_body': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'dob': 'Date of Birth',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['auxiliary_body'].required = True
        self.fields['dob'].required = False


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

