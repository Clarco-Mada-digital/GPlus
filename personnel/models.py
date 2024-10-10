from django.db import models
from django.utils import timezone
from datetime import date
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
import re

class Departement(models.Model): #Model Departement
    nom = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.nom}"

class Poste(models.Model): #Model Poste
    nom = models.CharField(max_length=100)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.departement} {self.nom}"

class Competence(models.Model): #Model Compétence
    nom = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.nom}"

class Employee(models.Model): #Model employée
    SEXE_CHOICES = [
        ('Masculin', 'Masculin'),
        ('Féminin', 'Féminin'),
    ]



    STATUT_CHOICES = [
        ('Célibataire', 'Célibataire'),
        ('Marié(e)', 'Marié(e)'),
        ('Divorcé(e)', 'Divorcé(e)'),
    ]

    TYPE_CHOICES = [
        ('salarie', 'Salarié'),
        ('benevole', 'Bénévole'),
        ('freelance', 'Freelance'),
        ('stagiaire', 'Stagiaire'),
        ('direction', 'Direction'),
        ('assit_direction', 'Assistant Direction'),

    ]
    STATUTCON_CHOICES = [
        ('C', 'En congée'),
        ('T', 'Au travail'),
    ]
    CONTRAT_CHOICES = [
        ('CDI', 'CDI'),
        ('CDD', 'CDD'),
        ('Aucun', 'Aucun')

    ]

    ROLE_CHOICES = [
        ('stagiaire', 'Stagiaire'),
        ('salarie', 'Salarié'),
        ('developpeur', 'développeur'),
        ('technicien', 'Téchnicien'),
        ('benevole', 'Bénévole'),
        ('manager', 'Manager'),
        ('freelance', 'Freelance'),
        ('rh', 'Ressource humaine')
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,  related_name='employee', blank=True, null=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True , default="photos/default.png")
    email = models.EmailField(max_length=100, unique=True)
    numero_telephone = models.CharField(max_length=15)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    ville = models.CharField(max_length=100)
    adresse = models.CharField(max_length=100)
    statut_matrimonial = models.CharField(max_length=11, choices=STATUT_CHOICES)
    nationalite = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10)
    date_embauche = models.DateField(default=timezone.now)
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True)
    type_salarie = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=10, choices=STATUTCON_CHOICES, default="T")
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, null=True)
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, null=True)
    type_contrat = models.CharField(max_length=10, choices=CONTRAT_CHOICES, null=True)
    lettre_motivation = models.FileField( upload_to='fichier/', null=True, blank=True)
    lettre_introduction = models.FileField( upload_to='fichier/', null=True, blank=True)
    bulletin_salaire = models.FileField( upload_to='fichier/', null=True, blank=True)
    curriculum_vitae = models.FileField( upload_to='fichier/', null=True, blank=True)
    id_facebook = models.CharField(max_length=150, null=True)
    id_skype = models.CharField(max_length=150, null=True)
    id_github = models.CharField(max_length=150, null=True)
    id_linkedln = models.CharField(max_length=150, null=True)
    groupe = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True,blank=True)
    jours_conge_annuels = models.PositiveIntegerField(default=15)  # Jours de congé annuels
    jours_conge_formation = models.PositiveIntegerField(default=12)  # Jours de congé pour formation
    jours_conge_maternite = models.PositiveIntegerField(default=105)  # Jours de congé maternité
    jours_conge_paternite = models.PositiveIntegerField(default=3)  # Jours de congé pour paternité
    jours_conge_exceptionnel = models.PositiveIntegerField(default=10)  # Jours de congé exceptionel
    jours_conge_obligatoire = models.PositiveIntegerField(default=15)  # Jours de congé obligatoire

    def clean(self):
        # Validation du numéro de téléphone
        if not re.match(r'^\+?[0-9]{10}$', self.numero_telephone):
            raise ValidationError('Le numéro de téléphone doit comporter que 10.')

        # Validation de la date de naissance (vérifie si l'âge est raisonnable)
        if self.date_naissance >= timezone.now().date():
            raise ValidationError('La date de naissance doit être dans le passé.')

        # Gener automatiquement un âge pour l'employé
    def age(self):
        today = date.today()
        return today.year - self.date_naissance.year - (
                    (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))

    def __str__(self):
        return f"{self.nom} {self.prenom}"

 #User modifier pour rajouter photo de profil

 #Model Congé
