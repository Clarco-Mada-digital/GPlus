# Generated by Django 5.1.1 on 2024-11-01 05:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0006_historicalbeneficiaire_historicalcaisse_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historicaloperationsortir',
            old_name='quantité',
            new_name='quantite',
        ),
        migrations.RenameField(
            model_name='operationsortir',
            old_name='quantité',
            new_name='quantite',
        ),
    ]
