# Generated by Django 5.1.1 on 2024-10-29 18:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0007_remove_paie_cotisations_patronales_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prime',
            name='paie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primes', to='personnel.paie'),
        ),
    ]
