import base64
import os
import subprocess
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash, get_user_model
from django.utils.translation import activate
from django.contrib.auth.models import Permission, User
from rest_framework.generics import UpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView
from xhtml2pdf import pisa
from .models import Employee, Conge, Notification, Historique, Schedule, UserSettings, AgendaEvent, Paie, \
    UserNotification, Poste, Departement, Competence, Prime
from .serializers import RefusCongeSerializer, EmployeeSerializer, CongeSerializer, CongesDetailSerializer, \
    NotificationSerializer, ScheduleSerializer, SettingsSerializer, AgendaEventSerializer, HistoriqueSerializer, \
    ScheduleListSerializer, PaieSerializer, LoginSerializer, UserNotificationSerializer
from .services import create_notification, create_global_notification
from rest_framework.decorators import action
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.template.response import TemplateResponse
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# from weasyprint import HTML, CSS
from django.db.models.functions import TruncMonth
from django.db.models import F
# from weasyprint.text.fonts import FontConfiguration
from django.contrib.staticfiles import finders
from django.template.loader import get_template


CustomUser = get_user_model()

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Exige que l'utilisateur soit authentifié

    def get(self, request, *args, **kwargs):
        # Récupération des statistiques des employés
        total_salaries = Employee.objects.count()
        salaries_en_conge = Employee.objects.filter(statut='C').count()
        salaries_disponibles = Employee.objects.filter(statut='T').count()

        # Récupération des notifications non lues
        unread_notifications = UserNotification.objects.filter(
            user_affected=request.user,
            is_read=False
        ).select_related('notification').values(
            'notification__user__username',
            'notification__message',
            'notification__date_created'
        )

        # Calcul des dates pour les événements
        today = timezone.now().date()
        tomorrow = today + timezone.timedelta(days=1)

        # Récupération des événements d'aujourd'hui
        today_events = AgendaEvent.objects.filter(
            start_date__date=today
        ).values(
            'description',
            'title',
            'start_time',
            'start_date'
        )

        # Récupération des événements de demain
        tomorrow_events = AgendaEvent.objects.filter(
            start_date__date=tomorrow
        ).values(
            'description',
            'title',
            'start_time',
            'start_date'
        )

        # Préparation du contexte pour le template
        context = {
            'total_salaries': total_salaries,
            'salaries_en_conge': salaries_en_conge,
            'salaries_disponibles': salaries_disponibles,
            'unread_notifications': list(unread_notifications),
            'today_events': list(today_events),
            'tomorrow_events': list(tomorrow_events),
        }

        # Rendu du template avec le contexte
        return render(request, 'dashboard.html', context)

#Les classes pour gérer les permissions
class EmployeePermission(permissions.BasePermission):
    """
    Classe pour gérer les permissions spécifiques à l'ajout et à la modification d'employés.
    """

    def has_permission(self, request, view):
        # Pour la création d'un employé, vérifier la permission 'add_employee'
        if view.action == 'create':
            return request.user.is_authenticated and request.user.has_perm('personnel.add_employee')

        # Pour la mise à jour d'un employé, vérifier la permission 'change_employee'
        if view.action == 'update':
            return request.user.is_authenticated and request.user.has_perm('personnel.change_employee')

        # Autoriser la liste pour tous les utilisateurs connectés
        if view.action == 'list':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_employee')

        return False  # Interdire par défaut toute autre action

class CongePermission(permissions.BasePermission):
    """
    Gère les permissions pour les actions de création, mise à jour et consultation des congés.
    """

    def has_permission(self, request, view):
        # Si l'action est 'create', vérifier la permission 'add_conge'
        if view.action == 'create':
            return request.user.is_authenticated and request.user.has_perm('personnel.add_conge')

        # Si l'action est 'update' ou 'partial_update', vérifier la permission 'change_conge'
        if view.action in ['update', 'partial_update']:
            return request.user.is_authenticated and request.user.has_perm('personnel.change_conge')

        # Si l'action est 'list', autoriser seulement si l'utilisateur est authentifié et possède la permission 'view_conge'
        if view.action == 'list':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_conge')

        # Si l'action est 'retrieve' (voir les détails d'un congé), vérifier la permission 'view_conge'
        if view.action == 'retrieve':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_conge')

        return False

    def has_object_permission(self, request, view, obj):
        # Permettre aux directeurs et assistant-directeurs de voir tous les congés
        if request.user.has_perm('personnel.acces_all_conge').exists():
            return True

        # Si l'utilisateur est un employé normal, il ne peut voir que ses propres congés
        if view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return obj.employee.user == request.user

        # Pour toute autre action, refuser l'accès par défaut
        return False
class HistoriquePermission(permissions.BasePermission):
    """
    Classe pour gérer les permissions liée à l'historique.
    """

    def has_permission(self, request, view):

        if view.action == 'get':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_historique')

        return False  # Interdire par défaut toute autre action


class SchedulePermission(permissions.BasePermission):
    """
    Classe pour gérer les permissions du calendrier.
    """

    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated and request.user.has_perm('personnel.add_schedule')

        if view.action == 'retrieve':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_schedule')

        if view.action == 'update':
            return request.user.is_authenticated and request.user.has_perm('personnel.change_schedule')

        if view.action == 'list':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_schedule')

        if view.action == 'destroy':
            return request.user.is_authenticated and request.user.has_perm('personnel.delete_schedule')

        return False  # Interdire par défaut toute autre action

class AgendaEventPermission(permissions.BasePermission):
    """
    Classe pour gérer les permissions des agendas.
    """

    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated and request.user.has_perm('personnel.add_agendaevent')

        if view.action == 'update':
            return request.user.is_authenticated and request.user.has_perm('personnel.change_agendaevent')

        if view.action == 'list':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_agendaevent')

        if view.action == 'destroy':
            return request.user.is_authenticated and request.user.has_perm('personnel.delete_agendaevent')

        return False  # Interdire par défaut toute autre action

class PaiePermission(permissions.BasePermission):
    """
    Classe pour gérer les permissions des fiches de paies.
    """

    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated and request.user.has_perm('personnel.add_paie')

        if view.action == 'update' or 'partial_update':
            return request.user.is_authenticated and request.user.has_perm('personnel.change_paie')

        if view.action == 'list':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_paie')

        if view.action == 'retrieve':
            return request.user.is_authenticated and request.user.has_perm('personnel.view_paie')

        if view.action == 'destroy':
            return request.user.is_authenticated and request.user.has_perm('personnel.delete_paie')

        return False  # Interdire par défaut toute autre action

    def has_object_permission(self, request, view, obj):
        # Vérifie les permissions pour les fiches de paie spécifiques
        if request.user.has_perm('personnel.acces_all_paie').exists():
            return True

            # Si l'utilisateur est un employé normal, il ne peut voir que ses propres congés
        if view.action in ['retrieve', 'update', 'partial_update', 'destroy', 'list']:
            return obj.employee.user == request.user

            # Pour toute autre action, refuser l'accès par défaut
        return False

class ExportPaiePermission(permissions.BasePermission):
    """
    Permission personnalisée pour l'exportation des fiches de paie.
    """

    def has_permission(self, request, view):
        # Vérifie si l'utilisateur est authentifié et a la permission d'exporter des fiches de paie
        return request.user.is_authenticated and request.user.has_perm('personnel.export_paie')


# Pagination personnalisée
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Nombre d'éléments par page
    page_size_query_param = 'page_size'
    max_page_size = 100

