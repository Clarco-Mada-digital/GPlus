# Generated by Django 5.1.1 on 2024-10-29 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0005_employee_salaire_base_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='paie',
            name='salaire_brut',
            field=models.IntegerField(default=0),
        ),
    ]
