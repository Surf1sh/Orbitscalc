# Generated by Django 2.2.6 on 2020-02-12 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0026_auto_20200212_1428'),
    ]

    operations = [
        migrations.AddField(
            model_name='ge',
            name='diameter_m',
            field=models.DecimalField(decimal_places=3, max_digits=7, null=True),
        ),
    ]