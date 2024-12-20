# Generated by Django 5.1.1 on 2024-10-21 12:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0004_alter_operationsortir_beneficiaire'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beneficiaire',
            name='name',
            field=models.CharField(blank=True, help_text="Nom du bénéficiaire (facultatif, utilisé si personnel n'est pas spécifié)", max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='beneficiaire',
            name='personnel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='caisse.personnel'),
        ),
    ]
