from django.test import TestCase, Client
from django.contrib.auth.models import User, Group, Permission
from django.urls import reverse
from .models import Registration, Vitals
from datetime import date


class RegistrationCRUDTests(TestCase):
    """Test CRUD operations for Registration model"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a superuser
        self.superuser = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create a regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            password='regular123'
        )
        
        # Create a user in the "register" group
        self.register_user = User.objects.create_user(
            username='register',
            password='register123'
        )
        
        # Create or get the "register" group
        register_group, created = Group.objects.get_or_create(name='register')
        
        # Add permissions: add, view, change (but NOT delete)
        add_permission = Permission.objects.get(codename='add_registration')
        view_permission = Permission.objects.get(codename='view_registration')
        change_permission = Permission.objects.get(codename='change_registration')
        
        register_group.permissions.add(add_permission, view_permission, change_permission)
        self.register_user.groups.add(register_group)
        
        # Create a test registration
        self.test_registration = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            region='URR',
            auxiliary_body='Khuddam',
            dob=date(1990, 1, 1)
        )
    
    def test_create_registration_as_register_user(self):
        """Test that register group user can create registration"""
        self.client.login(username='register', password='register123')
        
        url = reverse('tagnid:registration_create')
        response = self.client.post(url, {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'region': 'LRR',
            'auxiliary_body': 'Atfal',
            'dob': '2000-01-01'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Registration.objects.filter(first_name='Jane', last_name='Smith').exists())
    
    def test_create_registration_as_regular_user(self):
        """Test that regular user can create registration"""
        self.client.login(username='regular', password='regular123')
        
        url = reverse('tagnid:registration_create')
        response = self.client.post(url, {
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'region': 'CRR',
            'auxiliary_body': 'Ansar',
            'dob': '1985-05-15'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Registration.objects.filter(first_name='Bob', last_name='Johnson').exists())
    
    def test_view_registration_list_as_register_user(self):
        """Test that register group user can view registration list"""
        self.client.login(username='register', password='register123')
        
        url = reverse('tagnid:registration_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John')
        self.assertContains(response, 'Doe')
    
    def test_view_registration_detail_as_register_user(self):
        """Test that register group user can view registration detail"""
        self.client.login(username='register', password='register123')
        
        url = reverse('tagnid:registration_detail', args=[self.test_registration.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John')
        self.assertContains(response, 'Doe')
    
    def test_update_registration_as_register_user(self):
        """Test that register group user can update registration"""
        self.client.login(username='register', password='register123')
        
        url = reverse('tagnid:registration_update', args=[self.test_registration.pk])
        response = self.client.post(url, {
            'first_name': 'John',
            'last_name': 'Updated',
            'region': 'LRR',
            'auxiliary_body': 'Khuddam',
            'dob': '1990-01-01'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.test_registration.refresh_from_db()
        self.assertEqual(self.test_registration.last_name, 'Updated')
    
    def test_delete_registration_as_register_user_denied(self):
        """Test that register group user CANNOT delete registration"""
        self.client.login(username='register', password='register123')
        
        url = reverse('tagnid:registration_delete', args=[self.test_registration.pk])
        response = self.client.get(url)
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tagnid:registration_list'))
        
        # Try POST request
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tagnid:registration_list'))
        
        # Registration should still exist
        self.assertTrue(Registration.objects.filter(pk=self.test_registration.pk).exists())
    
    def test_delete_registration_as_regular_user_denied(self):
        """Test that regular user CANNOT delete registration"""
        self.client.login(username='regular', password='regular123')
        
        url = reverse('tagnid:registration_delete', args=[self.test_registration.pk])
        response = self.client.get(url)
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tagnid:registration_list'))
        
        # Try POST request
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tagnid:registration_list'))
        
        # Registration should still exist
        self.assertTrue(Registration.objects.filter(pk=self.test_registration.pk).exists())
    
    def test_delete_registration_as_superuser_allowed(self):
        """Test that superuser CAN delete registration"""
        self.client.login(username='admin', password='admin123')
        
        registration_id = self.test_registration.pk
        url = reverse('tagnid:registration_delete', args=[registration_id])
        
        # GET request should work
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # POST request should delete
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Registration should be deleted
        self.assertFalse(Registration.objects.filter(pk=registration_id).exists())
    
    def test_delete_registration_as_staff_allowed(self):
        """Test that staff user CAN delete registration"""
        staff_user = User.objects.create_user(
            username='staff',
            password='staff123',
            is_staff=True
        )
        self.client.login(username='staff', password='staff123')
        
        registration = Registration.objects.create(
            first_name='Test',
            last_name='Staff',
            region='URR',
            auxiliary_body='Khuddam'
        )
        
        url = reverse('tagnid:registration_delete', args=[registration.pk])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertFalse(Registration.objects.filter(pk=registration.pk).exists())


class VitalsCRUDTests(TestCase):
    """Test CRUD operations for Vitals model"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a superuser
        self.superuser = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create a user in the "register" group
        self.register_user = User.objects.create_user(
            username='register',
            password='register123'
        )
        
        # Create or get the "register" group
        register_group, created = Group.objects.get_or_create(name='register')
        
        # Add permissions: add, view, change (but NOT delete)
        add_permission = Permission.objects.get(codename='add_vitals')
        view_permission = Permission.objects.get(codename='view_vitals')
        change_permission = Permission.objects.get(codename='change_vitals')
        
        register_group.permissions.add(add_permission, view_permission, change_permission)
        self.register_user.groups.add(register_group)
        
        # Create a test registration
        self.test_registration = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            region='URR',
            auxiliary_body='Khuddam',
            dob=date(1990, 1, 1)
        )
        
        # Create test vitals
        self.test_vitals = Vitals.objects.create(
            registration=self.test_registration,
            blood_group='A+',
            height=175.5
        )
    
    def test_create_vitals_as_register_user(self):
        """Test that register group user can create vitals"""
        self.client.login(username='register', password='register123')
        
        registration = Registration.objects.create(
            first_name='Jane',
            last_name='Smith',
            region='LRR',
            auxiliary_body='Atfal'
        )
        
        url = reverse('tagnid:vitals_create', args=[registration.pk])
        response = self.client.post(url, {
            'blood_group': 'B+',
            'height': '180.0'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Vitals.objects.filter(registration=registration).exists())
    
    def test_view_vitals_as_register_user(self):
        """Test that register group user can view vitals"""
        self.client.login(username='register', password='register123')
        
        url = reverse('tagnid:registration_detail', args=[self.test_registration.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A+')
    
    def test_update_vitals_as_register_user(self):
        """Test that register group user can update vitals"""
        self.client.login(username='register', password='register123')
        
        url = reverse('tagnid:vitals_update', args=[self.test_registration.pk])
        response = self.client.post(url, {
            'blood_group': 'O+',
            'height': '185.0'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.test_vitals.refresh_from_db()
        self.assertEqual(self.test_vitals.blood_group, 'O+')
        self.assertEqual(float(self.test_vitals.height), 185.0)
    
    def test_delete_vitals_as_register_user_denied(self):
        """Test that register group user CANNOT delete vitals"""
        self.client.login(username='register', password='register123')
        
        url = reverse('tagnid:vitals_delete', args=[self.test_registration.pk])
        response = self.client.get(url)
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tagnid:registration_detail', args=[self.test_registration.pk]))
        
        # Try POST request
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tagnid:registration_detail', args=[self.test_registration.pk]))
        
        # Vitals should still exist
        self.assertTrue(Vitals.objects.filter(pk=self.test_vitals.pk).exists())
    
    def test_delete_vitals_as_superuser_allowed(self):
        """Test that superuser CAN delete vitals"""
        self.client.login(username='admin', password='admin123')
        
        vitals_id = self.test_vitals.pk
        url = reverse('tagnid:vitals_delete', args=[self.test_registration.pk])
        
        # GET request should work
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # POST request should delete
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Vitals should be deleted
        self.assertFalse(Vitals.objects.filter(pk=vitals_id).exists())


class AuthenticationTests(TestCase):
    """Test authentication and authorization"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
    
    def test_login_required_for_registration_list(self):
        """Test that registration list requires login"""
        url = reverse('tagnid:registration_list')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_login_required_for_dashboard(self):
        """Test that dashboard requires login"""
        url = reverse('tagnid:dashboard')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_login_success(self):
        """Test successful login"""
        url = reverse('tagnid:login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'test123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertIn('/dashboard/', response.url)
    
    def test_login_failure(self):
        """Test failed login"""
        url = reverse('tagnid:login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(response, 'Invalid username or password')


class ModelTests(TestCase):
    """Test model functionality"""
    
    def test_registration_str(self):
        """Test Registration __str__ method"""
        registration = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            region='URR',
            auxiliary_body='Khuddam'
        )
        self.assertEqual(str(registration), 'John Doe')
    
    def test_registration_age_calculation(self):
        """Test age property calculation"""
        from datetime import date, timedelta
        
        # Test with DOB
        dob = date.today() - timedelta(days=365*25)  # 25 years ago
        registration = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            region='URR',
            auxiliary_body='Khuddam',
            dob=dob
        )
        self.assertEqual(registration.age, 25)
        
        # Test without DOB
        registration_no_dob = Registration.objects.create(
            first_name='Jane',
            last_name='Smith',
            region='LRR',
            auxiliary_body='Atfal'
        )
        self.assertIsNone(registration_no_dob.age)
    
    def test_vitals_str(self):
        """Test Vitals __str__ method"""
        registration = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            region='URR',
            auxiliary_body='Khuddam'
        )
        vitals = Vitals.objects.create(
            registration=registration,
            blood_group='A+',
            height=175.5
        )
        self.assertEqual(str(vitals), 'Vitals for John Doe')
