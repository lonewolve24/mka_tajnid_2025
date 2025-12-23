# Generated migration to rename majilis to auxiliary_body

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tagnid', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='registration',
            old_name='majilis',
            new_name='auxiliary_body',
        ),
    ]

