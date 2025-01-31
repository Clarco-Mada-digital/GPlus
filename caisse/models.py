from django.db import models
import re
from django.forms import ValidationError
from django.utils import timezone
from django.db import models
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from django.conf import settings
from simple_history.models import HistoricalRecords

# Create your models here.

# Modèle Category - Catégorie des transactions
class Categorie(models.Model):
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='entree')
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def to_json(self):
        return json.dumps({
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type
        }, cls=DjangoJSONEncoder)

# Modèle Personnel
class Personnel(models.Model):
    # Sexe
    HOMME = 'Homme'
    FEMME = 'Femme'
    SEXE_CHOICES = [
        (HOMME, 'Homme'),
        (FEMME, 'Femme'),
    ]

    # Type d'employé
    S = 'Salarié'
    B = 'Bénévole'
    F = 'Freelance'
    ST = 'Stagiaire'
    TYPE_CHOICES = [
        (S, 'Salarié'),
        (B, 'Bénévole'),
        (F, 'Freelance'),
        (ST, 'Stagiaire'),
    ]
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    tel = models.CharField(max_length=15, default="+261")
    email = models.EmailField()
    date_embauche = models.DateTimeField(default=timezone.now)
    sexe = models.CharField(max_length=6, choices=SEXE_CHOICES, default='Homme')
    date_naissance = models.DateField()
    photo = models.ImageField(upload_to='photos/', blank=True , default="photos/pdp_defaut.png")
    adresse = models.CharField(max_length=100, null=True)
    type_personnel = models.CharField(max_length=10, choices=TYPE_CHOICES, null=False, default='Salarié')
    history = HistoricalRecords()

    def clean(self):

    # Validation du numéro de téléphone
        if not re.match(r'^\+?[0-9]{10,15}$', self.tel):
            raise ValidationError('Le numéro de téléphone doit comporter entre 10 et 15 chiffres.')
    
    # Validation de la date de naissance (vérifie si l'âge est raisonnable)
        if self.date_naissance >= timezone.now().date():
            raise ValidationError('La date de naissance doit être dans le passé.')

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def to_json(self):
        return json.dumps({
            'id': self.id,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'tel': self.tel,
            'email': self.email,
            'sexe': self.sexe,
            'date_naissance': self.date_naissance.isoformat(),
            'photo': self.photo.url if self.photo else None,
            'adresse': self.adresse,
            'type_personnel': self.type_personnel
        }, cls=DjangoJSONEncoder)

# Modèle Fournisseur
class Fournisseur(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True, default="")
    contact = models.CharField(max_length=15,  null=True, blank=True, default="")  # Contact comme numéro de téléphone
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def to_json(self):
        return json.dumps({
            'id': self.id,
            'name': self.name,
            'contact': self.contact
        }, cls=DjangoJSONEncoder)

# Modèle Beneficiaire
class Beneficiaire(models.Model):
    personnel = models.ForeignKey(Personnel, on_delete=models.PROTECT, blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True, help_text="Nom du bénéficiaire (facultatif, utilisé si personnel n'est pas spécifié)")
    history = HistoricalRecords()

    def __str__(self):
        if self.personnel:
            return str(self.personnel)
        elif self.name:
            return self.name
        else:
            return "Beneficiaire sans nom ni personnel"

    def clean(self):
        if not self.personnel and not self.name:
            raise ValidationError("Au moins l'un des champs 'personnel' ou 'name' doit être rempli.")

# Modèle pour les opérations (entrées et sorties)
# Modèle pour les entrées
class OperationEntrer(models.Model):
    
    description = models.CharField(max_length=75, null=False)  # Nom de l'opération
    montant = models.DecimalField(max_digits=10, decimal_places=0, default=0)  # Montant
    date = models.DateField(auto_now_add=True)  # Date de l'ajout dans l'application
    date_transaction = models.DateField(default=timezone.now) # Date de l'opération
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, null=False, default="")  # Clé étrangère vers Categorie
    beneficiaire = models.ForeignKey(Beneficiaire, default="", on_delete=models.PROTECT, blank=True) #beneficiaire
    client = models.CharField(max_length=75, default="", blank=True) #client
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.description} - {self.montant} - {self.benef} - {self.client}"  

# Modèle pour les sorties
class OperationSortir(models.Model):
    
    description = models.CharField(max_length=255)  # Nom de l'opération
    montant = models.DecimalField(max_digits=10, decimal_places=0, default=0)  # Montant
    date = models.DateField(auto_now_add=True)  # Date de l'ajout dans l'application
    date_de_sortie = models.DateField(default=timezone.now) #Date du moment où une sortie de la caisse s'est fait 
    quantite = models.DecimalField(max_digits=10, decimal_places=0, default=1) # Quantité de la chose acheté
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, default="", null=False)  # Clé étrangère vers Categorie
    beneficiaire = models.ForeignKey(Beneficiaire, default="", on_delete=models.PROTECT, blank=True) #clé étrangère vers Personnel et Bénéficiaire
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, blank=True) #clé étrangère vers Fournisseur
    history = HistoricalRecords() # Stocker l'historique par Django simple history

    # Affichage des données stockées 
    def __str__(self):
        return f"{self.description} - {self.montant} - {self.beneficiaire} - {self.categorie} - {self.fournisseur}"

# Modèle Caisse
class Caisse(models.Model):
    montant = models.DecimalField(max_digits=10, decimal_places=2)  # Montant en décimal pour plus de précision
    date_creation = models.DateField(auto_now_add=True)  # Date de création automatique
    history = HistoricalRecords()

    def __str__(self):
        return f"Caisse {self.id} - Montant: {self.montant}"
    
class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)