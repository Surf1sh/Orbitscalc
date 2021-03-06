# Generated by Django 2.2.6 on 2020-02-12 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0025_auto_20200212_1427'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ge',
            old_name='uplink_frequency_max',
            new_name='downlink_frequency_max_MHz',
        ),
        migrations.RenameField(
            model_name='ge',
            old_name='uplink_frequency_min',
            new_name='downlink_frequency_min_MHz',
        ),
        migrations.AddField(
            model_name='ge',
            name='uplink_frequency_max_MHz',
            field=models.DecimalField(decimal_places=3, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='ge',
            name='uplink_frequency_min_MHz',
            field=models.DecimalField(decimal_places=3, max_digits=10, null=True),
        ),
    ]
