# Generated by Django 3.0.8 on 2020-08-30 16:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0059_aperture_durchmesser'),
    ]

    operations = [
        migrations.RenameField(
            model_name='Aperture',
            old_name='eirp_max_dbw',
            new_name='eirp_dbw'
        ),
        migrations.RenameField(
            model_name='Aperture',
            old_name='gt_max_dbw_k',
            new_name='gt_dbw_k'
        ),
    ]
