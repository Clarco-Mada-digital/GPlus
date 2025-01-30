# Generated by Django 5.1.1 on 2025-01-29 13:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0015_alter_historicaloperationentrer_benef_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fournisseur',
            name='contact',
            field=models.CharField(blank=True, default='', max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='fournisseur',
            name='name',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='historicalfournisseur',
            name='contact',
            field=models.CharField(blank=True, default='', max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='historicalfournisseur',
            name='name',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='historicaloperationentrer',
            name='benef',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='historicaloperationentrer',
            name='client',
            field=models.CharField(blank=True, default='', max_length=75),
        ),
        migrations.AlterField(
            model_name='operationentrer',
            name='benef',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='operationentrer',
            name='client',
            field=models.CharField(blank=True, default='', max_length=75),
        ),
        migrations.AlterField(
            model_name='operationsortir',
            name='beneficiaire',
            field=models.ForeignKey(blank=True, default='', on_delete=django.db.models.deletion.PROTECT, to='caisse.beneficiaire'),
        ),
        migrations.AlterField(
            model_name='operationsortir',
            name='fournisseur',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, to='caisse.fournisseur'),
        ),
    ]