#Les vues
class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour regrouper les actions list, create, et update des employés.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    #permission_classes = [EmployeePermission]  # Exige que l'utilisateur soit authentifié et a les permission spécifique
    pagination_class = CustomPageNumberPagination  # Utilise la pagination personnalisée

    # Spécifie que cette vue peut rendre du HTML
    renderer_classes = [TemplateHTMLRenderer]

    @action(detail=False, methods=['GET', 'POST'], renderer_classes=[TemplateHTMLRenderer])
    def create_employee_form(self, request, *args, **kwargs):

        # Pour les requêtes GET, on récupère les choix pour les départements et les postes
        departements = Departement.objects.all()
        postes = Poste.objects.all()
        type_choices = Employee.TYPE_CHOICES
        contrat_choices = Employee.CONTRAT_CHOICES
        statut_matrimonials = Employee.STATUT_CHOICES
        sexes = Employee.SEXE_CHOICES
        competences = Competence.objects.all()

        return Response({
            'departements': departements,
            'postes': postes,
            'type_choices': type_choices,
            'contrat_choices': contrat_choices,
            'statut_matrimonial': statut_matrimonials,
            'sexe': sexes,
            'competences': competences,
        }, template_name='employee_cree.html')

    # Liste des employés
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Récupérer les filtres
        id_filter = request.GET.get('id', None)
        nom_filter = request.GET.get('nom', None)
        poste_filter = request.GET.getlist('poste', None)
        type_filter = request.GET.get('type_salarie', None)
        statut_filter = request.GET.get('statut', None)
        date_embauche_filter = request.GET.get('date_embauche', None)
        departement_filter = request.GET.getlist('departement', None)
        competence_filter = request.GET.getlist('competence', None)

        if id_filter:
            queryset = queryset.filter(id=id_filter)  # Filtrer par ID exact
        if nom_filter:
            queryset = queryset.filter(nom__icontains=nom_filter)  # Filtrer par nom (insensible à la casse)
        if poste_filter:
            queryset = queryset.filter(poste__id__in=poste_filter)  # Filtrer par le nom du poste
        if type_filter:
            queryset = queryset.filter(type_salarie=type_filter)  # Filtrer par type de salarié (exact)
        if statut_filter:
            queryset = queryset.filter(statut=statut_filter)  # Filtrer par statut (exact)
        if date_embauche_filter:
            queryset = queryset.filter(date_embauche=date_embauche_filter)  # Filtrer par date d'embauche exacte
        if departement_filter:
            queryset = queryset.filter(departement__id__in=departement_filter)
        if competence_filter:
            queryset = queryset.filter(competence__id__in=competence_filter).distinct()

        # Paginer le queryset
        paginator = CustomPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        total_employees = queryset.count()

        filtered_employees = []
        for emp in page:
            filtered_employees.append({
                'photo': emp.photo.url if emp.photo else None,
                'nom': emp.nom,
                'prenom': emp.prenom,
                'id': emp.id,
                'poste': emp.poste.nom if emp.poste else None,
                'type_salarie': emp.get_type_salarie_display(),
                'statut': emp.get_statut_display(),
                'date_embauche': emp.date_embauche,
                'departement': emp.departement.nom if emp.departement else None,
                'email': emp.email,
            })
        num_pages = paginator.page.paginator.num_pages if paginator.page else None
        departements = Departement.objects.all()  # Récupère tous les départements
        competences = Competence.objects.all()  # Récupère toutes les compétences
        types_salaries = Employee.TYPE_CHOICES  # Récupère les choix de types de salarié
        postes = Poste.objects.all()

        # Retourner les employés dans un template HTML avec la pagination
        return render(request, 'employee_list.html', {
            'employees': filtered_employees,
            'paginator': paginator,
            'page_obj': paginator.page,
            'num_pages': num_pages,  # Passe explicitement le nombre total de pages
            'total_employees': total_employees,
            'departements': departements,
            'competences': competences,
            'type_salaries': types_salaries,
            'postes': postes,
        })


    # Mise à jour d'un employé
    def perform_update(self, serializer):
        # Sauvegarder les modifications de l'employé
        employee = serializer.save()

        # Créer une notification pour la modification d'un employé
        create_notification(
            user_action=self.request.user,
            message=f"L'employé {employee.nom} a été modifié.",
            user_affected=employee.user
        )

        # Créer un historique de la mise à jour de l'employé
        Historique.objects.create(
            utilisateur=self.request.user,
            action='update',
            consequence=f"Mise à jour des informations de l'employé : {employee.nom} {employee.prenom}",
            utilisateur_affecte=employee.user,
            categorie='employe',
            date_action=timezone.now(),
        )

        # Méthode de création d'employé via POST

    def create(self, request, *args, **kwargs):
        # Récupérer les données du formulaire POST
        employee_data = request.POST

        # Valider les données du formulaire
        photo = employee_data.get('photo')
        date_naissance = employee_data.get('date_naissance')
        email = employee_data.get('email')
        pays = employee_data.get('pays')
        code_postal = employee_data.get('code_postal')
        nom = employee_data.get('nom')
        prenom = employee_data.get('prenom')
        sexe = employee_data.get('sexe')
        statut_matrimonial = employee_data.get('statut_matrimonial')
        type_contrat = employee_data.get('type_contrat')
        departement_id = employee_data.get('departement')
        poste_id = employee_data.get('poste')

        # Créer un nouvel employé après vérification des champs
        new_employee = Employee(
            photo=photo,
            nom=nom,
            prenom=prenom,
            sexe=sexe,
            statut_matrimonial=statut_matrimonial,
            date_naissance=date_naissance,
            type_contrat=type_contrat,
            departement_id=departement_id,
            poste_id=poste_id,
        )

        try:
            # Enregistrer le nouvel employé
            new_employee.save()

            # Créer une notification pour l'ajout d'un employé
            create_notification(
                user_action=request.user,
                message=f"Un nouvel employé {new_employee.nom} a été ajouté.",
                user_affected=new_employee.user
            )

            # Créer un historique de l'ajout de l'employé
            Historique.objects.create(
                utilisateur=request.user,
                action='create',
                consequence=f"Ajout d'un nouvel employé : {new_employee.nom} {new_employee.prenom}",
                utilisateur_affecte=new_employee.user,
                categorie='employe',
                date_action=timezone.now(),
            )

            # Rediriger après succès
            return redirect('personnel:employee-list')

        except Exception as e:
            # Gestion d'erreur en cas de problème lors de la sauvegarde
            return Response({'error': str(e)}, template_name='employee_cree.html')

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        employee = response.data

        return Response({
            'status': 'success',
            'message': f"L'employé {employee['nom']} {employee['prenom']} a été modifié avec succès."
        }, status=status.HTTP_200_OK)

########################################

class EmployeeCreateAPIView(APIView):
    """
    Vue pour la création d'un nouvel employé.
    """
    def get(self, request, *args, **kwargs):
        # Récupérer toutes les données nécessaires pour le formulaire
        departements = Departement.objects.all()
        postes = Poste.objects.all()
        type_choices = Employee.TYPE_CHOICES
        contrat_choices = Employee.CONTRAT_CHOICES
        statut_matrimonials = Employee.STATUT_CHOICES
        sexes = Employee.SEXE_CHOICES
        competences = Competence.objects.all()

        # Créer un dictionnaire de contexte pour envoyer ces données au template
        context = {
            'departements': departements,
            'postes': postes,
            'type_choices': type_choices,
            'contrat_choices': contrat_choices,
            'statut_matrimonials': statut_matrimonials,
            'sexes': sexes,
            'competences': competences
        }

        # Afficher le formulaire HTML pour créer un employé avec les contextes
        return render(request, 'employee_cree.html', context)

    def post(self, request, *args, **kwargs):
        # Récupérer les données du formulaire POST
        employee_data = request.data
        employee_files = request.FILES  # Pour gérer les fichiers uploadés

        # Valider les données du formulaire
        nom = employee_data.get('nom')
        prenom = employee_data.get('prenom')
        sexe = employee_data.get('sexe')
        statut_matrimonial = employee_data.get('statut_matrimonial')
        date_naissance = employee_data.get('date_naissance')
        type_contrat = employee_data.get('type_contrat')
        departement_id = employee_data.get('departement')
        poste_id = employee_data.get('poste')
        type_salarie = employee_data.get('type_salarie')
        email = employee_data.get('email')
        numero_telephone = employee_data.get('numero_telephone')
        ville = employee_data.get('ville')
        adresse = employee_data.get('adresse')
        nationalite = employee_data.get('nationalite')
        pays = employee_data.get('pays')
        code_postal = employee_data.get('code_postal')
        maladie = employee_data.get('maladie')
        groupe_sanguin = employee_data.get('groupe_sanguin')
        date_embauche = employee_data.get('date_embauche')
        competence_id = employee_data.get('competence')
        salaire_base = employee_data.get('salaire_base')

        # Fichiers téléchargés
        photo = employee_files.get('photo')
        lettre_motivation = employee_files.get('lettre_motivation')
        lettre_introduction = employee_files.get('lettre_introduction')
        bulletin_salaire = employee_files.get('bulletin_salaire')
        curriculum_vitae = employee_files.get('curriculum_vitae')

        # Identifiants sociaux
        id_github = employee_data.get('id_github')
        id_linkedln = employee_data.get('id_linkedln')

        try:
            # Créer un nouvel employé après validation des champs
            new_employee = Employee(
                nom=nom,
                prenom=prenom,
                sexe=sexe,
                statut_matrimonial=statut_matrimonial,
                date_naissance=date_naissance,
                type_contrat=type_contrat,
                type_salarie=type_salarie,
                departement_id=departement_id,
                poste_id=poste_id,
                email=email,
                numero_telephone=numero_telephone,
                ville=ville,
                adresse=adresse,
                nationalite=nationalite,
                pays=pays,
                code_postal=code_postal,
                groupe_sanguin=groupe_sanguin,
                maladie=maladie,
                date_embauche=date_embauche,
                competence_id=competence_id,
                salaire_base=salaire_base,
                photo=photo if photo else "photos/pdp_defaut.png",
                lettre_motivation=lettre_motivation,
                lettre_introduction=lettre_introduction,
                bulletin_salaire=bulletin_salaire,
                curriculum_vitae=curriculum_vitae,
                id_github=id_github,
                id_linkedln=id_linkedln,
            )

            # Enregistrer le nouvel employé dans la base de données
            new_employee.save()

            # Créer une notification pour l'ajout de l'employé
            create_notification(
                user_action=request.user,
                type='employee_create',
                message=f"Un nouvel employé {new_employee.nom} {new_employee.prenom} a été ajouté.",
                user_affected=new_employee.user
            )

            # Créer un historique de l'ajout de l'employé
            Historique.objects.create(
                utilisateur=request.user,
                action='create',
                consequence=f"Ajout d'un nouvel employé : {new_employee.nom} {new_employee.prenom}",
                utilisateur_affecte=new_employee,
                categorie='employe',
                date_action=timezone.now(),
            )

            # Rediriger après succès
            return redirect('personnel:employee-list')

        except Exception as e:
            # Gestion d'erreur en cas de problème lors de la sauvegarde
            return Response({'error': str(e)}, status=400)


