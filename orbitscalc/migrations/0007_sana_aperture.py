# Generated by Django 2.2.6 on 2020-02-03 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0006_auto_20200129_1621'),
    ]

    operations = [
        migrations.CreateModel(
            name='SANA_aperture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Status', models.CharField(max_length=200, null=True)),
                ('OID', models.CharField(max_length=200, null=True)),
                ('Abbreviation', models.CharField(max_length=200, null=True)),
                ('Forward_Links', models.CharField(max_length=200, null=True)),
                ('Return_Links', models.CharField(max_length=200, null=True)),
                ('Location_Type', models.CharField(max_length=200, null=True)),
                ('Planetary_Body', models.CharField(max_length=200, null=True)),
                ('Country', models.CharField(max_length=200, null=True)),
                ('City', models.CharField(max_length=200, null=True)),
                ('State_Region', models.CharField(max_length=200, null=True)),
                ('Latitude', models.CharField(max_length=200, null=True)),
                ('Longitude', models.CharField(max_length=200, null=True)),
                ('Elevation', models.CharField(max_length=200, null=True)),
                ('Operating_Domain', models.CharField(max_length=200, null=True)),
                ('Trajectory', models.CharField(max_length=200, null=True)),
                ('Diameter', models.CharField(max_length=200, null=True)),
                ('Aperture_Type', models.CharField(max_length=200, null=True)),
                ('Pointing_Contraints', models.CharField(max_length=200, null=True)),
                ('Available_Services', models.CharField(max_length=200, null=True)),
                ('Mission_Type', models.CharField(max_length=200, null=True)),
                ('Notes', models.CharField(max_length=200, null=True)),
                ('References', models.CharField(max_length=200, null=True)),
                ('created_by', models.CharField(max_length=200, null=True)),
                ('Creation_Date', models.CharField(max_length=200, null=True)),
                ('updated_by', models.CharField(max_length=200, null=True)),
                ('Update_Date', models.CharField(max_length=200, null=True)),
            ],
        ),
    ]
