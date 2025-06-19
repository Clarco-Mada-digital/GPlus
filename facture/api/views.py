from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from facture.models import Facture, Entreprise, Service
from clients.models import Client
from accounts.models import User

from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from .serializers import FactureSerializer, ClientSerializer, EntrepriseSerializer, UserSerializer, FactureServiceSerializer

class UserViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all()
    
    

class FactureServiceViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FactureServiceSerializer
    
    def get_queryset(self):
        return Service.objects.all().order_by('-id')


class FactureViewset(ModelViewSet):
    """
    FactureViewset: Utilisée pour gérer les factures
    """
    permission_classes = [IsAuthenticated] #! On définit les permissions pour cette vue
    serializer_class = FactureSerializer # Serializer par défaut, pour la List des factures

    def get_queryset(self):
        return Facture.objects.all().order_by('-id') # Toute les factures
    
    # Selectionne le serialiseur adequat
    def get_serializer_class(self):
        return super().get_serializer_class() # /facture/
    
    @action(detail=True, methods=['put'])
    def updateEtat(self, request, pk=None):
        # Recupérer les datas du request body
        new_etat_facture = request.data.get('etat_facture')

        if new_etat_facture is None:
            raise ValidationError("etat_facture non fournis")

        try:
            facture = Facture.objects.get(pk=pk)
        except Facture.DoesNotExist:
            return Response({'error': 'Facture introuvable.'}, status=404)
        
        facture_year = facture.date_facture.year

        facture.ref = FactureSerializer.generate_ref(
            facture_id=pk, 
            facture_year=facture_year,
            etat_facture=new_etat_facture,
            facture_type=facture.type
        )
        facture.etat_facture = new_etat_facture
        facture.updated_at = timezone.now()
        facture.save()

        # print(facture.ref)

        serializer = FactureSerializer(facture)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def actualiseFactures(self, request):
        latest_sync_date_str = request.query_params.get('s_dt')

        # Vérifier si le paramètre est présent
        if not latest_sync_date_str:
            raise ValidationError({"latest_sync_date": "Paramètre obligatoire."})

        # Convertir la date string en datetime
        latest_sync_date = parse_datetime(latest_sync_date_str)
        
        if latest_sync_date is None:
            return Response({"error": "Format de date incorrect"}, status=400)

        # Filtrer les factures mises à jour ou créées après la date
        factures = Facture.objects.filter(
            Q(created_at__gt=latest_sync_date) | Q(updated_at__gt=latest_sync_date)
        )

        # Sérialisation et réponse
        serializer = FactureSerializer(factures, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def actualiseClients(self, request):
        latest_sync_date_str = request.query_params.get('s_dt')

        # Vérifier si le paramètre est présent
        if not latest_sync_date_str:
            raise ValidationError({"latest_sync_date": "Paramètre obligatoire."})

        # Convertir la date string en datetime
        latest_sync_date = parse_datetime(latest_sync_date_str)
        
        if latest_sync_date is None:
            return Response({"error": "Format de date incorrect"}, status=400)

        # Filtrer les clients mises à jour ou créées après la date
        clients = Client.objects.filter(
            Q(created_at__gt=latest_sync_date) | Q(updated_at__gt=latest_sync_date)
        )

        # Sérialisation et réponse
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def actualiseUsers(self, request):
        latest_sync_date_str = request.query_params.get('s_dt')

        # Vérifier si le paramètre est présent
        if not latest_sync_date_str:
            raise ValidationError({"latest_sync_date": "Paramètre obligatoire."})

        # Convertir la date string en datetime
        latest_sync_date = parse_datetime(latest_sync_date_str)
        
        if latest_sync_date is None:
            return Response({"error": "Format de date incorrect"}, status=400)

        # Filtrer les users mises à jour ou créées après la date
        users = User.objects.filter(date_joined=latest_sync_date)

        # Sérialisation et réponse
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    # Permet d'obtenir les infos de l'utilisateur connécté
    @action(detail=False, methods=['get'])
    def user_data(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    # Permet d'obtenir les infos de l'entreprise
    @action(detail=False, methods=['get'])
    def entreprise_data(self, request):
        entreprise = Entreprise.objects.first()
        if entreprise:
            serializer = EntrepriseSerializer(entreprise)
            return Response(serializer.data)
        return Response({"error": "Aucune entreprise trouvée"}, status=404)

    # Permet d'obtenir tout les utilisateurs
    @action(detail=False, methods=['get'])
    def users(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    # Permet d'obtenir tout les clients
    @action(detail=False, methods=['get'])
    def clients(self, request):
        clients = Client.objects.all()
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)
    
