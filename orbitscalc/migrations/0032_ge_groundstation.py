# Generated by Django 2.2.6 on 2020-02-13 09:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0031_auto_20200213_1005'),
    ]

    operations = [
        migrations.AddField(
            model_name='ge',
            name='groundstation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='orbitscalc.GroundStation'),
        ),
    ]
