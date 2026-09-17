from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Program, Registration, UserProfile, Vitals
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_program(name='Tajnid 2026', year=2026, is_active=True, is_archived=False):
    return Program.objects.create(name=name, year=year, is_active=is_active, is_archived=is_archived)


def make_user(username, password='pass1234', role='male_data_entry', program=None, is_superuser=False, is_staff=False):
    user = User.objects.create_user(
        username=username,
        password=password,
        is_superuser=is_superuser,
        is_staff=is_staff,
    )
    UserProfile.objects.create(user=user, role=role, default_program=program)
    return user


def make_registration(program=None, gender='Male', auxiliary_body='Khuddam', region='URR',
                      first_name='Test', last_name='User'):
    return Registration.objects.create(
        program=program,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        region=region,
        auxiliary_body=auxiliary_body,
    )


# ---------------------------------------------------------------------------
# Session / login helpers
# ---------------------------------------------------------------------------

class BaseTestCase(TestCase):
    """Base class that ensures session has active_program_id after login."""

    def login_with_program(self, user, program=None):
        """Log in and set active_program_id in session if program given."""
        self.client.login(username=user.username, password='pass1234')
        if program:
            session = self.client.session
            session['active_program_id'] = program.pk
            session.save()


# ---------------------------------------------------------------------------
# 1. Login / session tests
# ---------------------------------------------------------------------------

