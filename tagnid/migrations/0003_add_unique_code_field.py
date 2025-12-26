# Generated migration to add unique_code field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagnid', '0002_rename_majilis_to_auxiliary_body'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='unique_code',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='Unique Registration Code'),
        ),
    ]

