# Generated by Django 2.2.6 on 2020-02-13 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orbitscalc', '0029_auto_20200213_0923'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ge',
            old_name='erip_max_dBW_k',
            new_name='erip_max_dbw',
        ),
        migrations.RenameField(
            model_name='ge',
            old_name='erip_min_dBW_k',
            new_name='erip_min_dbw',
        ),
        migrations.AddField(
            model_name='ge',
            name='gt_max_dbw_k',
            field=models.DecimalField(decimal_places=3, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='ge',
            name='gt_min_dbw_k',
            field=models.DecimalField(decimal_places=3, max_digits=10, null=True),
        ),
    ]
