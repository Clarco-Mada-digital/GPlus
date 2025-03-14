from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from .serializers.facture import FactureSerializer
from .serializers.client import ClientSerializer
from .serializers.entreprise import EntrepriseSerializer
from .serializers.user import UserSerializer

from facture.models import Facture, Entreprise
from clients.models import Client
from accounts.models import User

from django.db.models import Q
from django.utils.dateparse import parse_datetime

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
    
    # Permet d'obtenir les des factures
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
    
    # Permet d'obtenir les des clients
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
        factures = Client.objects.filter(
            Q(created_at__gt=latest_sync_date) | Q(updated_at__gt=latest_sync_date)
        )

        # Sérialisation et réponse
        serializer = ClientSerializer(factures, many=True)
        return Response(serializer.data)

    # Permet d'obtenir les des users
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
        factures = User.objects.filter(
            Q(created_at__gt=latest_sync_date) | Q(updated_at__gt=latest_sync_date)
        )

        # Sérialisation et réponse
        serializer = UserSerializer(factures, many=True)
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