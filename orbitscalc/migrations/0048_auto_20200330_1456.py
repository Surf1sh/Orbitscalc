# Generated by Django 2.2.6 on 2020-03-30 12:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0047_remove_groundstationaperturelink_groundstation'),
    ]

    operations = [
        migrations.DeleteModel('GroundStationApertureLink'),
    ]