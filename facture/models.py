from django.db import models
from clients.models import Client
from accounts.models import User
from django.utils import timezone

ETAT_FACTURE_CHOICES = [
    ('Impayée', 'Impayée'),
    ('Payé', 'Payé'),
    ('En cours', 'En cours'),
    ('Brouillon', 'Brouillon'),
    ('Annulé', 'Annulé'),
]
TYPES_FACTURE_CHOICES = [
    ('Facture', 'Facture'),
    ('Devis', 'Devis'),
]

REGLEMENT_CHOICES = [
    ('A réception', 'A réception'),
    ('30 jours', '30 jours'),
    ('30 jours fin de mois', '30 jours fin de mois'),
    ('60 jours', '60 jours'),
    ('60 jours fin de mois', '60 jours fin de mois'),
    ('A commande', 'A commande'),
    ('A livraison', 'A livraison'),
    ('50/50', '50/50'),
    ('10 jours', '10 jours'),
    ('10 jours fin de mois', '10 jours fin de mois'),
    ('14 jours', '14 jours'),
    ('14 jours fin de mois', '14 jours fin de mois'),
]




class Facture(models.Model):
    ref = models.CharField(max_length=200, verbose_name="Réf. du facture", null=True)
    intitule = models.CharField(max_length=200, verbose_name="Intitulé du facture")
    reglement = models.CharField(max_length=200, choices=REGLEMENT_CHOICES, verbose_name="Règlement")
    condition = models.CharField(max_length=200, verbose_name="Condition")
    # etat = models.CharField(max_length=200, verbose_name="Etat")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Client", null=True, blank=True)
    date_facture = models.DateField(verbose_name="Date du facture", default=timezone.now)
    etat_facture = models.CharField(max_length=10, null=False, default='Non payé',choices=ETAT_FACTURE_CHOICES)
    # service = models.ManyToManyField('Service', verbose_name="Services", blank=True)
    services = models.JSONField(verbose_name="Services supplémentaires", blank=True, default=None)
    type = models.CharField(max_length=10, choices=TYPES_FACTURE_CHOICES, default="Facture", null=True, blank=True)
    with_tva = models.BooleanField(default=False, verbose_name="TVA", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="Facture créer par ")
    created_at = models.DateTimeField(null=True, default=timezone.now)
    updated_at = models.DateTimeField(null=True, default=timezone.now)

    def __str__(self):
        return f"Facture {self.intitule} du {self.etat_facture}"

class Service(models.Model):
    nom_service = models.CharField(max_length=200, verbose_name="Nom de l'article")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")
    description = models.TextField(max_length=1000, verbose_name="Description", blank=True, default=None)

    def __str__(self):
        return f"{self.nom_service} - Prix unitaire: {self.prix_unitaire}"

