import re
from django.forms import ValidationError
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
CONDITION_REGLEMENT_CHOICES = [
    ('Carte bancaire', 'Carte bancaire'),
    ('Chèque', 'Chèque'),
    ('Espèce', 'Espèce'),
    ('Ordre de prélèvement', 'Ordre de prélèvement'),
    ('Virement bancaire', 'Virement bancaire'),
]

class Facture(models.Model):
    ref = models.CharField(max_length=200, verbose_name="Réf. du facture", null=True)
    intitule = models.CharField(max_length=200, verbose_name="Intitulé du facture")
    reglement = models.CharField(max_length=200, blank=True, choices=REGLEMENT_CHOICES, verbose_name="Règlement")
    condition = models.DateField(blank=True, verbose_name="Condition")
    condition_reglement = models.CharField(max_length=200, choices=CONDITION_REGLEMENT_CHOICES, null=True, default=None, blank=True, verbose_name="Condition de règlement")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Client", null=True, blank=True, db_constraint=False)
    date_facture = models.DateField(verbose_name="Date du facture", default=timezone.now, blank=True)
    etat_facture = models.CharField(max_length=10, null=False, blank=True, default='Brouillon',choices=ETAT_FACTURE_CHOICES)
    # service = models.ManyToManyField('Service', verbose_name="Services", blank=True)
    services = models.JSONField(verbose_name="Services supplémentaires", blank=True, default=None)
    type = models.CharField(max_length=10, choices=TYPES_FACTURE_CHOICES, default="Facture", null=True, blank=True)
    with_tva = models.BooleanField(default=False, verbose_name="TVA", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="Facture créer par ")
    created_at = models.DateTimeField(null=True, default=timezone.now)
    updated_at = models.DateTimeField(null=True, default=timezone.now)

    def __str__(self):
        return f"Facture {self.intitule} du {self.etat_facture}"
    
    class Meta:
        db_table = 'facture_facture'

class Service(models.Model):
    nom_service = models.CharField(max_length=200, verbose_name="Nom de l'article")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")
    description = models.TextField(max_length=1000, verbose_name="Description", blank=True, default=None)

    def __str__(self):
        return f"{self.nom_service} - Prix unitaire: {self.prix_unitaire}"

class Entreprise(models.Model):    
    logo = models.ImageField(upload_to='photos/', blank=True)
    nom = models.CharField(max_length=200, verbose_name="Nom d'entreprise")
    tel = models.CharField(max_length=15, default="+261", verbose_name="Téléphone")
    email = models.EmailField()
    adresse = models.CharField(max_length=100, null=True, verbose_name="Adresse")
    region = models.CharField(max_length=100, null=True, verbose_name="Région")
    code_postal = models.CharField(max_length=10, null=True, blank=True, verbose_name="Code postal")
    nif = models.CharField(max_length=100, blank=True, verbose_name="NIF")
    stat = models.CharField(max_length=100, blank=True, verbose_name="STAT")
    taux_tva = models.DecimalField(max_digits=100, decimal_places=2,verbose_name="Taux TVA")

    def clean(self):

    # Validation du numéro de téléphone
        if not re.match(r'^\+?[0-9]{10,15}$', self.tel):
            raise ValidationError('Le numéro de téléphone doit comporter entre 10 et 15 chiffres.')

    def __str__(self):
        return f"Entreprise : {self.nom}"

    class Meta:
        managed = True
        verbose_name = 'Entreprise'
        verbose_name_plural = 'Entreprises'