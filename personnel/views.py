from django.contrib.auth.hashers import check_password
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash, get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils.translation import activate
from django.contrib.auth.models import Permission, User
from rest_framework.generics import UpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from xhtml2pdf import pisa
from .models import Employee, Conge, Notification, Historique, Schedule, UserSettings, AgendaEvent, Paie, \
    UserNotification
from .serializers import RefusCongeSerializer, EmployeeSerializer, CongeSerializer, CongesDetailSerializer, \
    NotificationSerializer, ScheduleSerializer, SettingsSerializer, AgendaEventSerializer, HistoriqueSerializer, \
    ScheduleListSerializer, PaieSerializer, LoginSerializer, UserNotificationSerializer
from .services import create_notification, create_global_notification

CustomUser = get_user_model()

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Exige que l'utilisateur soit authentifié

    def get(self, request, *args, **kwargs):
        # Récupérer les informations pour le tableau de bord
        total_salaries = Employee.objects.count()
        salaries_en_conge = Employee.objects.filter(statut='C').count()
        salaries_disponibles = Employee.objects.filter(statut='T').count()
        unread_notifications = UserNotification.objects.filter(user_affected=request.user, is_read=False).select_related('notification').values('notification__user__username', 'notification__message', 'notification__date_created')
        today = timezone.now().date()
        tomorrow = today + timezone.timedelta(days=1)

        today_events = AgendaEvent.objects.filter(start_date__date=today).values('description',
                                                                                 'title',
                                                                                 'start_time',
                                                                                 'start_date')
        tomorrow_events = AgendaEvent.objects.filter(start_date__date=tomorrow).values('description',
                                                                                       'title',
                                                                                        'start_time',
                                                                                         'start_date')

        # Créer le contexte
        context = {
            'total_salaries': total_salaries,
            'salaries_en_conge': salaries_en_conge,
            'salaries_disponibles': salaries_disponibles,
            'unread_notifications': list(unread_notifications),
            'today_events': list(today_events),
            'tomorrow_events': list(tomorrow_events),
        }

        return Response(context)

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


#Les vues
class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour regrouper les actions list, create, et update des employés.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [EmployeePermission]  # Exige que l'utilisateur soit authentifié et a les permission spécifique
    # Liste des employés
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        employees = serializer.data

        # Filtrage personnalisé des employés
        filtered_employees = [
            {
                'photo': emp['photo'],
                'nom': emp['nom'],
                'prenom': emp['prenom'],
                'id': emp['id'],
                'poste': emp['poste'],
                'type_salarie': emp['type_salarie'],
                'statut': emp['statut'],
                'date_embauche': emp['date_embauche'],
                'departement': emp['departement'],
                'email': emp['email'],
            }
            for emp in employees
        ]

        return Response({'employees': filtered_employees})

    # Création d'un employé
    def perform_create(self, serializer):
        employee = serializer.save()

        # Créer une notification pour l'ajout d'un employé
        create_notification(
            user_action=self.request.user,
            message=f"Un nouvel employé {employee.nom} a été ajouté.",
            user_affected=employee.user
        )

        # Créer un historique de l'ajout de l'employé
        Historique.objects.create(
            utilisateur=self.request.user,
            action='create',
            consequence=f"Ajout d'un nouvel employé : {employee.nom} {employee.prenom}",
            utilisateur_affecte=employee.user,
            categorie='employe',
            date_action=timezone.now(),
        )

    # Mise à jour d'un employé
    def perform_update(self, serializer):
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

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        employee = response.data

        return Response({
            'status': 'success',
            'message': f"L'employé {employee['nom']} {employee['prenom']} a été ajouté avec succès."
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        employee = response.data

        return Response({
            'status': 'success',
            'message': f"L'employé {employee['nom']} {employee['prenom']} a été modifié avec succès."
        }, status=status.HTTP_200_OK)

class CongeViewSet(viewsets.ModelViewSet):
    queryset = Conge.objects.all()
    serializer_class = CongeSerializer
    permission_classes = [IsAuthenticated, CongePermission]  # Exige que l'utilisateur soit authentifié et a les permission spécifique

    def get_queryset(self):
        user = self.request.user
        if user.has_perm('personnel.acces_all_conge'):
            return Conge.objects.all()  # Voir tous les congés si l'utilisateur est dans la direction
        return Conge.objects.filter(employee__user=user)  # Sinon, voir seulement ses propres congés

    # Lister les congés pour un employé spécifique
    def get_conges_for_employee(self, request, employee_id):
        conges = self.queryset.filter(employee__id=employee_id)
        serializer = CongesDetailSerializer(conges, many=True)
        return Response({'conges': serializer.data}, status=status.HTTP_200_OK)

    # Lister les congés (GET)
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'conges': serializer.data}, status=status.HTTP_200_OK)

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

