# Generated by Django 3.0.8 on 2020-08-30 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0058_auto_20200830_1803'),
    ]

    operations = [
        migrations.AddField(
            model_name='aperture',
            name='durchmesser',
            field=models.DecimalField(decimal_places=3, max_digits=6, null=True),
        ),
    ]