class LoginSessionTests(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.program = make_program()
        self.user = make_user('male_user', role='male_data_entry', program=self.program)

    def test_login_redirects_to_dashboard(self):
        url = reverse('tagnid:login')
        resp = self.client.post(url, {'username': 'male_user', 'password': 'pass1234'})
        self.assertRedirects(resp, reverse('tagnid:dashboard'))

    def test_login_sets_active_program_in_session(self):
        self.client.post(reverse('tagnid:login'), {'username': 'male_user', 'password': 'pass1234'})
        self.assertEqual(self.client.session.get('active_program_id'), self.program.pk)

    def test_login_wrong_password_stays_on_login(self):
        resp = self.client.post(reverse('tagnid:login'), {'username': 'male_user', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')

    def test_logout_clears_session(self):
        self.login_with_program(self.user, self.program)
        self.client.get(reverse('tagnid:logout'))
        self.assertNotIn('active_program_id', self.client.session)

    def test_unauthenticated_user_redirected_to_login(self):
        for name in ['dashboard', 'registration_list', 'registration_create']:
            resp = self.client.get(reverse(f'tagnid:{name}'))
            self.assertIn('/login/', resp.url, msg=f'Failed for {name}')


# ---------------------------------------------------------------------------
# 2. require_program gate tests
# ---------------------------------------------------------------------------

class RequireProgramTests(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.program = make_program()
        self.user_no_program = make_user('no_prog', role='male_data_entry', program=None)
        self.user_with_program = make_user('has_prog', role='male_data_entry', program=self.program)

    def test_user_without_program_redirected_to_no_program(self):
        self.client.login(username='no_prog', password='pass1234')
        resp = self.client.get(reverse('tagnid:dashboard'))
        self.assertRedirects(resp, reverse('tagnid:no_program'))

    def test_user_with_program_can_access_dashboard(self):
        self.login_with_program(self.user_with_program, self.program)
        resp = self.client.get(reverse('tagnid:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_user_without_program_can_still_access_dashboard(self):
        admin = make_user('adm', role='admin', program=None)
        self.client.login(username='adm', password='pass1234')
        resp = self.client.get(reverse('tagnid:dashboard'))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# 3. Registration creation tests
# ---------------------------------------------------------------------------

class RegistrationCreateTests(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.program = make_program()

    def _post_registration(self, data):
        return self.client.post(reverse('tagnid:registration_create'), data)

    # -- Male data entry role --

    def test_male_role_can_create_male_registration(self):
        user = make_user('male_user', role='male_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'Ahmad',
            'last_name': 'Bah',
            'gender': 'Male',
            'region': 'URR',
            'auxiliary_body': 'Khuddam',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        reg = Registration.objects.get(first_name='Ahmad', last_name='Bah')
        self.assertEqual(reg.gender, 'Male')
        self.assertEqual(reg.program, self.program)

    def test_male_role_cannot_create_female_auxiliary_body(self):
        user = make_user('male_user2', role='male_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'Ahmad',
            'last_name': 'Bah',
            'gender': 'Male',
            'region': 'URR',
            'auxiliary_body': 'Lajina',
        })
        # Form should be invalid – stay on page
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Registration.objects.filter(first_name='Ahmad', auxiliary_body='Lajina').exists())

    # -- Female data entry role --

    def test_female_role_can_create_female_registration(self):
        user = make_user('female_user', role='female_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'Fatou',
            'last_name': 'Jallow',
            'gender': 'Female',
            'region': 'LRR',
            'auxiliary_body': 'Lajina',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        reg = Registration.objects.get(first_name='Fatou', last_name='Jallow')
        self.assertEqual(reg.gender, 'Female')
        self.assertEqual(reg.program, self.program)

    def test_female_role_cannot_create_male_auxiliary_body(self):
        user = make_user('female_user2', role='female_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'Fatou',
            'last_name': 'Jallow',
            'gender': 'Female',
            'region': 'LRR',
            'auxiliary_body': 'Khuddam',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Registration.objects.filter(first_name='Fatou', auxiliary_body='Khuddam').exists())

    # -- Nasirat (female auxiliary body) --

    def test_nasirat_is_valid_for_female(self):
        user = make_user('female_user3', role='female_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'Aminata',
            'last_name': 'Ceesay',
            'gender': 'Female',
            'region': 'CRR',
            'auxiliary_body': 'Nasirat',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        self.assertTrue(Registration.objects.filter(first_name='Aminata', auxiliary_body='Nasirat').exists())

    def test_female_role_can_create_guest_registration(self):
        user = make_user('female_guest', role='female_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'GuestFem',
            'last_name': 'Test',
            'gender': 'Female',
            'region': 'CRR',
            'auxiliary_body': 'Guest',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        self.assertTrue(Registration.objects.filter(first_name='GuestFem', auxiliary_body='Guest').exists())

    def test_male_role_can_create_foreign_delegate_registration(self):
        user = make_user('male_fd', role='male_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'DelMale',
            'last_name': 'Test',
            'gender': 'Male',
            'region': 'URR',
            'auxiliary_body': 'Foreign_Delegate',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        self.assertTrue(Registration.objects.filter(first_name='DelMale', auxiliary_body='Foreign_Delegate').exists())

    def test_female_role_can_create_foreign_delegate_registration(self):
        user = make_user('female_fd', role='female_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'DelFem',
            'last_name': 'Test',
            'gender': 'Female',
            'region': 'LRR',
            'auxiliary_body': 'Foreign_Delegate',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        self.assertTrue(Registration.objects.filter(first_name='DelFem', auxiliary_body='Foreign_Delegate').exists())

    # -- Viewer role --

    def test_viewer_cannot_create_registration(self):
        user = make_user('viewer', role='viewer', program=self.program)
        self.login_with_program(user, self.program)
        resp = self._post_registration({
            'first_name': 'Should',
            'last_name': 'Fail',
            'gender': 'Male',
            'region': 'URR',
            'auxiliary_body': 'Atfal',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        self.assertFalse(Registration.objects.filter(first_name='Should').exists())

    # -- Admin --

    def test_admin_can_create_male_registration_with_program(self):
        admin = make_user('adm_create', role='admin', program=None)
        self.client.login(username='adm_create', password='pass1234')
        resp = self._post_registration({
            'program': self.program.pk,
            'first_name': 'Admin',
            'last_name': 'Created',
            'gender': 'Male',
            'region': 'URR',
            'auxiliary_body': 'Ansar',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        reg = Registration.objects.get(first_name='Admin', last_name='Created')
        self.assertEqual(reg.program, self.program)

    def test_admin_can_create_female_registration_with_program(self):
        admin = make_user('adm_female', role='admin', program=None)
        self.client.login(username='adm_female', password='pass1234')
        resp = self._post_registration({
            'program': self.program.pk,
            'first_name': 'Admin',
            'last_name': 'Female',
            'gender': 'Female',
            'region': 'LRR',
            'auxiliary_body': 'Nasirat',
        })
        self.assertRedirects(resp, reverse('tagnid:registration_list'))
        reg = Registration.objects.get(first_name='Admin', last_name='Female')
        self.assertEqual(reg.gender, 'Female')
        self.assertEqual(reg.program, self.program)

    def test_admin_form_requires_program_selection(self):
        admin = make_user('adm_noprog', role='admin', program=None)
        self.client.login(username='adm_noprog', password='pass1234')
        resp = self._post_registration({
            # no program submitted
            'first_name': 'No',
            'last_name': 'Program',
            'gender': 'Male',
            'region': 'URR',
            'auxiliary_body': 'Ansar',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Registration.objects.filter(first_name='No', last_name='Program').exists())

    # -- Registration auto-assigns program --

    def test_registration_auto_assigned_to_active_program(self):
        user = make_user('prog_user', role='male_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        self._post_registration({
            'first_name': 'Prog',
            'last_name': 'Test',
            'gender': 'Male',
            'region': 'FONI',
            'auxiliary_body': 'Atfal',
        })
        reg = Registration.objects.get(first_name='Prog', last_name='Test')
        self.assertEqual(reg.program, self.program)


# ---------------------------------------------------------------------------
# 4. Program scoping tests
# ---------------------------------------------------------------------------

class ProgramScopingTests(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.prog_a = make_program('Program A', 2025)
        self.prog_b = make_program('Program B', 2026)
        self.user_a = make_user('user_a', role='male_data_entry', program=self.prog_a)
        self.reg_a = make_registration(program=self.prog_a)
        self.reg_b = make_registration(program=self.prog_b, first_name='Other', last_name='Person')

    def test_user_only_sees_their_program_registrations(self):
        self.login_with_program(self.user_a, self.prog_a)
        resp = self.client.get(reverse('tagnid:registration_list'))
        self.assertContains(resp, self.reg_a.first_name)
        self.assertNotContains(resp, self.reg_b.first_name)

    def test_user_cannot_view_other_program_registration_detail(self):
        self.login_with_program(self.user_a, self.prog_a)
        resp = self.client.get(reverse('tagnid:registration_detail', args=[self.reg_b.pk]))
        self.assertRedirects(resp, reverse('tagnid:registration_list'))

    def test_admin_sees_all_programs(self):
        admin = make_user('admin_scope', role='admin', program=None)
        self.client.login(username='admin_scope', password='pass1234')
        resp = self.client.get(reverse('tagnid:registration_list'))
        self.assertContains(resp, self.reg_a.first_name)
        self.assertContains(resp, self.reg_b.first_name)


# ---------------------------------------------------------------------------
# 5. Gender scoping tests
# ---------------------------------------------------------------------------

class GenderScopingTests(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.program = make_program()
        self.male_reg = make_registration(program=self.program, gender='Male', first_name='Lamin')
        self.female_reg = make_registration(program=self.program, gender='Female',
                                            auxiliary_body='Lajina', first_name='Fatou')

    def test_male_role_sees_only_male_records(self):
        user = make_user('male_scope', role='male_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self.client.get(reverse('tagnid:registration_list'))
        self.assertContains(resp, 'Lamin')
        self.assertNotContains(resp, 'Fatou')

    def test_female_role_sees_only_female_records(self):
        user = make_user('female_scope', role='female_data_entry', program=self.program)
        self.login_with_program(user, self.program)
        resp = self.client.get(reverse('tagnid:registration_list'))
        self.assertContains(resp, 'Fatou')
        self.assertNotContains(resp, 'Lamin')

    def test_program_manager_sees_both_genders(self):
        user = make_user('pm', role='program_manager', program=self.program)
        self.login_with_program(user, self.program)
        resp = self.client.get(reverse('tagnid:registration_list'))
        self.assertContains(resp, 'Lamin')
        self.assertContains(resp, 'Fatou')


# ---------------------------------------------------------------------------
# 6. Unique code generation tests
# ---------------------------------------------------------------------------

class UniqueCodeTests(TestCase):

    def test_unique_code_uses_program_year(self):
        program = make_program(year=2026)
        reg = make_registration(program=program)
        # New format: YEARSEQ, e.g. "2026001" — no dash
        self.assertTrue(reg.unique_code.startswith('2026'))
        self.assertNotIn('-', reg.unique_code)

    def test_unique_codes_are_sequential(self):
        program = make_program(year=2026)
        reg1 = make_registration(program=program, first_name='A')
        reg2 = make_registration(program=program, first_name='B')
        # Strip the 4-char year prefix, rest is zero-padded seq
        num1 = int(reg1.unique_code[4:])
        num2 = int(reg2.unique_code[4:])
        self.assertEqual(num2, num1 + 1)

    def test_unique_code_different_programs_same_year_start_at_one(self):
        """Each programme resets its own sequence – both can share the same code value."""
        prog1 = make_program('P1', 2026)
        prog2 = make_program('P2', 2026)
        reg1 = make_registration(program=prog1)
        reg2 = make_registration(program=prog2)
        # Both programmes start at 001 independently
        self.assertEqual(reg1.unique_code, '2026001')
        self.assertEqual(reg2.unique_code, '2026001')
        # But they are in different programmes so the unique_together constraint is satisfied
        self.assertNotEqual(reg1.program, reg2.program)

    def test_unique_code_format_three_digit_seq(self):
        program = make_program(year=2026)
        reg = make_registration(program=program)
        # Format: YEAR (4 chars) + SEQ (3 chars, zero-padded) = 7 chars
        self.assertEqual(len(reg.unique_code), 7)
        self.assertEqual(reg.unique_code, '2026001')


# ---------------------------------------------------------------------------
# 7. Settings – admin-only access tests
# ---------------------------------------------------------------------------

class SettingsAccessTests(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.program = make_program()
        self.admin = make_user('admin_s', role='admin', program=None)
        self.regular = make_user('reg_s', role='male_data_entry', program=self.program)

    def test_admin_can_access_settings_users(self):
        self.client.login(username='admin_s', password='pass1234')
        resp = self.client.get(reverse('tagnid:settings_users'))
        self.assertEqual(resp.status_code, 200)

    def test_non_admin_cannot_access_settings_users(self):
        self.login_with_program(self.regular, self.program)
        resp = self.client.get(reverse('tagnid:settings_users'))
        self.assertRedirects(resp, reverse('tagnid:dashboard'))

    def test_admin_can_access_settings_programs(self):
        self.client.login(username='admin_s', password='pass1234')
        resp = self.client.get(reverse('tagnid:settings_programs'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_create_user(self):
        self.client.login(username='admin_s', password='pass1234')
        resp = self.client.post(reverse('tagnid:settings_user_create'), {
            'username': 'newuser',
            'password': 'Str0ngPass!',
            'confirm_password': 'Str0ngPass!',
            'role': 'male_data_entry',
            'default_program': '',
        })
        self.assertRedirects(resp, reverse('tagnid:settings_users'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_admin_can_create_program(self):
        self.client.login(username='admin_s', password='pass1234')
        resp = self.client.post(reverse('tagnid:settings_program_create'), {
            'name': 'New Program',
            'year': 2027,
            'is_active': True,
            'is_archived': False,
        })
        self.assertRedirects(resp, reverse('tagnid:settings_programs'))
        self.assertTrue(Program.objects.filter(name='New Program', year=2027).exists())


# ---------------------------------------------------------------------------
# 8. Archive tests
# ---------------------------------------------------------------------------

class ArchiveTests(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.active_prog = make_program('Active', 2026, is_active=True, is_archived=False)
        self.archived_prog = make_program('Archived', 2025, is_active=False, is_archived=True)
        self.admin = make_user('arch_admin', role='admin', program=None)

    def test_archived_program_not_shown_to_regular_users(self):
        user = make_user('arch_user', role='male_data_entry', program=self.active_prog)
        self.login_with_program(user, self.active_prog)
        resp = self.client.get(reverse('tagnid:programs_overview'))
        self.assertNotContains(resp, 'Archived')

    def test_admin_can_see_archived_with_toggle(self):
        self.client.login(username='arch_admin', password='pass1234')
        resp = self.client.get(reverse('tagnid:programs_overview') + '?archived=1')
        self.assertContains(resp, 'Archived')


# ---------------------------------------------------------------------------
# 9. Model tests
# ---------------------------------------------------------------------------

class ModelTests(TestCase):

    def test_program_str(self):
        p = make_program('Tajnid', 2026)
        self.assertEqual(str(p), 'Tajnid (2026)')

    def test_registration_str(self):
        reg = make_registration(first_name='Lamin', last_name='Touray')
        self.assertEqual(str(reg), 'Lamin Touray')

    def test_registration_age_calculation(self):
        from datetime import timedelta
        dob = date.today().replace(year=date.today().year - 25)
        reg = Registration.objects.create(
            first_name='A', last_name='B', region='URR',
            gender='Male', auxiliary_body='Khuddam', dob=dob
        )
        self.assertEqual(reg.age, 25)

    def test_registration_age_none_without_dob(self):
        reg = make_registration()
        self.assertIsNone(reg.age)

    def test_userprofile_gender_scope_male(self):
        user = make_user('gsc_male', role='male_data_entry')
        self.assertEqual(user.profile.gender_scope, 'Male')

    def test_userprofile_gender_scope_female(self):
        user = make_user('gsc_female', role='female_data_entry')
        self.assertEqual(user.profile.gender_scope, 'Female')

    def test_userprofile_gender_scope_none_for_admin(self):
        user = make_user('gsc_admin', role='admin')
        self.assertIsNone(user.profile.gender_scope)

    def test_userprofile_is_read_only_for_viewer(self):
        user = make_user('viewer_ro', role='viewer')
        self.assertTrue(user.profile.is_read_only)

    def test_userprofile_not_read_only_for_data_entry(self):
        user = make_user('entry_rw', role='male_data_entry')
        self.assertFalse(user.profile.is_read_only)

    def test_vitals_str(self):
        reg = make_registration(first_name='Omar', last_name='Jobe')
        vitals = Vitals.objects.create(registration=reg, blood_group='O+', height=175)
        self.assertEqual(str(vitals), 'Vitals for Omar Jobe')