class ApprouverCongeView(APIView):
    permission_classes = [IsAuthenticated, CongePermission]  # Exige que l'utilisateur soit authentifié et a les permission spécifique

    def post(self, request, conge_id, action):

        if not request.user.has_perm(
                'personnel.manage_conge'):  # Vérifier si l'utilisateur a la permission 'accept_conge' pour accepter un congé

            return Response({
                'status': 'error',
                'message': "Vous n'avez pas la permission d'accepter ce congé."
            }, status=status.HTTP_403_FORBIDDEN)
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
                message=f"Le congé de {conge.employee.nom} a été accepté.",
                user_affected=conge.employee.user
            )

            Historique.objects.create(
                utilisateur=request.user,
                action='update',
                consequence=f"Une demande de congé de {conge.employee.nom} {conge.employee.prenom} a été approuvée.",
                utilisateur_affecte=conge.employee.user,
                categorie='conge',
                date_action=timezone.now(),
            )

            return Response({
                'status': 'success',
                'message': f"Le congé de {conge.employee.nom} a été accepté."
            }, status=status.HTTP_200_OK)

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

                return Response({
                    'status': 'success',
                    'message': f"Le congé de {conge.employee.nom} a été refusé."
                }, status=status.HTTP_200_OK)
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

        # Passez les objets complets au serializer
        serializer = UserNotificationSerializer(notifications, many=True)
        return Response({'notifications': serializer.data}, status=status.HTTP_200_OK)
class HistoriqueListView(APIView):
    permission_classes = [IsAuthenticated, HistoriquePermission]  # Exige que l'utilisateur soit authentifié et a les permission spécifique
    def get(self, request):
        """Récupérer et retourner l'historique en JSON."""
        historiques = Historique.objects.all().order_by('-date_action')
        serializer = HistoriqueSerializer(historiques, many=True)
        return Response({'historiques': serializer.data}, status=status.HTTP_200_OK)


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated
                          ]
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
        """Récupérer le profil de l'utilisateur connecté."""
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
class LoginView(APIView):
    permission_classes = [AllowAny]  # Autoriser l'accès à tout le monde

    def post(self, request):
        """Gérer la connexion de l'utilisateur."""
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():  # Vérifie si les données sont valides
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)  # Connecter l'utilisateur

                # Créer une notification pour l'utilisateur connecté

                create_notification(
                    user_action=user,
                    type='connexion_reussi',
                    message=f"{user.username} s'est connecté.",
                    user_affected=user
                )

                return Response({'success': True, 'message': 'Connexion réussie.'})
            else:
                return Response({'success': False, 'message': 'Nom d’utilisateur ou mot de passe incorrect.'},
                                status=401)
        else:
            print(serializer.errors)  # Afficher les erreurs
            return Response(serializer.errors, status=400)

    def options(self, request):
        """Gérer la méthode OPTIONS."""
        return Response({'success': False, 'message': 'Méthode non autorisée.'}, status=405)


class CustomLogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Sécurise la vue

    def post(self, request):
        """Gérer la déconnexion de l'utilisateur."""
        logout(request)  # Déconnexion de l'utilisateur

        create_notification(
            user_action=request.user,
            type='deconnexion_reussi',
            message=f"{request.user.username} s'est déconnecté.",
            user_affected=request.user
        )

        return Response({'message': 'Déconnexion réussie'}, status=200)

    def get(self, request):
        """Fournir le token CSRF dans une requête GET."""
        csrf_token = get_token(request)  # Obtenir le token CSRF
        return Response({'csrfToken': csrf_token}, status=200)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log la connexion de l'utilisateur."""
    Historique.objects.create(
        utilisateur=user,
        action='login',
        consequence='Utilisateur connecté',
        categorie='session',
        date_action=timezone.now(),
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log la déconnexion de l'utilisateur."""
    Historique.objects.create(
        utilisateur=user,
        action='logout',
        consequence='Utilisateur déconnecté',
        categorie='session',
        date_action=timezone.now(),
    )

class CustomPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # Vérifiez si le mot de passe ancien est correct
        if not check_password(old_password, request.user.password):
            raise ValidationError("L'ancien mot de passe est incorrect.")

        # Mettre à jour le mot de passe de l'utilisateur
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)  # Maintenir la session active

        # Enregistrer l'historique
        Historique.objects.create(
            utilisateur=request.user,
            action='update',
            consequence=f"{request.user.username} a mis à jour son mot de passe.",
            utilisateur_affecte=request.user,
            categorie='employe',
            date_action=timezone.now(),
        )

        return Response({'message': 'Mot de passe mis à jour avec succès', 'status': 'success'},
                        status=status.HTTP_200_OK)

class CustomPasswordChangeDoneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Vous pouvez ajouter des fonctionnalités supplémentaires ici si nécessaire
        return Response({'message': 'Changement de mot de passe terminé', 'status': 'success'}, status=status.HTTP_200_OK)

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [SchedulePermission]

    def perform_create(self, serializer):
        schedule = serializer.save()

        # Créer une notification pour l'ajout d'un emploi du temps
        create_notification(
            user_action=self.request.user,
            message=f"Un nouvel emploi du temps a été ajouté pour {schedule.employee.nom} {schedule.employee.prenom}.",
            user_affected=schedule.employee.user  # Associez la notification à l'utilisateur affecté
        )

        # Créer un historique de l'ajout de l'emploi du temps
        Historique.objects.create(
            utilisateur=self.request.user,
            action='create',
            consequence=f"Ajout d'un emploi du temps pour {schedule.employee.nom} {schedule.employee.prenom}.",
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
        """Récupérer et retourner la liste des emplois du temps en JSON."""
        # Obtenir tous les horaires
        queryset = Schedule.objects.select_related('employee')

        # Sérialiser les horaires
        serializer = ScheduleListSerializer(queryset, many=True)

        # Créer un dictionnaire pour stocker les résultats
        schedules_dict = {}

        # Regrouper les horaires par employé
        for schedule in serializer.data:
            employee_id = f"{schedule['employee_first_name']} {schedule['employee_last_name']}"
            if employee_id not in schedules_dict:
                schedules_dict[employee_id] = {
                    'employee_photo': schedule['employee_photo'],
                    'employee_first_name': schedule['employee_first_name'],
                    'employee_last_name': schedule['employee_last_name'],
                    'employee_poste': schedule['employee_poste'],
                    'employee_type': schedule['employee_type'],
                    'employee_department': schedule['employee_department'],
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

        # Retourner la réponse formatée
        return Response({'schedules': list(schedules_dict.values())})

class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        # Récupérer la notification pour l'utilisateur connecté
        user_notification = get_object_or_404(UserNotification, notification_id=notification_id,
                                              user_affected=request.user)

        # Marquer la notification comme lue
        user_notification.is_read = True
        user_notification.save()

        return Response({'success': True, 'message': 'Notification marquée comme lue.'}, status=status.HTTP_200_OK)
class SettingsUpdateAPIView(UpdateAPIView):
    queryset = Employee.objects.all()  # Tous les employés, mais nous allons filtrer par utilisateur
    serializer_class = SettingsSerializer
    permission_classes = [IsAuthenticated]  # l'utilisateur est authentifié

    def get_object(self):
        """Récupérer l'employé lié à l'utilisateur connecté."""
        return self.request.user.employee  # Accéder à l'employé lié

    def perform_update(self, serializer):
        """Traiter la mise à jour après la validation."""
        settings = serializer.save()  # Enregistrer les paramètres
        # Gestion de la langue
        activate(settings.language)

    def get(self, request, *args, **kwargs):
        """Récupérer les paramètres de l'utilisateur."""
        employee = self.get_object()  # Récupérer l'employé lié
        settings = get_object_or_404(UserSettings, user=request.user)  # Récupérer les paramètres de l'utilisateur
        serializer = self.get_serializer(employee)  # Sérialiser les données de l'employé
        # Ajouter les paramètres à la réponse
        return Response({
            'employee': serializer.data,
            'settings': {
                'language': settings.language,
                'theme': settings.theme,
                'receive_desktop_notifications': settings.receive_desktop_notifications,
                'receive_email_notifications': settings.receive_email_notifications
            }
        })  # Retourner les données en JSON

    def patch(self, request, *args, **kwargs):
        """Mise à jour partielle des paramètres de l'utilisateur."""
        employee = self.get_object()  # Récupérer l'employé lié
        language = request.data.get('language')
        theme = request.data.get('theme')

        settings = get_object_or_404(UserSettings, user=request.user)  # Récupérer les paramètres de l'utilisateur

        if language:
            settings.language = language
            settings.save()

        if theme:
            settings.theme = theme
            settings.save()

        # Pour les notifications
        receive_desktop_notifications = request.data.get('receive_desktop_notifications')
        if receive_desktop_notifications is not None:
            settings.receive_desktop_notifications = receive_desktop_notifications
            settings.save()

        receive_email_notifications = request.data.get('receive_email_notifications')
        if receive_email_notifications is not None:
            settings.receive_email_notifications = receive_email_notifications
            settings.save()

        return Response({'success': True, 'message': 'Paramètres mis à jour avec succès.'})

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

        # Préparez les données des utilisateurs pour la réponse JSON
        user_data = [{
            'id': user.id,
            'username': user.username,
            'permissions': list(user.user_permissions.values_list('id', flat=True)),  # Liste des ID des permissions
        } for user in users]

        return Response({
            'users': user_data,
            'permissions': list(permissions.values()),  # Liste des permissions
        }, status=status.HTTP_200_OK)

    def post(self, request):
        # Récupérer tous les utilisateurs personnalisés
        for user in CustomUser.objects.all():
            # Utiliser get pour récupérer les permissions de la requête
            user_permissions = request.data.get(f'permissions_{user.id}', [])  # Récupère les permissions ou une liste vide
            user.user_permissions.set(user_permissions)  # Met à jour les permissions
        return Response({'success': True, 'message': 'Permissions mises à jour avec succès.'},
                        status=status.HTTP_200_OK)

class PaiePagination(PageNumberPagination):
    page_size = 10  # Nombre de fiches de paie par page

class PaieViewSet(viewsets.ModelViewSet):
    queryset = Paie.objects.order_by('-date_creation')
    serializer_class = PaieSerializer
    pagination_class = PaiePagination
    permission_classes = [PaiePermission]

    def list(self, request, *args, **kwargs):
        """Liste paginée des fiches de paie."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Récupérer le détail d'une fiche de paie."""
        paie = get_object_or_404(Paie, pk=pk)
        serializer = self.get_serializer(paie)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Créer une nouvelle fiche de paie."""
        serializer = PaieSerializer(data=request.data)
        if serializer.is_valid():
            nouvelle_fiche = serializer.save()

            create_notification(
                user_action=request.user,
                message=f"Une fiche de paie a été créée pour {nouvelle_fiche.employee.nom} {nouvelle_fiche.employee.prenom}.",
                user_affected=nouvelle_fiche.employee.user  # Notification pour l'utilisateur de l'employé
            )

            Historique.objects.create(
                utilisateur=request.user,
                action='create',
                consequence=f"Une fiche de paie a été créée par: {request.user} pour {nouvelle_fiche.employee.nom} "
                            f"{nouvelle_fiche.employee.prenom}",
                utilisateur_affecte=nouvelle_fiche.employee.user,
                categorie='paie',
                date_action=timezone.now(),
            )

            return Response({'success': True, 'message': 'Fiche de paie créée avec succès.'},
                            status=status.HTTP_201_CREATED)

        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

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

class ExportFicheDePaiePDFView(APIView):
    permission_classes = [ExportPaiePermission]
    def get(self, request, id):
        """Exporter la fiche de paie en PDF."""
        fiche = get_object_or_404(Paie, id=id)

        try:
            # Rendre le template HTML avec les données de la fiche de paie
            html = render_to_string('payroll/fiche_de_paie.html', {'fiche': fiche})

            # Initialiser la réponse HTTP avec le type de contenu PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="fiche_de_paie_de_{fiche.employee.nom}_{fiche.employee.prenom}_{fiche.mois}.pdf"'
            )

            # Générer le PDF depuis le contenu HTML
            pisa_status = pisa.CreatePDF(html, dest=response)

            # Vérifier si une erreur est survenue lors de la génération du PDF
            if pisa_status.err:
                raise Exception(f'Erreur lors de la génération du PDF : {pisa_status.err}')

            # Enregistrer l'action dans l'historique
            Historique.objects.create(
                utilisateur=request.user,
                action='export',
                consequence=f"Une fiche de paie de {fiche.employee.nom} {fiche.employee.prenom} a été exportée",
                utilisateur_affecte=fiche.employee.user,
                categorie='paie',
                date_action=timezone.now(),
            )

            # Retourner la réponse PDF
            return response

        except Exception as e:
            # Gestion de l'erreur avec un message explicatif
            return Response({'error': f"Une erreur est survenue lors de la génération du PDF : {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)