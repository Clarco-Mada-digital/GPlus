from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .serializers.facture import FactureListSerializer, FactureDetailSerializer
from .serializers.client import ClientListSerializer

from facture.models import Facture
from clients.models import Client


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
    

class FactureViewset(MultipleSerializerMixin, ModelViewSet): #! MultipleSerializerMixin doit être mis avant tout autre class
    """
    FactureViewset: Utilisée pour gérer les factures
    """
    serializer_class = FactureListSerializer # Serializer par défaut, pour la List des factures
    detail_serializer_class = FactureDetailSerializer # Sérialize pour les detailles d'une facture

    def get_queryset(self):
        return Facture.objects.all().order_by('-id')


class ClientViewSet(ReadOnlyModelViewSet):
    """
    ClientViewSet: Utilisée pour gérer les clients
    """
    serializer_class = ClientListSerializer # Serializer par défaut, pour la List des factures

    def get_queryset(self):
        return Client.objects.all()

