from django.db import models
from clients.models import Client

class Facture(models.Model):
    intitule = models.CharField(max_length=200, verbose_name="Intitulé du facture")
    reglement = models.CharField(max_length=200, verbose_name="Règlement")
    condition = models.CharField(max_length=200, verbose_name="Condition")
    etat = models.CharField(max_length=200, verbose_name="Etat")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Client", null=True, blank=True)
    service = models.ManyToManyField('Service', verbose_name="Services", blank=True)
    services_supplementaires = models.JSONField(verbose_name="Services supplémentaires")

    def __str__(self):
        return f"Facture {self.intitule} du {self.etat}"

class Service(models.Model):
    nom_service = models.CharField(max_length=200, verbose_name="Nom de l'article")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")
    description = models.TextField(max_length=1000, verbose_name="Description", blank=True, default=None)

    def __str__(self):
        return f"{self.nom_service} - Prix unitaire: {self.prix_unitaire}"

