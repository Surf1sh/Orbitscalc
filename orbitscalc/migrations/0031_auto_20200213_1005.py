# Generated by Django 2.2.6 on 2020-02-13 09:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0030_auto_20200213_0938'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ge',
            old_name='erip_max_dbw',
            new_name='eirp_max_dbw',
        ),
        migrations.RenameField(
            model_name='ge',
            old_name='erip_min_dbw',
            new_name='eirp_min_dbw',
        ),
    ]
