from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date


class Program(models.Model):
    name = models.CharField(max_length=120)
    year = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False, help_text='Archived programs are hidden from users but data is preserved.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', 'name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'year'], name='unique_program_name_year')
        ]

    def __str__(self):
        return f"{self.name} ({self.year})"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('program_manager', 'Program Manager'),
        ('male_data_entry', 'Male Data Entry'),
        ('female_data_entry', 'Female Data Entry'),
        ('viewer', 'Viewer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    default_program = models.ForeignKey(
        Program,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_users'
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='male_data_entry')

    def __str__(self):
        return f"{self.user.username} – {self.get_role_display()}"

    @property
    def is_admin_role(self):
        return self.role == 'admin'

    @property
    def gender_scope(self):
        """Returns the gender this role is restricted to, or None for no restriction."""
        if self.role == 'male_data_entry':
            return 'Male'
        if self.role == 'female_data_entry':
            return 'Female'
        return None

    @property
    def is_read_only(self):
        return self.role == 'viewer'


class RegistrationManager(models.Manager):
    """Custom manager for Registration model"""

    def backfill_unique_codes(self):
        """Backfill unique codes for registrations that don't have one"""
        from django.db import transaction
        from collections import defaultdict

        registrations = self.filter(unique_code__isnull=True).order_by('created_at', 'id')
        count = 0
        by_year = defaultdict(list)

        for registration in registrations:
            year = registration.program.year if registration.program else (
                registration.created_at.year if registration.created_at else 2025
            )
            by_year[year].append(registration)

        with transaction.atomic():
            for year, year_registrations in sorted(by_year.items()):
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

                for i, registration in enumerate(year_registrations, start=1):
                    next_num = max_num + i
                    registration.unique_code = f"{year}-{next_num:04d}"
                    registration.save(update_fields=['unique_code'])
                    count += 1

        return count


class Registration(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    REGION_CHOICES = [
        ('URR', 'URR'),
        ('LRR', 'LRR'),
        ('CRR', 'CRR'),
        ('NBR1', 'NBR1'),
        ('NBR2', 'NBR2'),
        ('BANJUL_KOMBO', 'BANJUL KOMBO'),
        ('FONI', 'FONI'),
    ]

    # All possible auxiliary body choices – validated against gender server-side
    AUXILIARY_BODY_CHOICES = [
        ('Atfal', 'Atfal'),
        ('Khuddam', 'Khuddam'),
        ('Ansar', 'Ansar'),
        ('Guest', 'Guest'),
        ('Lajina', 'Lajina'),
        ('Nasirat', 'Nasirat'),
    ]

    MALE_AUXILIARY_BODIES = {'Atfal', 'Khuddam', 'Ansar', 'Guest'}
    FEMALE_AUXILIARY_BODIES = {'Lajina', 'Nasirat'}

    program = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        related_name='registrations',
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True, verbose_name='Date of Birth')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
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

        year = self.program.year if self.program else (
            self.created_at.year if self.created_at else date.today().year
        )

        last_reg = Registration.objects.filter(
            unique_code__startswith=f"{year}-"
        ).exclude(pk=self.pk if self.pk else None).order_by('-unique_code').first()

        if last_reg and last_reg.unique_code:
            try:
                last_num = int(last_reg.unique_code.split('-')[1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                year_count = Registration.objects.filter(
                    created_at__year=year
                ).exclude(pk=self.pk if self.pk else None).count()
                next_num = year_count + 1
        else:
            next_num = 1

        proposed_code = f"{year}-{next_num:04d}"
        while Registration.objects.filter(unique_code=proposed_code).exclude(
            pk=self.pk if self.pk else None
        ).exists():
            next_num += 1
            proposed_code = f"{year}-{next_num:04d}"

        self.unique_code = proposed_code
        return self.unique_code

    def save(self, *args, **kwargs):
        if not self.unique_code:
            self.generate_unique_code()
        super().save(*args, **kwargs)

    @property
    def age(self):
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - (
                (today.month, today.day) < (self.dob.month, self.dob.day)
            )
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
