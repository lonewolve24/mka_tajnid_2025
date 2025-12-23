from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date


class Registration(models.Model):
    REGION_CHOICES = [
        ('URR', 'URR'),
        ('LRR', 'LRR'),
        ('CRR', 'CRR'),
        ('NBR1', 'NBR1'),
        ('NBR2', 'NBR2'),
        ('BANJUL_KOMBO', 'BANJUL KOMBO'),
        ('FONI', 'FONI'),
    ]
    
    AUXILIARY_BODY_CHOICES = [
        ('Atfal', 'Atfal'),
        ('Khuddam', 'Khuddam'),
        ('Ansar', 'Ansar'),
        ('Guest', 'Guest'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True, verbose_name='Date of Birth')
    region = models.CharField(max_length=20, choices=REGION_CHOICES)
    auxiliary_body = models.CharField(max_length=20, choices=AUXILIARY_BODY_CHOICES, verbose_name='Auxiliary Body')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Registration'
        verbose_name_plural = 'Registrations'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None


class Vitals(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name='vitals'
    )
    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUP_CHOICES,
        null=True,
        blank=True
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text='Height in cm'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vitals'
        verbose_name_plural = 'Vitals'
    
    def __str__(self):
        return f"Vitals for {self.registration.first_name} {self.registration.last_name}"
