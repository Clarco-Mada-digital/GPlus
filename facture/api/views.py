from rest_framework.viewsets import ModelViewSet

from facture.api.serializers import FactureListSerializer, FactureDetailSerializer

from facture.models import Facture

"""
Cette classe mixin permet de définir un sérialiseur différent pour les vues de détail.
Si l'action est 'retrieve' (récupérer un objet unique), elle utilise la classe de sérialiseur
spécifiée dans 'detail_serializer_class'. Sinon, elle utilise la classe de sérialiseur par défaut.
"""
class MultipleSerializerMixin:

    detail_serializer_class = None

    def get_serializer_class(self):
        # Si l'action est 'retrieve' et qu'une classe de sérialiseur de détail est définie, l'utiliser
        if self.action == 'retrieve' and self.detail_serializer_class is not None:
            return self.detail_serializer_class
        # Sinon, utiliser la classe de sérialiseur par défaut
        return super().get_serializer_class()
    
class FactureViewset(MultipleSerializerMixin, ModelViewSet): #! MultipleSerializerMixin doit être mis avant tout autre class

    serializer_class = FactureListSerializer # Serializer par défaut, pour la List des factures
    detail_serializer_class = FactureDetailSerializer # Sérialize pour les detailles d'une facture

    def get_queryset(self):
        return Facture.objects.all()

