from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.db.models.functions import ExtractYear, ExtractMonth

from .serializers.facture import FactureListSerializer, FactureDetailSerializer, FactureDateSerializer
from .serializers.client import ClientListSerializer
from .serializers.entreprise import EntrepriseSerializer

from facture.models import Facture, Entreprise
from clients.models import Client

from datetime import datetime

class FactureViewset(ModelViewSet):
    """
    FactureViewset: Utilisée pour gérer les factures
    """
    permission_classes = [IsAuthenticated] #! On définit les permissions pour cette vue
    serializer_class = FactureListSerializer # Serializer par défaut, pour la List des factures
    detail_serializer_class = FactureDetailSerializer # Sérialize pour les detailles d'une facture

    def get_queryset(self):
        # Si /facture?date_facture=YYYY-MM
        date_facture = self.request.query_params.get('date_facture')
        if date_facture: 
            try: # Factures en fonction de leurs date de creation
                date_filter = datetime.strptime(date_facture, '%Y-%m')
                return Facture.objects.filter(date_facture__year=date_filter.year, date_facture__month=date_filter.month).order_by('-id')
            except ValueError:
                raise ValidationError("Format de date incorrect, attendu YYYY-MM")
        
        # Sinon
        return Facture.objects.all().order_by('-id') # Toute les factures
    
    # Selectionne le serialiseur adequat
    def get_serializer_class(self):
        if self.action == 'retrieve': # /factutre/<pk>/
            return self.detail_serializer_class
        
        return super().get_serializer_class() # /facture/
    
    # Permet d'obtenir la liste des sections par des factures
    @action(detail=False, methods=['get'], serializer_class=FactureDateSerializer)
    def historique_dates(self, request):
        dates = Facture.objects.annotate(
            year=ExtractYear('date_facture'),
            month=ExtractMonth('date_facture')
        ).values('year', 'month').distinct().order_by('-year', '-month')
        return Response(dates)


class ClientViewSet(ReadOnlyModelViewSet):
    """
    ClientViewSet: Utilisée pour gérer les clients
    """
    permission_classes = [IsAuthenticated] #! On définit les permissions pour cette vue
    serializer_class = ClientListSerializer # Serializer par défaut, pour la List des factures

    def get_queryset(self):
        return Client.objects.all()
    

class EntrepriseViewSet(ReadOnlyModelViewSet):
    """
    EntrepriseViewSet: Utilisée pour obtnenir les infos de l'entreprise
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EntrepriseSerializer

    def get_queryset(self):
        return Entreprise.objects.all()