class EmployeeUpdateAPIView(APIView):
    def get(self, request, employee_id, *args, **kwargs):
        try:
            # Récupérer l'employé par son ID
            employee = Employee.objects.get(id=employee_id)

            # Récupérer les données contextuelles comme dans la création
            departements = Departement.objects.all()
            postes = Poste.objects.all()
            type_choices = Employee.TYPE_CHOICES
            contrat_choices = Employee.CONTRAT_CHOICES
            statut_matrimonials = Employee.STATUT_CHOICES
            sexes = Employee.SEXE_CHOICES
            competences = Competence.objects.all()

            # Préparer les données pour pré-remplir le formulaire
            context = {
                'employee': employee,
                'departements': departements,
                'postes': postes,
                'type_choices': type_choices,
                'contrat_choices': contrat_choices,
                'statut_matrimonials': statut_matrimonials,
                'sexes': sexes,
                'competences': competences,
            }

            # Rendre le formulaire avec les données pré-remplies
            return render(request, 'employee_update.html', context)

        except Employee.DoesNotExist:
            return Response({'error': 'Employé non trouvé'}, status=404)

    def post(self, request, employee_id, *args, **kwargs):
        try:
            # Récupérer l'employé par son ID
            employee = Employee.objects.get(id=employee_id)

            # Récupérer les données du formulaire POST
            employee_data = request.data
            employee_files = request.FILES

            # Mettre à jour les champs avec les nouvelles données
            employee.nom = employee_data.get('nom')
            employee.prenom = employee_data.get('prenom')
            employee.sexe = employee_data.get('sexe')
            employee.statut_matrimonial = employee_data.get('statut_matrimonial')
            employee.date_naissance = employee_data.get('date_naissance')
            employee.type_contrat = employee_data.get('type_contrat')
            employee.type_salarie = employee_data.get('type_salarie')
            employee.departement_id = employee_data.get('departement')
            employee.poste_id = employee_data.get('poste')
            employee.email = employee_data.get('email')
            employee.numero_telephone = employee_data.get('numero_telephone')
            employee.ville = employee_data.get('ville')
            employee.adresse = employee_data.get('adresse')
            employee.nationalite = employee_data.get('nationalite')
            employee.pays = employee_data.get('pays')
            employee.code_postal = employee_data.get('code_postal')
            employee.groupe_sanguin = employee_data.get('groupe_sanguin')
            employee.maladie = employee_data.get('maladie')
            employee.date_embauche = employee_data.get('date_embauche')
            employee.competence_id = employee_data.get('competence')
            employee.salaire_base = employee_data.get('salaire_base')

            # Mettre à jour les fichiers si présents
            if employee_files.get('photo'):
                employee.photo = employee_files.get('photo')
            if employee_files.get('lettre_motivation'):
                employee.lettre_motivation = employee_files.get('lettre_motivation')
            if employee_files.get('lettre_introduction'):
                employee.lettre_introduction = employee_files.get('lettre_introduction')
            if employee_files.get('bulletin_salaire'):
                employee.bulletin_salaire = employee_files.get('bulletin_salaire')
            if employee_files.get('curriculum_vitae'):
                employee.curriculum_vitae = employee_files.get('curriculum_vitae')

            # Sauvegarder les modifications
            employee.save()

            # Créer un historique de la modification de l'employé
            Historique.objects.create(
                utilisateur=request.user,
                action='update',
                consequence=f"Modification de l'employé : {employee.nom} {employee.prenom}",
                utilisateur_affecte=employee,
                categorie='employe',
                date_action=timezone.now(),
            )

            # Rediriger après succès
            return redirect('personnel:employee-list')

        except Employee.DoesNotExist:
            return Response({'error': 'Employé non trouvé'}, status=404)

        except Exception as e:
            # Gestion d'erreur
            return Response({'error': str(e)}, status=400)


class EmployeeDetailAPIView(APIView):
    def get(self, request, employee_id, *args, **kwargs):
        try:
            # Récupérer l'employé via son ID
            employee = Employee.objects.get(id=employee_id)
            # Préparer les données à afficher
            context = {
                'employee': employee,
            }

            # Rendre le template avec les informations de l'employé
            return render(request, 'employee_detail.html', context)

        except Employee.DoesNotExist:
            return Response({'error': 'Employé non trouvé'}, status=404)


class CongeViewSet(viewsets.ModelViewSet):
    queryset = Conge.objects.all()
    serializer_class = CongeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtre les congés en fonction des paramètres du GET, incluant
        l’employé, le type de congé, le statut, le poste et le département.
        """
        queryset = super().get_queryset()
        return queryset

    # Lister les congés pour un employé spécifique
    def get_conges_for_employee(self, request, employee_id):
        conges = self.queryset.filter(employee__id=employee_id)
        serializer = CongesDetailSerializer(conges, many=True)
        return Response({'conges': serializer.data}, status=status.HTTP_200_OK)

    # Lister les congés (GET)
    def list(self, request, *args, **kwargs):
        """
        Affiche une liste de congés avec des options de filtrage similaires à PaieViewSet,
        incluant le type de congé, le statut de congé, le poste et le département de l'employé.
        """
        queryset = self.get_queryset()

        # Groupement des congés par mois pour créer les lots

        # Récupération des filtres depuis les paramètres GET
        statut_filter = request.GET.getlist('statut', None)
        date_filter = request.GET.get('date', None)
        employee_filter = request.GET.get('employee', None)
        conge_type_filter = request.GET.get('conge_type', None)
        employee_poste_filter = request.GET.get('employee_poste', None)
        employee_departement_filter = request.GET.get('employee_departement', None)

        # Application des filtres
        if statut_filter:
            queryset = queryset.filter(statut__in=statut_filter)
        if date_filter:
            queryset = queryset.filter(date_debut__date=date_filter)
        if employee_filter:
            queryset = queryset.filter(employee__id=employee_filter)
        if conge_type_filter:
            queryset = queryset.filter(type=conge_type_filter)
        if employee_poste_filter:
            queryset = queryset.filter(employee__poste=employee_poste_filter)
        if employee_departement_filter:
            queryset = queryset.filter(employee__departement=employee_departement_filter)

        # Pagination
        paginator = Paginator(queryset, 10)  # 10 congés par page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Rendre le template HTML avec les données paginées et les filtres appliqués
        return render(request, 'conges_list.html', {
            'conges': page_obj,
            'total_conges': queryset.count(),
            'paginator': paginator,
            'page_obj': page_obj,
            'employees': Employee.objects.all(),  # Récupérer tous les employés pour le filtre
            'statuts': Conge.STATUTS,
            'types_conge': Conge.TYPE_CHOICES,  # Fournir le type de congé pour le filtre
            'postes': Poste.objects.all(),  # Récupérer tous les postes uniques
            'departements': Departement.objects.all(),            # Récupérer tous les départements uniques
        })
        # Renvoyer la réponse avec le template 'conge_list.html' et le contexte
        return TemplateResponse(request, 'conges_list.html', context)
    # Créer un nouveau congé (POST)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            conge = serializer.save()

            # Vérifier si l'employé a suffisamment de jours de congé
            try:
                jours_restants = conge.verifier_jours_restants()
                if jours_restants < 0:
                    return Response({
                        'status': 'error',
                        'message': f"Pas assez de jours de congé pour {conge.employee.nom}."
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer la notification et l'historique
            create_notification(
                user_action=request.user,
                type='demande_conge',
                message=f"Un nouveau congé pour {conge.employee.nom} {conge.employee.prenom} a été créé.",
                user_affected=conge.employee.user
            )

            Historique.objects.create(
                utilisateur=request.user,
                action='create',
                consequence=f"Création d'un congé pour {conge.employee.nom} {conge.employee.prenom}.",
                utilisateur_affecte=conge.employee.user,
                categorie='conge',
                date_action=timezone.now(),
            )

            return Response({
                'status': 'success',
                'message': f"Le congé de {conge.employee.nom} {conge.employee.prenom} a été créé avec succès."
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # Mettre à jour un congé (PUT)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            conge = serializer.save()

            # Créer la notification et l'historique
            create_notification(
                user_action=request.user,
                message=f"Le congé de {conge.employee.nom} a été modifié.",
                user_affected=conge.employee.user
            )

            Historique.objects.create(
                utilisateur=request.user,
                action='update',
                consequence=f"Le congé de {conge.employee.nom} {conge.employee.prenom} a été modifié.",
                utilisateur_affecte=conge.employee.user,
                categorie='conge',
                date_action=timezone.now(),
            )

            return Response({
                'status': 'success',
                'message': f"Le congé de {conge.employee.nom} {conge.employee.prenom} a été modifié avec succès."
            })

        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CongeCreateView(APIView):
    """
    Vue pour la création d'un congé sans serializer. Utilise le template HTML `conges_create.html`.
    """

    def get(self, request):
        if request.user.is_authenticated:
            employee = None
            conges = None
            employees = Employee.objects.all()
            types_conges = Conge.TYPE_CHOICES  # Récupère les choix de types de congés

            if hasattr(request.user, 'employee'):
                employee = request.user.employee
                all_conges = employee.conge_set.all()

                # Pagination des congés
                paginator = Paginator(all_conges, 10)  # 5 congés par page
                page = request.GET.get('page', 1)

                try:
                    conges = paginator.page(page)
                except PageNotAnInteger:
                    conges = paginator.page(1)
                except EmptyPage:
                    conges = paginator.page(paginator.num_pages)

        return render(request, 'conges_create.html', {
            'username': request.user.username,
            'employee': employee,
            'conges': conges,
            'employees': employees,
            'types_conges': types_conges,
            'page_obj': conges,  # On transmet l'objet de pagination
        })

    def post(self, request):
        # Récupération des données du formulaire
        type_conge = request.POST.get('type_conge')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        raison = request.POST.get('raison', "")
        piece_justificatif = request.FILES.get('piece_justificatif')
        employee_id = request.POST.get('employee_id')

        # Récupération de l'employé concerné
        employee = get_object_or_404(Employee, id=employee_id)

        # Validation et calcul des jours demandés
        try:
            date_debut = timezone.datetime.strptime(date_debut, "%Y-%m-%d").date()
            date_fin = timezone.datetime.strptime(date_fin, "%Y-%m-%d").date()
        except ValueError:
            return render(request, 'conges_create.html', {'error': "Les dates de début et de fin sont invalides."})

        jours_utilises = (date_fin - date_debut).days + 1

        # Vérification du nombre de jours maximum pour le type de congé
        max_jours = {
            'ANN': 15, 'FOR': 12, 'MAT': 105, 'PAT': 3, 'EXC': 10, 'OBL': 15
        }
        if jours_utilises > max_jours.get(type_conge, 0):
            return render(request, 'conges_create.html', {'error': "Le nombre de jours dépasse le maximum autorisé."})

        # Vérification des jours restants de l'employé
        jours_disponibles = {
            'ANN': employee.jours_conge_annuels,
            'FOR': employee.jours_conge_formation,
            'MAT': employee.jours_conge_maternite,
            'PAT': employee.jours_conge_paternite,
            'EXC': employee.jours_conge_exceptionnel,
            'OBL': employee.jours_conge_obligatoire,
        }
        jours_restants = jours_disponibles.get(type_conge) - jours_utilises
        if jours_restants < 0:
            return render(request, 'conges_create.html', {'error': "Pas assez de jours restants pour ce congé."})

        # Création du congé
        Conge.objects.create(
            employee=employee,
            type_conge=type_conge,
            date_debut=date_debut,
            date_fin=date_fin,
            raison=raison,
            piece_justificatif=piece_justificatif,
            date_demande=timezone.now()
        )
        return redirect('personnel:conge_create')  # Redirection après création


class CongeUpdateView(APIView):
    """
    Vue pour la mise à jour d'un congé sans serializer. Utilise le template HTML `conges_update.html`.
    """

    def get(self, request, pk):
        # Chargement du congé et affichage du formulaire de mise à jour
        conge = get_object_or_404(Conge, pk=pk)
        return render(request, 'conges_update.html', {'conge': conge})

    def post(self, request, pk):
        # Récupération de l'objet congé existant
        conge = get_object_or_404(Conge, pk=pk)

        # Récupération des données mises à jour depuis le formulaire
        type_conge = request.POST.get('type_conge')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        raison = request.POST.get('raison', "")
        piece_justificatif = request.FILES.get('piece_justificatif', conge.piece_justificatif)

        # Validation des dates
        try:
            date_debut = timezone.datetime.strptime(date_debut, "%Y-%m-%d").date()
            date_fin = timezone.datetime.strptime(date_fin, "%Y-%m-%d").date()
        except ValueError:
            return render(request, 'conges_update.html', {'conge': conge, 'error': "Dates invalides."})

        # Calcul du nombre de jours de congé
        jours_utilises = (date_fin - date_debut).days + 1

        # Vérification du nombre maximum de jours pour le type de congé
        max_jours = {
            'ANN': 15, 'FOR': 12, 'MAT': 105, 'PAT': 3, 'EXC': 10, 'OBL': 15
        }
        if jours_utilises > max_jours.get(type_conge, 0):
            return render(request, 'conges_update.html', {'conge': conge, 'error': "Nombre de jours trop élevé."})

        # Mise à jour des informations du congé
        conge.type_conge = type_conge
        conge.date_debut = date_debut
        conge.date_fin = date_fin
        conge.raison = raison
        conge.piece_justificatif = piece_justificatif
        conge.save()

        return redirect('personnel:conge_create')  # Redirection après mise à jour

class CongeDetailAPIView(APIView):
    def get(self, request, conge_id, *args, **kwargs):
        try:
            # Récupérer l'employé via son ID
            conge = Conge.objects.get(id=conge_id)
            employee = request.user.employee

            # Préparer les données à afficher
            context = {
                'conge': conge,
                'employee': employee
            }

            # Rendre le template avec les informations de l'employé
            return render(request, 'conges_detail.html', context)

        except Conge.DoesNotExist:
            return Response({'error': 'Congé non trouvé'}, status=404)

class CongeDeleteView(APIView):
    """
    Vue pour la suppression d'un congé sans serializer.
    """

    def post(self, request, pk):
        conge = get_object_or_404(Conge, pk=pk)
        conge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApprouverCongeView(APIView):
    permission_classes = [IsAuthenticated]  # Exige que l'utilisateur soit authentifié et a les permission spécifique

    def get(self, request):
        if request.user.is_authenticated:
            employee = None
            conges = None
            employees = Employee.objects.all()
            types_conges = Conge.TYPE_CHOICES  # Récupère les choix de types de salarié
            if hasattr(request.user, 'employee'):
                employee = request.user.employee
                # Filtrer les congés en attente pour l'employé courant
                all_conges = employee.conge_set.filter(statut='en_attente')

                # Pagination des congés
                paginator = Paginator(all_conges, 10)  # 10 congés par page
                page = request.GET.get('page', 1)

                try:
                    conges = paginator.page(page)
                except PageNotAnInteger:
                    conges = paginator.page(1)
                except EmptyPage:
                    conges = paginator.page(paginator.num_pages)

        return render(request, 'conges_manage.html', {
            'username': request.user.username,
            'employee': employee,
            'conges': conges,
            'employees': employees,
            'types_conges': types_conges
        })
    def post(self, request, conge_id, action):

        '''if not request.user.has_perm(
                'personnel.manage_conge'):  # Vérifier si l'utilisateur a la permission 'accept_conge' pour accepter un congé

            return Response({
                'status': 'error',
                'message': "Vous n'avez pas la permission d'accepter ce congé."
            }, status=status.HTTP_403_FORBIDDEN)'''
        conge = get_object_or_404(Conge, id=conge_id)

        if action == 'accepter':

            if not conge.verifier_jours_restants():
                return Response({
                    'status': 'error',
                    'message': f"Impossible d'accepter le congé. Il ne reste pas suffisamment de jours de congé pour "
                               f"{conge.employee.nom}."
                }, status=status.HTTP_400_BAD_REQUEST)

            conge.statut = 'accepte'
            conge.employee.statut = 'C'
            conge.responsable = request.user.employee  # Assignez le responsable, utilisez l'attribut 'employe' de l'utilisateur
            conge.employee.save()
            conge.save()

            create_notification(
                user_action=request.user,
                type='conge_approuve',
                message=f"Le congé de {conge.employee.nom} {conge.employee.prenom} a été accepté par {request.user}.",
                user_affected=conge.employee.user
            )

            Historique.objects.create(
                utilisateur=request.user,
                action='update',
                consequence=f"Une demande de congé de {conge.employee.nom} {conge.employee.prenom} a été approuvée par {request.user}.",
                utilisateur_affecte=conge.employee.user,
                categorie='conge',
                date_action=timezone.now(),
            )

            messages.success(request, f"Le congé de {conge.employee.nom} a été accepté.")
            return redirect('personnel:conge_manage')
        elif action == 'refuser':
            serializer = RefusCongeSerializer(data=request.data)
            if serializer.is_valid():
                reason = serializer.validated_data['reason']
                conge.raison_refus = reason
                conge.statut = 'refuse'
                conge.responsable = request.user.employee  # Assignez le responsable
                conge.save()

                create_notification(
                    user_action=request.user,
                    type='conge_refuse',
                    message=f"Le congé de {conge.employee.nom} a été refusé car {conge.raison_refus}.",
                    user_affected=conge.employee.user
                )

                Historique.objects.create(
                    utilisateur=request.user,
                    action='update',
                    consequence=f"Une demande de congé de {conge.employee.nom} {conge.employee.prenom} "
                                f"a été refusée car {conge.raison_refus}.",
                    utilisateur_affecte=conge.employee.user,
                    categorie='conge',
                    date_action=timezone.now(),
                )

                messages.success(request, f"Le congé de {conge.employee.nom} a été refusé.")
                return redirect('personnel:conge_manage')
            else:
                return Response({
                    'status': 'error',
                    'message': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'error',
            'message': "Action non reconnue."
        }, status=status.HTTP_400_BAD_REQUEST)




class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Récupérer et retourner les notifications de l'utilisateur."""
        notifications = UserNotification.objects.filter(
            user_affected=request.user
        ).select_related('notification').order_by('-notification__date_created')

        serializer = UserNotificationSerializer(notifications, many=True)

        # Rendu du template HTML avec les notifications
        return render(request, 'notification.html', {'notifications': serializer.data})
