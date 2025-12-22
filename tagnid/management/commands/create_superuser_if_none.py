"""
Management command to create a superuser if none exists.
Safe to run multiple times - won't create duplicate superusers.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a superuser if one does not already exist'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'),
            help='Username for the superuser',
        )
        parser.add_argument(
            '--email',
            type=str,
            default=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
            help='Email for the superuser',
        )
        parser.add_argument(
            '--password',
            type=str,
            default=os.environ.get('DJANGO_SUPERUSER_PASSWORD'),
            help='Password for the superuser (required if not in env)',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Run in non-interactive mode (requires password in env or --password)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        noinput = options['noinput']

        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser already exists. Skipping creation.')
            )
            return

        # Check if user with this username already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'User with username "{username}" already exists.')
            )
            return

        # If noinput mode, password must be provided
        if noinput and not password:
            self.stdout.write(
                self.style.ERROR('Error: --password is required when using --noinput')
            )
            return

        # If not noinput and no password, prompt for it
        if not noinput and not password:
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(
                    self.style.ERROR('Error: Passwords do not match.')
                )
                return

        # Create superuser
        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{username}"')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )

