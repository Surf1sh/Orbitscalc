# Generated by Django 2.2.6 on 2020-03-30 12:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0045_auto_20200330_1455'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groundstationaperture',
            name='groundStation',
        ),
    ]
