# Generated by Django 5.1.1 on 2024-10-24 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='groupe_sanguin',
            field=models.CharField(max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='maladie',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