class Conge(models.Model):
    TYPE_CHOICES = [
        ('ANN', 'Annuel'),
        ('FOR', 'Formation'),
        ('MAT', 'Maternité'),
        ('PAT', 'Paternité'),
        ('EXC', 'Exceptionnel'),
        ('OBL', 'Obligatoire'),
    ]

    STATUTS = [
        ('en_attente', 'En attente'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
    ]

    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, null=True)
    type_conge = models.CharField(max_length=3, choices=TYPE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    jours_utilises = models.PositiveIntegerField()
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    raison = models.TextField(blank=True, null=True)
    piece_justificatif = models.FileField(upload_to='fichier/', null=True, blank=True)
    date_demande = models.DateTimeField(default=timezone.now)
    raison_refus = models.TextField(null=True, blank=True)
    responsable = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_responsables')  # Lien avec l'employé qui répond au congé

    def jours_maximum(self):
        """Renvoie le nombre maximum de jours autorisés pour le type de congé."""
        if self.type_conge == 'ANN':
            return 15
        elif self.type_conge == 'FOR':
            return 12
        elif self.type_conge == 'MAT':
            return 105
        elif self.type_conge == 'PAT':
            return 3
        elif self.type_conge == 'EXC':
            return 10
        elif self.type_conge == 'OBL':
            return 15
        return 0

    def verifier_jours_restants(self):
        """Calcule les jours restants pour le type de congé spécifique."""

        # Assure-toi que l'employé est bien associé au congé
        if self.employee is None:
            raise ValueError("L'employé associé au congé est indéfini.")

        # On récupère les jours de congé disponibles
        jours_disponibles = {
            'ANN': self.employee.jours_conge_annuels,
            'FOR': self.employee.jours_conge_formation,
            'MAT': self.employee.jours_conge_maternite,
            'PAT': self.employee.jours_conge_paternite,
            'EXC': self.employee.jours_conge_exceptionnel,
            'OBL': self.employee.jours_conge_obligatoire,
        }

        # Vérifie si le type de congé est valide
        if self.type_conge not in jours_disponibles:
            raise ValueError(f"Type de congé '{self.type_conge}' non valide.")

        # Calcul des jours restants
        jours_restants = jours_disponibles[self.type_conge] - self.jours_utilises

        # Si jours_restants est négatif, retourne 0
        return max(jours_restants, 0)

    def save(self, *args, **kwargs):
        # Vérifier si les jours utilisés dépassent le maximum autorisé pour le type de congé
        if self.verifier_jours_restants() > self.jours_maximum():
            raise ValueError("Le nombre de jours utilisés dépasse le maximum autorisé pour ce type de congé.")

        # Vérifier les jours de congé restants pour l'employé
        if self.verifier_jours_restants() < 0:
            raise ValueError("Le nombre de jours restants pour cet employé est insuffisant.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.employee} - {self.type_conge} du {self.date_debut} au {self.date_fin} - {self.statut}'

#Model Notification
class Notification(models.Model):
    TYPES = [
        ('conge_termine', 'Congé terminé'),
        ('rappel_mise_a_jour', 'Rappel de mise à jour'),
        ('conge_approuve', 'Congé approuvé'),
        ('conge_refuse', 'Congé refusé'),
        ('fiche_de_paie_prete', 'Fiche de paie prête'),
        ('mise_a_jour_document', 'Mise à jour de document'),
        ('avis_de_conge', 'Avis de congé'),
        ('demande_conge_recue', 'Demande de congé reçue'),
        ('connexion_reussi', 'Connéxion réussie'),
        ('deconnexion_reussi', 'Déconnexion réussie')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_creat_notifications')
    type = models.CharField(max_length=20, choices=TYPES)
    message = models.TextField()
    date_created = models.DateTimeField(default=timezone.now)
    is_global = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.get_type_display()} pour {self.user.username}"

class UserNotification(models.Model):
    user_affected = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_received_notifications')
    is_read = models.BooleanField(default=False)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='notifications')

class Historique(models.Model):
    ACTION_CHOICES = [
        ('create', 'Création'),
        ('update', 'Mise à jour'),
        ('delete', 'Suppression'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('export', 'Exportation')
                    ]

    CATEGORIE_CHOICES = [
        ('employe', 'Employé'),
        ('conge', 'Congé'),
        ('paie', 'Paie'),
        ('session', 'Session'),
        ('privilege', 'Privilèges'),
        ('calendrier', 'Calendrier'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    consequence = models.TextField(null=True, blank=True)
    utilisateur_affecte = models.CharField(max_length=255, null=True, blank=True)
    date_action = models.DateTimeField(default=timezone.now)
    categorie = models.CharField(max_length=50, choices=CATEGORIE_CHOICES)

    def __str__(self):
        return f"{self.utilisateur} a effectué {self.action} dans {self.categorie} à {self.date_action}"



class Schedule(models.Model):
    DAY_CHOICES = [
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
        ('Vendredi', 'Vendredi'),
        ('Samedi', 'Samedi'),
        ('Dimanche', 'Dimanche')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)  # Liaison avec le modèle User
    location = models.CharField(max_length=100)  # Lieu de travail
    start_time = models.TimeField()  # Heure de début
    end_time = models.TimeField()  # Heure de fin
    start_date = models.DateField()  # Date de début
    end_date = models.DateField()  # Date de fin
    jour_debut = models.CharField(max_length=10, choices=DAY_CHOICES , null=True)
    jour_fin = models.CharField(max_length=10, choices=DAY_CHOICES, null=True)
    description = models.TextField(blank=True, null=True)  # Description des tâches

    def __str__(self):
        return f'{self.employee.username} - {self.post}'

class UserSettings(models.Model):
    THEME_CHOICES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    language = models.CharField(max_length=5, choices=settings.LANGUAGES, default='fr')
    theme = models.CharField(max_length=5, choices=THEME_CHOICES, default='light')
    receive_desktop_notifications = models.BooleanField(default=True)
    receive_email_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings for {self.user.username}"

class AgendaEvent(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_time = models.TimeField()
    start_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Paie(models.Model):
    TYPE_CHOICES = [
        ('payé', 'payé'),
        ('En attente', 'En attente')
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    mois = models.CharField(max_length=20)
    matricule = models.CharField(max_length=20, unique=True)
    salaire_base = models.DecimalField(max_digits=10, decimal_places=2, )
    indemnite_transport = models.DecimalField(max_digits=10, decimal_places=2, )
    salaire_brut = models.DecimalField(max_digits=10, decimal_places=2, )
    smids = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cnaps = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    irsa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avance = models.DecimalField(max_digits=10, decimal_places=2, )
    regul_smids = models.DecimalField(max_digits=10, decimal_places=2, )
    salaire_net = models.DecimalField(max_digits=10, decimal_places=2, )
    montant_imposable = models.DecimalField(max_digits=10, decimal_places=2, )
    date_creation = models.DateTimeField(auto_now_add=True)  # Assurez-vous que ce champ existe
    signature_directeur = models.CharField(max_length=100, blank=True, null=True)
    signature_beneficiaire = models.CharField(max_length=100, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True)

    def __str__(self):
        return f"Fiche de paie de {self.employee.prenom} {self.employee.nom} pour {self.mois}"