class HistoriqueListView(APIView):
    permission_classes = [IsAuthenticated]  # Exige que l'utilisateur soit authentifié et a les permission spécifique
    def get(self, request, *args, **kwargs):
        """Récupérer et retourner l'historique en JSON."""
        historiques = Historique.objects.all().order_by('-date_action')
        serializer = HistoriqueSerializer(historiques, many=True)
        return render(request,'historique.html', {'historiques': serializer.data})


def profile_view(request):
    """Vue pour afficher le profil de l'utilisateur connecté avec les congés, et gestion de privileges."""
    if request.user.is_authenticated:
        employee = None
        conges = None
        employees = Employee.objects.all()
        types_conges = Conge.TYPE_CHOICES  # Récupère les choix de types de salarié
        if hasattr(request.user, 'employee'):
            employee = request.user.employee  # Récupérer l'objet Employee associé à l'utilisateur
            conges = employee.conge_set.all()  # Récupérer tous les congés associés à l'employé


        context = {
            'username': request.user.username,
            'employee': employee,
            'conges': conges,
            'employees': employees,
            'types_conges': types_conges
        }
        return render(request, 'profile.html', context)  # Rendre le template du profil avec le contexte
    return redirect('personnel:login')  # Rediriger vers la page de connexion si non authentifié

