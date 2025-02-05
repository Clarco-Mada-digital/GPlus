from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.db.models.functions import ExtractYear, ExtractMonth

from .serializers.facture import FactureListSerializer, FactureDetailSerializer, FactureDateSerializer
from .serializers.client import ClientListSerializer

from facture.models import Facture
from clients.models import Client

from datetime import datetime

class MultipleSerializerMixin:
    """
    Cette classe mixin permet de définir un sérialiseur différent pour les vues de détail.
    Si l'action est 'retrieve' (récupérer un objet unique), elle utilise la classe de sérialiseur
    spécifiée dans 'detail_serializer_class'. Sinon, elle utilise la classe de sérialiseur par défaut.
    """

    detail_serializer_class = None

    def get_serializer_class(self):
        # Si l'action est 'retrieve' et qu'une classe de sérialiseur de détail est définie, l'utiliser
        if self.action == 'retrieve' and self.detail_serializer_class is not None:
            return self.detail_serializer_class
        # Sinon, utiliser la classe de sérialiseur par défaut
        return super().get_serializer_class()
    

class FactureViewset(ModelViewSet): #! MultipleSerializerMixin doit être mis avant tout autre class
    """
    FactureViewset: Utilisée pour gérer les factures
    """

    permission_classes = [IsAuthenticated] #! On définit les permissions pour cette vue

    serializer_class = FactureListSerializer # Serializer par défaut, pour la List des factures
    detail_serializer_class = FactureDetailSerializer # Sérialize pour les detailles d'une facture
    date_serializer_class = FactureDateSerializer # Permet d'obtenir une overview de l'historique des factures

    def get_queryset(self):
        # Vérifie la présence du paramètre `date_facture`, Format attendu YYYY-MM
        date_facture = self.request.query_params.get('date_facture')
        if date_facture: 
            try:
                date_filter = datetime.strptime(date_facture, '%Y-%m')
                return Facture.objects.filter(date_facture__year=date_filter.year, date_facture__month=date_filter.month).order_by('-id')
            except ValueError:
                raise ValueError("Format de date incorrect, attendu YYYY-MM")
        
        # Retourne les dates distinctes uniquement
        return Facture.objects.annotate(year=ExtractYear('date_facture'), month=ExtractMonth('date_facture')).values('year', 'month').distinct().order_by('-year', '-month')
    
    def get_serializer_class(self):
        # details '/factutre/<pk>/'
        if self.action == 'retrieve':
            return self.detail_serializer_class
        
        # Utilise FactureDateSerializer si aucune date_facture n'est fournie
        if not self.request.query_params.get('date_facture'):
            return self.date_serializer_class
        
        return super().get_serializer_class()


class ClientViewSet(ReadOnlyModelViewSet):
    """
    ClientViewSet: Utilisée pour gérer les clients
    """

    permission_classes = [IsAuthenticated] #! On définit les permissions pour cette vue

    serializer_class = ClientListSerializer # Serializer par défaut, pour la List des factures

    def get_queryset(self):
        return Client.objects.all()

