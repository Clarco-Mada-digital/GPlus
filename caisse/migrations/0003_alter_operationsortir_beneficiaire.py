# Generated by Django 5.1.1 on 2024-10-21 12:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0002_categorie_type_alter_categorie_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operationsortir',
            name='beneficiaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='caisse.beneficiaire'),
        ),
    ]