# Pour mettre à jour le profil
class ProfileAPIView(APIView):
    """
    APIView pour gérer la mise à jour du profil de l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """Mettre à jour le profil de l'utilisateur connecté."""
        user = request.user  # Récupérer l'utilisateur connecté

        if hasattr(user, 'employee'):
            employee = user.employee  # Récupérer l'objet Employee associé à l'utilisateur
            serializer = EmployeeSerializer(employee, data=request.data)  # Passer les nouvelles données

            if serializer.is_valid():
                serializer.save()  # Enregistrer les données mises à jour
                return Response({'message': 'Profil mis à jour avec succès.'}, status=status.HTTP_200_OK)

            # Si le sérialiseur n'est pas valide, renvoyer les erreurs
            return Response({
                'error': 'Données invalides.',
                'details': serializer.errors  # Détails des erreurs de validation
            }, status=status.HTTP_400_BAD_REQUEST)

        # Si l'utilisateur n'a pas d'objet employee, renvoyer une réponse 404
        return Response({
            'error': 'Aucune information d\'employé trouvée pour cet utilisateur.'
        }, status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        """Récupérer le profil de l'utilisateur connecté pour l'affichage."""
        user = request.user  # Récupérer l'utilisateur connecté

        if hasattr(user, 'employee'):
            try:
                employee = user.employee  # Récupérer l'objet Employee associé à l'utilisateur
                serializer = EmployeeSerializer(employee)  # Sérialiser l'objet Employee
                user_data = serializer.data  # Obtenir les données sérialisées
                user_data['username'] = user.username  # Ajouter le username

                return Response({'user': user_data}, status=status.HTTP_200_OK)

            except Exception as e:
                # Gérer les erreurs lors de la sérialisation
                return Response({
                    'error': 'Erreur lors de la récupération des données de l\'employé.',
                    'details': str(e)  # Détails de l'erreur
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Si l'utilisateur n'a pas d'objet employee, renvoyer une réponse 404
        return Response({
            'error': 'Aucune information d\'employé trouvée pour cet utilisateur.'
        }, status=status.HTTP_404_NOT_FOUND)


class CustomPasswordChangeView(APIView):
    """
    APIView pour gérer le changement de mot de passe de l'utilisateur.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Récupération des mots de passe depuis la requête
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # Vérifiez si l'ancien mot de passe est correct
        if not check_password(old_password, request.user.password):
            return render(request, 'settings.html', {
                'error': "L'ancien mot de passe est incorrect."
            }, status=400)

        # Mettre à jour le mot de passe de l'utilisateur
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)

        # Enregistrer l'historique du changement de mot de passe
        Historique.objects.create(
            utilisateur=request.user,
            action='update',
            consequence=f"{request.user.username} a mis à jour son mot de passe.",
            utilisateur_affecte=request.user,
            categorie='employe',
            date_action=timezone.now(),
        )

        # Retourner une réponse de succès
        return render(request, 'settings.html', {
            'success': 'Mot de passe mis à jour avec succès.'
        }, status=200)

    def get(self, request, *args, **kwargs):
        # Si l'utilisateur accède à cette vue avec GET, on redirige vers la page des paramètres
        return render(request, 'settings.html')  # Afficher la page des paramètres

class CustomPasswordChangeDoneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Vous pouvez ajouter des fonctionnalités supplémentaires ici si nécessaire
        return Response({'message': 'Changement de mot de passe terminé', 'status': 'success'}, status=status.HTTP_200_OK)

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination  # Utilise la pagination personnalisée
    # Spécifie que cette vue peut rendre du HTML
    renderer_classes = [TemplateHTMLRenderer]

    @action(detail=False, methods=['GET', 'POST'])
    def create_schedule_form(self, request, *args, **kwargs):

        # Pour les requêtes GET, on récupère les choix pour les départements et les postes
        employees = Employee.objects.all()
        days = Schedule.DAY_CHOICES
        return Response({
            'employees': employees,
            'days': days,
        }, template_name='calendrier_create.html')

    def perform_create(self, serializer):
        schedule = serializer.save()

        # Créer une notification pour l'ajout d'un emploi du temps
        create_notification(
            user_action=self.request.user,
            type='schedule_create',
            message=f"Un nouvel emploi du temps a été ajouté pour {schedule.employee.nom} {schedule.employee.prenom} par {self.request.user}.",
            user_affected=schedule.employee.user  # Associez la notification à l'utilisateur affecté
        )

        # Créer un historique de l'ajout de l'emploi du temps
        Historique.objects.create(
            utilisateur=self.request.user,
            action='create',
            consequence=f"Ajout d'un emploi du temps pour {schedule.employee.nom} {schedule.employee.prenom} par {self.request.user}.",
            utilisateur_affecte=schedule.employee.user,
            categorie='emploi_du_temps',
            date_action=timezone.now(),
        )

        # Lors de la mise à jour d'un emploi du temps

    def perform_update(self, serializer):
        schedule = serializer.save()

        # Créer une notification pour la mise à jour de l'emploi du temps
        create_notification(
            user_action=self.request.user,
            message=f"L'emploi du temps de {schedule.employee.nom} {schedule.employee.prenom} a été modifié.",
            user_affected=schedule.employee.user  # Associez la notification à l'utilisateur affecté
        )

        # Créer un historique de la mise à jour de l'emploi du temps
        Historique.objects.create(
            utilisateur=self.request.user,
            action='update',
            consequence=f"Mise à jour de l'emploi du temps pour {schedule.employee.nom} {schedule.employee.prenom}.",
            utilisateur_affecte=schedule.employee.user,
            categorie='emploi_du_temps',
            date_action=timezone.now(),
        )

    def list(self, request, *args, **kwargs):
        """Récupérer et retourner la liste des emplois du temps en JSON avec filtrage."""
        # Récupérer tous les horaires
        queryset = Schedule.objects.select_related('employee')

        # Appliquer les filtres
        employee_department = request.GET.getlist('departement')
        employee_type = request.GET.getlist('type_salarie')
        employee_poste = request.GET.getlist('poste')
        location = request.GET.getlist('schedule')
        day = request.GET.get('day')

        # Filtrer par département
        if employee_department:
            queryset = queryset.filter(employee__department__id__in=employee_department)

        # Filtrer par type d'employé
        if employee_type:
            queryset = queryset.filter(employee__type__in=employee_type)

        # Filtrer par poste
        if employee_poste:
            queryset = queryset.filter(employee__poste__id__in=employee_poste)

        # Filtrer par lieu
        if location:
            queryset = queryset.filter(location__id__in=location)

        # Filtrer par jour
        if day:
            queryset = queryset.filter(jour_debut__icontains=day)  # Vous pouvez ajuster cela selon votre logique

        # Sérialiser les horaires
        serializer = ScheduleListSerializer(queryset, many=True)

        # Créer un dictionnaire pour stocker les résultats
        schedules_dict = {}

        # Paginer le queryset
        paginator = CustomPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        total_emploiedutemps = queryset.count()

        # Regrouper les horaires par employé
        for schedule in serializer.data:
            employee_id = f"{schedule['employee_first_name']} {schedule['employee_last_name']}"
            if employee_id not in schedules_dict:
                schedules_dict[employee_id] = {
                    'employee_photo': schedule['employee_photo'],
                    'employee_nom': schedule['employee_first_name'],
                    'employee_prenom': schedule['employee_last_name'],
                    'employee_poste': schedule['employee_poste'],
                    'employee_type_salarie': schedule['employee_type'],
                    'employee_departement': schedule['employee_department'],
                    'schedules': []  # Initialiser une liste pour les horaires
                }
            # Ajouter les horaires sans les imbriquer dans une liste supplémentaire
            schedules_dict[employee_id]['schedules'].append({
                'start_time': schedule['start_time'],
                'end_time': schedule['end_time'],
                'jour_debut': schedule['jour_debut'],
                'jour_fin': schedule['jour_fin'],
                'location': schedule['location']
            })

        num_pages = paginator.page.paginator.num_pages if paginator.page else None

        return render(request, 'calendrier_list.html', {
            'schedules': schedules_dict,
            'num_pages': num_pages,
            'paginator': paginator,
            'page_obj': paginator.page,
            'total_emploiedutemps': total_emploiedutemps,
        })


class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Récupérer la notification pour l'utilisateur connecté
        user_notification = get_object_or_404(UserNotification, pk=pk,
                                            user_affected=request.user)

        # Marquer la notification comme lue
        user_notification.is_read = True
        user_notification.save()

        # Rediriger vers la page des notifications
        return redirect('personnel:notifications_list')

    def post(self, request, pk):
        # Même logique que pour GET
        user_notification = get_object_or_404(UserNotification, pk=pk,
                                            user_affected=request.user)

        user_notification.is_read = True
        user_notification.save()

        # Vérifier si c'est une requête AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return Response({'success': True, 'message': 'Notification marquée comme lue.'},
                          status=status.HTTP_200_OK)

        # Sinon, rediriger vers la page des notifications
        return redirect('personnel:notifications_list')

class SettingsView(LoginRequiredMixin, View):
    """Affichage et mise à jour des paramètres de l'utilisateur."""

    template_name = 'settings.html'  # Template à rendre

    def get(self, request, *args, **kwargs):
        """Afficher la page de paramètres avec les données actuelles."""
        employee = request.user.employee  # Récupérer l'employé lié à l'utilisateur connecté
        settings = get_object_or_404(UserSettings, user=request.user)  # Récupérer les paramètres

        # Injecter les données de l'employé et les paramètres dans le template
        context = {
            'employee': employee,
            'settings': {
                'language': settings.language,
                'theme': settings.theme,
                'receive_desktop_notifications': settings.receive_desktop_notifications,
                'receive_email_notifications': settings.receive_email_notifications,
            }
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Mettre à jour les paramètres lorsque l'utilisateur soumet le formulaire."""
        employee = request.user.employee
        settings = get_object_or_404(UserSettings, user=request.user)

        # Récupérer les données du formulaire
        language = request.POST.get('language')
        theme = request.POST.get('theme')
        receive_desktop_notifications = request.POST.get('receive_desktop_notifications') == 'on'
        receive_email_notifications = request.POST.get('receive_email_notifications') == 'on'

        # Mettre à jour les paramètres
        if language:
            settings.language = language
            activate(settings.language)  # Changer la langue de l'utilisateur

        if theme:
            settings.theme = theme

        settings.receive_desktop_notifications = receive_desktop_notifications
        settings.receive_email_notifications = receive_email_notifications
        settings.save()

        # Utiliser les messages pour le feedback utilisateur
        messages.success(request, 'Paramètres mis à jour avec succès !')

        # Retourner à la page des paramètres après mise à jour
        return redirect('personnel:settings')  # Remplacez 'settings' par le nom de votre URL

class AgendaEventViewSet(viewsets.ModelViewSet):
    queryset = AgendaEvent.objects.all()
    serializer_class = AgendaEventSerializer
    permission_classes = [AgendaEventPermission]

    def perform_create(self, serializer):
        # Enregistrez l'événement dans la base de données
        event = serializer.save()

        # Créer une notification pour l'ajout d'un événement

        create_global_notification(
            message=f"Un nouvel événement a été ajouté : {event.title} par {self.request.user}.",
        )

        # Créer un historique de l'ajout de l'événement
        Historique.objects.create(
            utilisateur=self.request.user,
            action='create',
            consequence=f"Ajout d'un nouvel événement : {event.title}",
            utilisateur_affecte=self.request.user,  # Assurez-vous que `user` est défini dans votre modèle Event
            categorie='evenement',
            date_action=timezone.now(),
        )

    def perform_update(self, serializer):
        # Enregistrez l'événement dans la base de données
        event = serializer.save()

        # Créer un historique de la mise à jour de l'événement
        Historique.objects.create(
            utilisateur=self.request.user,
            action='update',
            consequence=f"Mise à jour de l'événement : {event.title}",
            utilisateur_affecte=self.request.user,
            categorie='evenement',
            date_action=timezone.now(),
        )

    def perform_destroy(self, instance):
        # Créer un historique de la suppression de l'événement
        Historique.objects.create(
            utilisateur=self.request.user,
            action='delete',
            consequence=f"Suppression de l'événement : {instance.title}",
            utilisateur_affecte=self.request.user,
            categorie='evenement',
            date_action=timezone.now(),
        )

        # Supprimer l'événement
        instance.delete()

class ManageEmployeePermissionsView(APIView):
    permission_classes = [IsAuthenticated]  # Sécurise la vue

    def get(self, request):
        users = CustomUser.objects.all()  # Utilise CustomUser ici
        permissions = Permission.objects.all()  # Récupère toutes les permissions

        # Préparez les données des utilisateurs pour le rendu du template
        user_data = [{
            'id': user.id,
            'username': user.username,
            'permissions': list(user.user_permissions.values_list('id', flat=True)),  # Liste des ID des permissions
        } for user in users]

        # Rendre le template avec les données nécessaires
        return render(request, 'profile_manage_perm.html', {
            'users': user_data,
            'permissions': permissions,  # Liste des permissions
        })

    def post(self, request):
        # Récupérer tous les utilisateurs personnalisés
        for user in CustomUser.objects.all():
            # Utiliser get pour récupérer les permissions de la requête
            user_permissions = request.POST.getlist(f'permissions_{user.id}', [])  # Récupère les permissions ou une liste vide
            user.user_permissions.set(user_permissions)  # Met à jour les permissions
        return Response({'success': True, 'message': 'Permissions mises à jour avec succès.'},
                        status=status.HTTP_200_OK)

class PaieViewSet(viewsets.ModelViewSet):
    queryset = Paie.objects.order_by('-date_creation')
    permission_classes = [PaiePermission]

    @action(detail=False, methods=['GET', 'POST'], renderer_classes=[TemplateHTMLRenderer])
    def create_paie_form(self, request, *args, **kwargs):
        employees = Employee.objects.all()
        types_paie = Paie.TYPE_CHOICES

        return render(request, 'paie_create.html', {
            'employees': employees,
            'types_paie': types_paie
        })

    def list(self, request, *args, **kwargs):
        """Liste paginée des fiches de paie."""
        queryset = self.get_queryset()

        available_lots = (
            queryset
            .annotate(month=TruncMonth('date_creation'))  # TruncMonth pour regrouper par mois
            .values(lot=F('month'))  # Alias pour 'lot' basé sur 'month'
            .distinct()
            .order_by('date_debut')  # Ordre chronologique
        )

        # Filtrage
        lot_filter = request.GET.getlist('lots', None)  # Corrigé pour correspondre au nom du champ
        statut_filter = request.GET.getlist('statut', None)
        date_filter = request.GET.get('date', None)
        employee_filter = request.GET.get('employee', None)

        if statut_filter:
            queryset = queryset.filter(statut__in=statut_filter)
        if lot_filter:
            # Filtrer par lot (mois et année)
            queryset = queryset.filter(date_creation__month__in=[date_debut.month.month for date_debut in available_lots],
                                       date_creation__year__in=[date_debut.month.year for date_debut in available_lots]).distinct()
        if date_filter:
            queryset = queryset.filter(date_creation__date=date_filter)
        if employee_filter:
            queryset = queryset.filter(employee__id=employee_filter)

        # Pagination
        paginator = Paginator(queryset, 10)  # 10 fiches par page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Rendre le template HTML avec les données paginées
        return render(request, 'paie_list.html', {
            'paies': page_obj,
            'types_paie': Paie.TYPE_CHOICES,
            'total_fiche': queryset.count(),
            'messages': messages.get_messages(request),
            'paginator': paginator,
            'page_obj': page_obj,
            'competences': Competence.objects.all(),  # Assurez-vous d'importer Competence
            'employees': Employee.objects.all(),  # Récupérer tous les employés pour le filtre
            'available_lots': available_lots,
        })

    def retrieve(self, request, pk=None):
        """Récupérer le détail d'une fiche de paie."""
        print(f"Récupération de la fiche de paie avec PK: {pk}")  # Debug log
        paie = get_object_or_404(Paie, pk=pk)
        return render(request, 'paie_detail.html', {'paie': paie})

    def create(self, request, *args, **kwargs):
        """Créer une nouvelle fiche de paie et rendre un fichier HTML."""

        # Récupérer les données directement depuis request.POST
        employee_id = request.POST.get('employee')
        date_debut = request.POST.get('periode_debut')
        date_fin = request.POST.get('periode_fin')
        salaire_base = request.POST.get('salaire_base')
        lot = request.POST.get('lot')
        primes = request.POST.get('primes')
        statut = request.POST.get('statut')
        indemnites = request.POST.get('indemnites')
        indice_anciennete = request.POST.get('indice_anciennete')

        # Vérifier que tous les champs nécessaires sont fournis
        if not (
                employee_id and date_debut and date_fin and indice_anciennete and lot and indemnites and primes and statut and salaire_base):
            # Rendre un template HTML avec un message d'erreur
            return render(request, 'paie_create.html', {
                'success': False,
                'message': 'Tous les champs sont obligatoires.',
            })

        try:
            employee = get_object_or_404(Employee, pk=employee_id)

            # Créer une nouvelle fiche de paie
            nouvelle_fiche = Paie.objects.create(
                employee=employee,
                date_debut=date_debut,
                date_fin=date_fin,
                indice_anciennete=indice_anciennete,
                lot=lot,
                statut=statut,
                primes=primes,
                salaire_base=salaire_base,
                indemnites=indemnites
            )

            # Créer la notification pour l'utilisateur de l'employé
            create_notification(
                user_action=request.user,
                message=f"Une fiche de paie a été créée pour {nouvelle_fiche.employee.nom} {nouvelle_fiche.employee.prenom}.",
                user_affected=nouvelle_fiche.employee.user
            )

            # Enregistrer l'historique de la création
            Historique.objects.create(
                utilisateur=request.user,
                action='create',
                consequence=f"Une fiche de paie a été créée par: {request.user} pour {nouvelle_fiche.employee.nom} "
                            f"{nouvelle_fiche.employee.prenom}",
                utilisateur_affecte=nouvelle_fiche.employee.user,
                categorie='paie',
                date_action=timezone.now(),
            )

            # Rendre un template HTML avec un message de succès
            return render(request, 'paie_create.html', {
                'success': True,
                'message': 'Fiche de paie créée avec succès.',
                'nouvelle_fiche': nouvelle_fiche,
            })

        except Exception as e:
            # Rendre un template HTML avec un message d'erreur en cas d'exception
            return render(request, 'paie_create.html', {
                'success': False,
                'message': f'Erreur lors de la création de la fiche de paie: {str(e)}',
            })

    def update(self, request, pk=None):
        """Mettre à jour une fiche de paie existante."""
        paie = get_object_or_404(Paie, pk=pk)
        serializer = PaieSerializer(paie, data=request.data)
        if serializer.is_valid():
            mise_a_jour_fiche = serializer.save()

            # Créer une notification pour la mise à jour de la fiche de paie
            create_notification(
                user_action=request.user,
                message=f"La fiche de paie de {mise_a_jour_fiche.employee.nom} {mise_a_jour_fiche.employee.prenom} a été modifiée.",
                user_affected=mise_a_jour_fiche.employee.user  # Notification pour l'utilisateur de l'employé
            )

            # Créer un historique de la mise à jour de la fiche de paie
            Historique.objects.create(
                utilisateur=request.user,
                action='update',
                consequence=f"La fiche de paie a été mise à jour par: {request.user} pour {mise_a_jour_fiche.employee.nom} "
                            f"{mise_a_jour_fiche.employee.prenom}",
                utilisateur_affecte=mise_a_jour_fiche.employee.user,
                categorie='paie',
                date_action=timezone.now(),
            )

            return Response({'success': True, 'message': 'Fiche de paie mise à jour avec succès.'},
                            status=status.HTTP_200_OK)

        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

############################## vue pour la fiche de paie séparer #######################
class CreatePaieView(APIView):
    def get(self, request):
        employees = Employee.objects.all()
        types_paie = Paie.TYPE_CHOICES
        return render(request, 'paie_create.html', {
            'employees': employees,
            'types_paie': types_paie
        })

    def post(self, request):
        # Création de la fiche de paie
        try:
            # Récupération des données de la requête POST
            employee_id = request.POST.get('employee_id')
            salaire_base = request.POST.get('salaire_base')
            date_debut = request.POST.get('date_debut')
            date_fin = request.POST.get('date_fin')
            indemnite_transport = request.POST.get('indemnite_transport', 0)
            indemnite_communication = request.POST.get('indemnite_communication', 0)
            indemnite_stage = request.POST.get('indemnite_stage', 0)
            net_a_payer = request.POST.get('net_a_payer', 0)
            statut = request.POST.get('statut', 'En attente')

            # Validation des champs nécessaires
            if not all([employee_id, salaire_base, date_debut, date_fin]):
                return Response({'success': False, 'message': 'Tous les champs sont obligatoires.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Récupération de l'employé
            employee = get_object_or_404(Employee, pk=employee_id)

            paie = Paie(
                employee=employee,
                salaire_base=salaire_base,
                indemnite_transport=indemnite_transport,
                indemnite_communication=indemnite_communication,
                indemnite_stage=indemnite_stage,
                date_debut=date_debut,
                date_fin=date_fin,
                statut=statut,
                net_a_payer=net_a_payer
            )

            # Enregistrer l'instance pour obtenir un ID (clé primaire)
            paie.save()  # Assurez-vous que cette ligne est exécutée avant d'essayer de créer des Prime
            print("hello")  # Pour le débogage

            # Ajouter des primes associées à l'instance de Paie
            primes_nom = request.POST.getlist('prime_nom[]')  # Récupération des noms des primes
            primes_montant = request.POST.getlist('prime_montant[]')  # Récupération des montants des primes

            # Boucle pour créer chaque prime
            for nom, montant in zip(primes_nom, primes_montant):
                if nom and montant:  # Vérification que les noms et montants ne sont pas vides
                    Prime.objects.create(paie=paie, nom=nom, montant=montant)

            # Créer une notification pour la création de la fiche de paie
            create_notification(
                user_action=request.user,
                type='paie_create',
                message=f"La fiche de paie de {paie.employee.nom} {paie.employee.prenom} a été créée.",
                user_affected=paie.employee.user
            )
            Historique.objects.create(
                utilisateur=request.user,
                action='update',
                consequence=f"La fiche de paie a été mise à jour par: {request.user} pour {paie.employee.nom} {paie.employee.prenom}",
                utilisateur_affecte=paie.employee.user,
                categorie='paie',
                date_action=timezone.now(),
            )

            # Rediriger vers la liste des fiches de paie
            return redirect('personnel:payroll-list')

        except Exception as e:
            return Response({'success': False, 'message': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdatePaieView(APIView):
    def get(self, request, pk):
        # Récupérer la fiche de paie à mettre à jour
        paie = get_object_or_404(Paie, pk=pk)
        employees = Employee.objects.all()
        types_paie = Paie.TYPE_CHOICES

        return render(request, 'paie_update.html', {
            'paie': paie,
            'employees': employees,
            'types_paie': types_paie
        })

    def post(self, request, pk):
        # Récupérer la fiche de paie à mettre à jour
        paie = get_object_or_404(Paie, pk=pk)

        try:
            # Récupération des données de la requête POST
            employee_id = request.POST.get('employee_id', paie.employee.id)
            salaire_base = request.POST.get('salaire_base', paie.salaire_base)
            date_debut = request.POST.get('date_debut', paie.date_debut)
            date_fin = request.POST.get('date_fin', paie.date_fin)
            indemnite_transport = request.POST.get('indemnite_transport', paie.indemnite_transport)
            indemnite_communication = request.POST.get('indemnite_communication', paie.indemnite_communication)
            indemnite_stage = request.POST.get('indemnite_stage', paie.indemnite_stage)
            statut = request.POST.get('statut', paie.statut)
            net_a_payer = request.POST.get('net_a_payer', paie.net_a_payer)
            # Validation des champs nécessaires
            if not all([employee_id, salaire_base, date_debut, date_fin]):
                return Response({'success': False, 'message': 'Tous les champs sont obligatoires.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Récupération de l'employé
            employee = get_object_or_404(Employee, pk=employee_id)

            # Mettre à jour l'instance de Paie
            paie.employee = employee
            paie.salaire_base = salaire_base
            paie.indemnite_transport = indemnite_transport
            paie.indemnite_communication = indemnite_communication
            paie.indemnite_stage = indemnite_stage
            paie.date_debut = date_debut
            paie.date_fin = date_fin
            paie.statut = statut
            paie.net_a_payer = net_a_payer
            # Enregistrer les modifications
            paie.save()

            # Supprimer les anciennes primes si nécessaire
            paie.primes.all().delete()

            # Ajouter des primes associées à l'instance de Paie
            primes_nom = request.POST.getlist('prime_nom[]')  # Récupération des noms des primes
            primes_montant = request.POST.getlist('prime_montant[]')  # Récupération des montants des primes

            # Boucle pour créer chaque prime
            for nom, montant in zip(primes_nom, primes_montant):
                if nom and montant:  # Vérification que les noms et montants ne sont pas vides
                    Prime.objects.create(paie=paie, nom=nom, montant=montant)

            # Créer une notification pour la mise à jour de la fiche de paie
            create_notification(
                user_action=request.user,
                type='paie_update',
                message=f"La fiche de paie de {paie.employee.nom} {paie.employee.prenom} a été mise à jour.",
                user_affected=paie.employee.user
            )
            Historique.objects.create(
                utilisateur=request.user,
                action='update',
                consequence=f"La fiche de paie a été mise à jour par: {request.user} pour {paie.employee.nom} {paie.employee.prenom}",
                utilisateur_affecte=paie.employee.user,
                categorie='paie',
                date_action=timezone.now(),
            )

            # Rediriger vers la liste des fiches de paie
            return redirect('personnel:payroll-list')

        except Exception as e:
            return Response({'success': False, 'message': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ViewPaieView(APIView):
    def get(self, request, pk):
        # Récupérer la fiche de paie à mettre à jour
        paie = get_object_or_404(Paie, pk=pk)

        return render(request, 'paie_detail.html', {
            'paie': paie,
        })


class DeletePaieView(APIView):
    def get(self, request, pk):
        paie = get_object_or_404(Paie, pk=pk)
        employee_name = f"{paie.employee.nom} {paie.employee.prenom}"

        # Supprimer la fiche de paie
        paie.delete()

        # Création de la notification et de l'historique (tu peux les adapter comme tu veux)
        create_notification(
            user_action=request.user,
            type='paie_delete',
            message=f"La fiche de paie de {employee_name} a été supprimée.",
            user_affected=paie.employee.user
        )

        Historique.objects.create(
            utilisateur=request.user,
            action='delete',
            consequence=f"La fiche de paie a été supprimée par: {request.user} pour {employee_name}",
            utilisateur_affecte=paie.employee.user,
            categorie='paie',
            date_action=timezone.now(),
        )

        # Rediriger vers la liste des fiches de paie après suppression
        return redirect('personnel:payroll-list')  # Adapte cette ligne selon ton nom de route

class DupliquerFicheDePaieAPIView(APIView):
    """
    Vue pour dupliquer une fiche de paie et créer une nouvelle instance .

    """

    def get(self, request, pk):
        # Récupérer la fiche de paie à mettre à jour
        paie = get_object_or_404(Paie, pk=pk)
        employees = Employee.objects.all()
        types_paie = Paie.TYPE_CHOICES

        return render(request, 'paie_create.html', {
            'paie': paie,
            'employees': employees,
            'types_paie': types_paie
        })

    def post(self, request, pk):
        # La logique de création de fiche de paie avec un pk spécifié
        try:
            # Récupération des données de la requête POST
            employee_id = request.POST.get('employee_id')
            salaire_base = request.POST.get('salaire_base')
            date_debut = request.POST.get('date_debut')
            date_fin = request.POST.get('date_fin')
            indemnite_transport = request.POST.get('indemnite_transport', 0)
            indemnite_communication = request.POST.get('indemnite_communication', 0)
            indemnite_stage = request.POST.get('indemnite_stage', 0)
            net_a_payer = request.POST.get('net_a_payer', 0)
            statut = request.POST.get('statut', 'En attente')

            # Validation des champs nécessaires
            if not all([employee_id, salaire_base, date_debut, date_fin]):
                return Response({'success': False, 'message': 'Tous les champs sont obligatoires.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Récupération de l'employé
            employee = get_object_or_404(Employee, pk=employee_id)

            # Récupérer la fiche de paie à dupliquer
            paie_to_duplicate = get_object_or_404(Paie, pk=pk)

            paie = Paie(
                employee=employee,
                salaire_base=salaire_base,
                indemnite_transport=indemnite_transport,
                indemnite_communication=indemnite_communication,
                indemnite_stage=indemnite_stage,
                date_debut=date_debut,
                date_fin=date_fin,
                statut=statut,
                net_a_payer=net_a_payer
            )

            # Enregistrer l'instance pour obtenir un ID (clé primaire)
            paie.save()  # Assurez-vous que cette ligne est exécutée avant d'essayer de créer des Prime

            # Ajouter des primes associées à l'instance de Paie
            primes_nom = request.POST.getlist('prime_nom[]')  # Récupération des noms des primes
            primes_montant = request.POST.getlist('prime_montant[]')  # Récupération des montants des primes

            # Boucle pour créer chaque prime
            for nom, montant in zip(primes_nom, primes_montant):
                if nom and montant:  # Vérification que les noms et montants ne sont pas vides
                    Prime.objects.create(paie=paie, nom=nom, montant=montant)

            # Créer une notification pour la création de la fiche de paie
            create_notification(
                user_action=request.user,
                type='paie_create',
                message=f"La fiche de paie de {paie.employee.nom} {paie.employee.prenom} a été créée.",
                user_affected=paie.employee.user
            )
            Historique.objects.create(
                utilisateur=request.user,
                action='update',
                consequence=f"La fiche de paie a été mise à jour par: {request.user} pour {paie.employee.nom} {paie.employee.prenom}",
                utilisateur_affecte=paie.employee.user,
                categorie='paie',
                date_action=timezone.now(),
            )

            # Rediriger vers la liste des fiches de paie
            return redirect('personnel:payroll-list')

        except Exception as e:
            return Response({'success': False, 'message': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class ExportFicheDePaiePDFView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, id):
#         """Exporter la fiche de paie en PDF."""
#         fiche = get_object_or_404(Paie, id=id)

#         try:
#             # Obtenir le template HTML
#             template = get_template('paie_export_pdf.html')
#             image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Employee', 'mada.png')
#             with open(image_path, 'rb') as image_file:
#                 image_data = base64.b64encode(image_file.read()).decode('utf-8')

#             # Rendre le template HTML avec les données de la fiche de paie
#                 # ... (début du code identique)

#                 html = f""" 
#                         <!DOCTYPE html>
#                         <html lang="fr">
#                         <head>
#                             <meta charset="UTF-8">
#                             <title>Fiche de paie</title>
#                         </head>
#                         <body>
#                             <div class="container">
#                                 <div class="header">
#                                     <h1>Fiche de Paie - {fiche.date_debut.strftime("%B %Y")}</h1>
#                                 </div>

#                                 <div class="main-content">
#                                     <div class="info-section">
#                                         <div class="employee-header">
#                                             <h2>Informations Employé</h2>
#                                             <p class="employee-id">ID: {fiche.employee.id:05d}</p>
#                                         </div>
#                                         <div class="employee-details">
#                                             <div class="name-section">
#                                                 <span class="label">Nom :</span>
#                                                 <span class="value">{fiche.employee.nom} {fiche.employee.prenom}</span>
#                                                 <div class="poste">{fiche.employee.poste}</div>
#                                             </div>
#                                             <div class="dates">
#                                                 <div>
#                                                     <span class="label">Période du</span>
#                                                     <span class="value">{fiche.date_debut.strftime("%d/%m/%Y")}</span>
#                                                 </div>
#                                                 <div>
#                                                     <span class="label">au</span>
#                                                     <span class="value">{fiche.date_fin.strftime("%d/%m/%Y")}</span>
#                                                 </div>
#                                             </div>
#                                         </div>
#                                     </div>

#                                     <div class="pay-details">
#                                         <h2>Détails de la Paie</h2>
#                                         <div class="pay-grid">
#                                             <div class="pay-item">
#                                                 <span class="label">Salaire de base</span>
#                                                 <span class="amount">{fiche.salaire_base:,.2f} MGA</span>
#                                             </div>
#                                             <div class="pay-item">
#                                                 <span class="label">Indemnité Transport</span>
#                                                 <span class="amount">{fiche.indemnite_transport:,.2f} MGA</span>
#                                             </div>
#                                             <div class="pay-item">
#                                                 <span class="label">Indemnité Communication</span>
#                                                 <span class="amount">{fiche.indemnite_communication:,.2f} MGA</span>
#                                             </div>
#                                             <div class="pay-item">
#                                                 <span class="label">Indemnité Stage</span>
#                                                 <span class="amount">{fiche.indemnite_stage:,.2f} MGA</span>
#                                             </div>
#                                         </div>
#                                     </div>

#                                     <div class="primes-section">
#                                         <h2>Primes</h2>
#                                         <table>
#                                             <thead>
#                                                 <tr>
#                                                     <th>Désignation</th>
#                                                     <th>Montant (MGA)</th>
#                                                 </tr>
#                                             </thead>
#                                             <tbody>
#                                                 {''.join([f"""
#                                                     <tr>
#                                                         <td>{prime.nom}</td>
#                                                         <td class="amount">{prime.montant:,.2f}</td>
#                                                     </tr>
#                                                 """ for prime in fiche.primes.all()]) if fiche.primes.exists() else
#                 '<tr><td colspan="2" class="no-prime">Aucune prime</td></tr>'}
#                                             </tbody>
#                                         </table>
#                                     </div>

#                                     <div class="total-section">
#                                         <span class="label">Net à Payer :</span>
#                                         <span class="total-amount">{fiche.net_a_payer:,.2f} MGA</span>
#                                     </div>

#                                     <div class="signature-section">
#                                         <div class="signature-box">
#                                             <p>Le Directeur</p>
#                                             <div class="signature-line">Date et Signature</div>
#                                         </div>
#                                         <div class="signature-box">
#                                             <p>Le Salarié</p>
#                                             <div class="signature-line">Date et Signature</div>
#                                         </div>
#                                     </div>
#                                 </div>

#                                 <div class="footer">
#                                     <img src="data:image/png;base64,{image_data}" alt="logo">
#                                     <p>Ce fiche de payé a été généré le { fiche.date_creation.strftime("%d/%m/%Y")}</p>
#                                 </div>
#                             </div>
#                         </body>
#                         </html>
#                         """

#                 css = CSS(string='''
#                             @page {
#                                 size: A4;
#                                 margin: 1.5cm;
#                             }

#                             body {
#                                 font-family: Arial, sans-serif;
#                                 margin: 0;
#                                 padding: 0;
#                                 font-size: 10pt;
#                             }

#                             .container {
#                                 background: white;
#                             }

#                             .header {
#                                 background: #FB923C;
#                                 color: white;
#                                 padding: 15px;
#                                 margin-bottom: 20px;
#                             }

#                             .header h1 {
#                                 margin: 0;
#                                 font-size: 16pt;
#                                 text-align: center;
#                             }

#                             .main-content {
#                                 padding: 0 15px;
#                             }

#                             .info-section {
#                                 margin-bottom: 20px;
#                             }

#                             .employee-header {
#                                 display: flex;
#                                 justify-content: space-between;
#                                 align-items: center;
#                                 border-bottom: 2px solid #1a237e;
#                                 margin-bottom: 10px;
#                             }

#                             .employee-header h2 {
#                                 margin: 0;
#                                 font-size: 12pt;
#                                 color: #1a237e;
#                             }

#                             .employee-details {
#                                 display: grid;
#                                 grid-template-columns: 1fr 1fr;
#                                 gap: 20px;
#                             }

#                             .name-section .value {
#                                 font-weight: bold;
#                                 font-size: 11pt;
#                             }

#                             .poste {
#                                 color: #666;
#                                 font-size: 9pt;
#                                 margin-top: 3px;
#                             }

#                             .pay-details {
#                                 margin: 20px 0;
#                             }

#                             .pay-grid {
#                                 display: grid;
#                                 grid-template-columns: repeat(2, 1fr);
#                                 gap: 10px;
#                             }

#                             .pay-item {
#                                 display: flex;
#                                 justify-content: space-between;
#                                 padding: 5px 0;
#                                 border-bottom: 1px solid #eee;
#                             }

#                             .amount {
#                                 font-weight: bold;
#                                 text-align: right;
#                             }

#                             table {
#                                 width: 100%;
#                                 border-collapse: collapse;
#                                 margin: 10px 0;
#                             }

#                             th, td {
#                                 padding: 8px;
#                                 border: 1px solid #ddd;
#                                 text-align: left;
#                             }

#                             th {
#                                 background: #f5f5f5;
#                             }

#                             .total-section {
#                                 display: flex;
#                                 justify-content: space-between;
#                                 align-items: center;
#                                 margin: 20px 0;
#                                 padding: 10px;
#                                 background: #f8f9fa;
#                                 border-radius: 4px;
#                             }

#                             .total-amount {
#                                 font-size: 14pt;
#                                 font-weight: bold;
#                                 color: #1a237e;
#                             }

#                             .signature-section {
#                                 display: grid;
#                                 grid-template-columns: 1fr 1fr;
#                                 gap: 40px;
#                                 margin: 20px 0;
#                             }

#                             .signature-box {
#                                 text-align: center;
#                             }

#                             .signature-line {
#                                 margin-top: 40px;
#                                 border-top: 1px solid #000;
#                                 padding-top: 5px;
#                             }

                        
# .footer {
#     position: fixed;
#     bottom: 20px;
#     right: 20px;
#     text-align: right;
#     padding: 10px;
# }

# .footer img {
#     height: 80px;
#     width: auto;
#     display: block;
#     margin-left: auto;  /* Aligne l'image à droite */
# }

# .footer p {
#     margin: 5px 0 0;
#     font-size: 8pt;
#     color: #666;
# }
# ''')
#             # Initialiser la réponse HTTP avec le type de contenu PDF
#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = (
#                 f'attachment; filename="fiche_de_paie_de_{fiche.employee.nom}_{fiche.employee.prenom}_{fiche.exercice}.pdf"'
#             )

            
#             # Générer le PDF à partir du contenu HTML avec WeasyPrint
#             HTML(string=html).write_pdf(
#                 response,
#                 stylesheets=[css]
#                   )

#             # Enregistrer l'action dans l'historique
#             Historique.objects.create(
#                 utilisateur=request.user,
#                 action='export',
#                 consequence=f"Une fiche de paie de {fiche.employee.nom} {fiche.employee.prenom} a été exportée",
#                 utilisateur_affecte=fiche.employee.user,
#                 categorie='paie',
#                 date_action=timezone.now(),
#             )

#             # Retourner la réponse PDF
#             return response

#         except Exception as e:
#             # Gestion de l'erreur avec un message explicatif
#             return Response({'error': f"Une erreur est survenue lors de la génération du PDF : {str(e)}"},
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExportDatabaseView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Récupérer le nom de la table depuis la requête POST
        table = request.POST.get('table')

        # Créer le chemin pour le fichier de sauvegarde
        if table == 'all':
            backup_file_path = os.path.join(settings.BASE_DIR, 'full_database_backup.sql')
        else:
            backup_file_path = os.path.join(settings.BASE_DIR, f'{table}_backup.sql')

        # Informations sur la base de données
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD']
        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT'] or '3306'  # Par défaut, le port MySQL est 3306

        # Vérifier si la table fait partie des tables que tu veux exporter ou si c'est "Tout exporter"
        allowed_tables = [
            'personnel_employee',
            'personnel_paie',
            'personnel_conge',
            'personnel_schedule',
        ]

        try:
            # Si l'utilisateur veut tout exporter, utilise mysqldump pour toute la base de données
            if table == 'all':
                # Exporter toute la base de données
                with open(backup_file_path, 'w') as output_file:
                    os.putenv('MYSQL_PWD', db_password)  # Mettre le mot de passe dans l'environnement pour mysqldump
                    subprocess.run(
                        ['mysqldump', '-u', db_user, '-h', db_host, '-P', db_port, db_name],
                        stdout=output_file
                    )
                # Lire le fichier et créer une réponse pour le téléchargement
                with open(backup_file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/sql')
                    response['Content-Disposition'] = 'attachment; filename="full_database_backup.sql"'
                    return response

            # Si l'utilisateur veut exporter une table spécifique
            elif table in allowed_tables:
                # Exporter la table spécifique
                with open(backup_file_path, 'w') as output_file:
                    os.putenv('MYSQL_PWD', db_password)
                    subprocess.run(
                        ['mysqldump', '-u', db_user, '-h', db_host, '-P', db_port, db_name, table],
                        stdout=output_file
                    )
                # Lire le fichier et créer une réponse pour le téléchargement
                with open(backup_file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/sql')
                    response['Content-Disposition'] = f'attachment; filename="{table}_backup.sql"'
                    return response

            else:
                return HttpResponse(f"Table '{table}' non autorisée pour l'exportation.", status=400)

        except Exception as e:
            return HttpResponse(f"Erreur lors de l'export de la base de données: {str(e)}", status=500)