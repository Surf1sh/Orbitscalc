# Generated by Django 2.2.6 on 2020-02-03 13:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0011_sana_aperture_links_is_forward_link'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sana_aperture_links',
            name='is_forward_link',
        ),
    ]
