"""
Management command to backfill unique codes for existing registrations.
"""
from django.core.management.base import BaseCommand
from tagnid.models import Registration
from tagnid.service import backfill_unique_codes


class Command(BaseCommand):
    help = 'Backfill unique codes for registrations that don\'t have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Count registrations without unique codes
        missing_count = Registration.objects.filter(unique_code__isnull=True).count()
        
        if missing_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All registrations already have unique codes.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {missing_count} registrations without unique codes.')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: Would backfill unique codes for these registrations.')
            )
            # Show sample of what would be updated
            sample = Registration.objects.filter(unique_code__isnull=True)[:5]
            for reg in sample:
                year = reg.created_at.year if reg.created_at else 2025
                proposed_code = f"{year}-{reg.pk:04d}"
                self.stdout.write(
                    f"  - {reg.first_name} {reg.last_name} (ID: {reg.pk}) -> {proposed_code}"
                )
            if missing_count > 5:
                self.stdout.write(f"  ... and {missing_count - 5} more")
            return
        
        # Actually backfill
        try:
            updated_count = backfill_unique_codes()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully backfilled unique codes for {updated_count} registrations.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error backfilling unique codes: {str(e)}')
            )

