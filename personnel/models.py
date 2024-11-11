from decimal import Decimal

from django.db import models
from django.utils import timezone
from datetime import date, datetime
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
        return f"{self.nom}"

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
    prenom = models.CharField(max_length=100, null=True)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True)
    numero_telephone = models.CharField(max_length=15, null=True)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    ville = models.CharField(max_length=100)
    adresse = models.CharField(max_length=100)
    statut_matrimonial = models.CharField(max_length=11, choices=STATUT_CHOICES)
    nationalite = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10)
    groupe_sanguin = models.CharField(max_length=3, null=True, blank=True)
    maladie = models.CharField(max_length=200,  null=True,blank=True)
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
    id_github = models.CharField(max_length=150, null=True, blank=True)
    id_linkedln = models.CharField(max_length=150, null=True, blank=True)
    groupe = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True,blank=True)
    jours_conge_annuels = models.PositiveIntegerField(default=15)  # Jours de congé annuels
    jours_conge_formation = models.PositiveIntegerField(default=12)  # Jours de congé pour formation
    jours_conge_maternite = models.PositiveIntegerField(default=105)  # Jours de congé maternité
    jours_conge_paternite = models.PositiveIntegerField(default=3)  # Jours de congé pour paternité
    jours_conge_exceptionnel = models.PositiveIntegerField(default=10)  # Jours de congé exceptionel
    jours_conge_obligatoire = models.PositiveIntegerField(default=15)  # Jours de congé obligatoire
    salaire_base = models.IntegerField(default=0, blank=True)

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
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    raison = models.TextField(blank=True, null=True)
    piece_justificatif = models.FileField(upload_to='fichier/', null=True, blank=True)
    date_demande = models.DateTimeField(default=timezone.now)
    raison_refus = models.TextField(null=True, blank=True)
    responsable = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conges_responsables'
    )  # Lien avec l'employé qui répond au congé

    def jours_utilises(self):
        """Calcule le nombre de jours de congé utilisés."""
        return (self.date_fin - self.date_debut).days + 1  # +1 pour inclure le dernier jour

    def jours_maximum(self):
        """Renvoie le nombre maximum de jours autorisés pour le type de congé."""
        max_jours = {
            'ANN': 15,
            'FOR': 12,
            'MAT': 105,
            'PAT': 3,
            'EXC': 10,
            'OBL': 15,
        }
        return max_jours.get(self.type_conge, 0)

    def verifier_jours_restants(self):
        """Calcule les jours restants pour le type de congé spécifique."""
        if self.employee is None:
            raise ValueError("L'employé associé au congé est indéfini.")

        jours_disponibles = {
            'ANN': self.employee.jours_conge_annuels,
            'FOR': self.employee.jours_conge_formation,
            'MAT': self.employee.jours_conge_maternite,
            'PAT': self.employee.jours_conge_paternite,
            'EXC': self.employee.jours_conge_exceptionnel,
            'OBL': self.employee.jours_conge_obligatoire,
        }

        jours_disponibles_type = jours_disponibles.get(self.type_conge)
        if jours_disponibles_type is None:
            raise ValueError(f"Type de congé '{self.type_conge}' non valide.")

        return max(jours_disponibles_type - self.jours_utilises(), 0)

    def save(self, *args, **kwargs):
        # Vérifie si le nombre de jours demandés est supérieur au maximum autorisé
        if self.jours_utilises() > self.jours_maximum():
            raise ValueError("Le nombre de jours demandés dépasse le maximum autorisé pour ce type de congé.")

        # Vérifie si l'employé a assez de jours restants
        if self.verifier_jours_restants() <= 0:
            raise ValueError("Le nombre de jours restants pour ce type de congé est insuffisant pour l'employé.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.employee} - {self.type_conge} du {self.date_debut} au {self.date_fin} - {self.statut}'


    #Model Notification
class Notification(models.Model):
    TYPES = [
        ('employee_create', 'Création d\'un nouvel employé réussie'),
        ('conge_termine', 'Le congé est terminé'),
        ('rappel_mise_a_jour', 'Rappel pour mise à jour'),
        ('conge_approuve', 'Le congé a été approuvé'),
        ('conge_refuse', 'Le congé a été refusé'),
        ('paie_create', 'La fiche de paie a été créée'),
        ('paie_delete', 'La fiche de paie a été supprimée'),
        ('paie_update', 'La fiche de paie a été mise à jour'),
        ('paie_ready', 'La fiche de paie est prête'),
        ('mise_a_jour_document', 'Le document a été mis à jour'),
        ('avis_de_conge', 'Un avis de congé a été émis'),
        ('demande_conge_recue', 'La demande de congé a été reçue'),
        ('connexion_reussi', 'Connexion réussie'),
        ('deconnexion_reussi', 'Déconnexion réussie'),
        ('demande_conge', 'La demande de congé a été envoyée avec succès'),
        ('schedule_create', 'Un nouvel emploi du temps a été ajouté au calendrier'),
        ('schedule_delete',  'Un emploi du temps a été supprimer'),
        ('evenement_create', 'Un nouvel événement a été ajouté'),
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
        ('emploi_du_temps', 'Calendrier'),
        ('evenement', 'Événement'),
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
        return f'{self.employee.nom} {self.employee.prenom} - {self.location}'

class UserSettings(models.Model):
    THEME_CHOICES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    language = models.CharField(max_length=10, choices=settings.LANGUAGES, default='fr')
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
        ('P', 'Payé'),
        ('E', 'En attente')
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    salaire_base = models.IntegerField(null=True, default=0)
    indemnite_transport = models.IntegerField(default=0)  # Indemnité
    indemnite_communication = models.IntegerField(default=0)  # Indemnité
    indemnite_stage = models.IntegerField(default=0)  # Indemnité
    statut = models.CharField(max_length=2,choices=TYPE_CHOICES, null=True)
    net_a_payer = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Champs pour la date de début et de fin d'exercice
    date_debut = models.DateField(help_text="Début de la période d'exercice")
    date_fin = models.DateField(help_text="Fin de la période d'exercice")

    # Champ lot (mois et année, ex: Janvier 2024)

    # Date de création automatiquement générée
    date_creation = models.DateTimeField(auto_now_add=True)

    # Champ généré automatiquement pour l'exercice (intervalle de temps)
    exercice = models.CharField(max_length=50, editable=False)

    # Constantes pour les taux de cotisations à Madagascar


    # Calcul du salaire brut en tenant compte de l'indemnité et de l'indice d'ancienneté
    def calcul_salaire_brut(self):
        total_primes = sum(Decimal(prime.montant) for prime in self.primes.all())
        salaire_base_anciennete = Decimal(self.salaire_base)
        return salaire_base_anciennete + total_primes + Decimal(self.indemnite_stage) + Decimal(
            self.indemnite_communication) + Decimal(self.indemnite_transport)





    # Méthode save pour automatiser les calculs lors de la sauvegarde
    def save(self, *args, **kwargs):
        # Sauvegarder l'instance pour générer une clé primaire
        if self.pk is None:  # Vérifiez que la paie n'a pas encore de clé primaire
            super(Paie, self).save(*args, **kwargs)

        self.salaire_brut = self.calcul_salaire_brut()

        # Si le lot est fourni sans jour, on ajoute le 1er jour du mois
        if isinstance(self.date_debut, str):
            self.date_debut = datetime.strptime(self.date_debut, '%Y-%m-%d').date()
        if isinstance(self.date_fin, str):
            self.date_fin = datetime.strptime(self.date_fin, '%Y-%m-%d').date()

        # Génération automatique du champ "exercice"
        self.exercice = f"{self.date_debut.strftime('%d %b')} - {self.date_fin.strftime('%d %b')}"

        # Puis sauvegarder à nouveau avec les calculs mis à jour
        super(Paie, self).save(*args, **kwargs)

    def __str__(self):
        return f"Fiche de paie de {self.employee.prenom} {self.employee.nom} pour {self.lot}"

class Prime(models.Model):

    nom = models.CharField(max_length=100)
    paie = models.ForeignKey(Paie, on_delete=models.CASCADE, related_name='primes')
    montant = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nom} - {self.montant} MGA"
