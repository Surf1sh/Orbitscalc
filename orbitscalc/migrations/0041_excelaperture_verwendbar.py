# Generated by Django 2.2.6 on 2020-03-29 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0040_auto_20200329_2046'),
    ]

    operations = [
        migrations.AddField(
            model_name='excelaperture',
            name='verwendbar',
            field=models.BooleanField(null=True),
        ),
    ]