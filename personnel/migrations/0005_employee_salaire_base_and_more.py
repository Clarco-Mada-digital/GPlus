# Generated by Django 5.1.1 on 2024-10-29 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personnel', '0004_rename_indemnites_paie_indemnite_communication_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='salaire_base',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='paie',
            name='cotisations_patronales',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='paie',
            name='cotisations_salariales',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='paie',
            name='indemnite_communication',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='paie',
            name='indemnite_stage',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='paie',
            name='indemnite_transport',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='paie',
            name='indice_anciennete',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='paie',
            name='net_a_payer',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='paie',
            name='net_imposable',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='paie',
            name='salaire_base',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='paie',
            name='statut',
            field=models.CharField(choices=[('P', 'Payé'), ('E', 'En attente')], max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='prime',
            name='montant',
            field=models.IntegerField(default=0),
        ),
    ]
