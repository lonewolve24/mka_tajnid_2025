from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date


class RegistrationManager(models.Manager):
    """Custom manager for Registration model"""
    
    def backfill_unique_codes(self):
        """Backfill unique codes for registrations that don't have one"""
        from django.db import transaction
        
        registrations = self.filter(unique_code__isnull=True).order_by('created_at', 'id')
        count = 0
        
        # Group by year for proper sequential numbering
        from collections import defaultdict
        by_year = defaultdict(list)
        
        for registration in registrations:
            year = registration.created_at.year if registration.created_at else 2025
            by_year[year].append(registration)
        
        with transaction.atomic():
            for year, year_registrations in sorted(by_year.items()):
                # Get the highest number for this year
                existing_codes = self.filter(
                    unique_code__startswith=f"{year}-"
                ).exclude(unique_code__isnull=True).values_list('unique_code', flat=True)
                
                max_num = 0
                for code in existing_codes:
                    try:
                        num = int(code.split('-')[1])
                        max_num = max(max_num, num)
                    except (ValueError, IndexError):
                        pass
                
                # Assign sequential numbers starting from max_num + 1
                for i, registration in enumerate(year_registrations, start=1):
                    next_num = max_num + i
                    registration.unique_code = f"{year}-{next_num:04d}"
                    registration.save(update_fields=['unique_code'])
                    count += 1
        
        return count


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
    unique_code = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='Unique Registration Code')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = RegistrationManager()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Registration'
        verbose_name_plural = 'Registrations'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def generate_unique_code(self):
        """Generate a unique code in format: YEAR-NNNN (e.g., 2025-0001)"""
        if self.unique_code:
            return self.unique_code
        
        year = self.created_at.year if self.created_at else date.today().year
        
        # Find the highest number for this year
        last_reg = Registration.objects.filter(
            unique_code__startswith=f"{year}-"
        ).exclude(pk=self.pk if self.pk else None).order_by('-unique_code').first()
        
        if last_reg and last_reg.unique_code:
            try:
                last_num = int(last_reg.unique_code.split('-')[1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                # If parsing fails, count existing registrations for this year
                year_count = Registration.objects.filter(
                    created_at__year=year
                ).exclude(pk=self.pk if self.pk else None).count()
                next_num = year_count + 1
        else:
            # No existing codes for this year, start from 1
            next_num = 1
        
        # Ensure uniqueness by checking if code already exists
        proposed_code = f"{year}-{next_num:04d}"
        while Registration.objects.filter(unique_code=proposed_code).exclude(pk=self.pk if self.pk else None).exists():
            next_num += 1
            proposed_code = f"{year}-{next_num:04d}"
        
        self.unique_code = proposed_code
        return self.unique_code
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate unique code if not set"""
        if not self.unique_code:
            self.generate_unique_code()
        super().save(*args, **kwargs)
    
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
