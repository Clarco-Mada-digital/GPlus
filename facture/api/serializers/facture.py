from rest_framework import serializers

from facture.models import Facture

from facture.api.serializers.client import ClientListSerializer
from facture.api.serializers.user import UserSerializer


# Utilisée pour sérialiser la liste de facture
class FactureListSerializer(serializers.ModelSerializer):
    
    client = serializers.SerializerMethodField()

    class Meta:
        model = Facture
        fields = ['id', 'ref', 'intitule', 'type', 'montant', 'etat_facture', 'date_facture', 'client']

    def get_client(self, instance):
        queryset = instance.client
        if queryset:   
            serializer = ClientListSerializer(queryset)
            return serializer.data
        return None


# Utilisée pour sérialiser les détails d'une facture
class FactureDetailSerializer(serializers.ModelSerializer):

    created_by = serializers.SerializerMethodField() # Vas permettre l'obtention des information de l'utilisateur à l'auteur de la facture

    class Meta:
        model = Facture
        fields = ['id', 'ref', 'intitule', 'type', 'montant', 'etat_facture', 'date_facture',
                  'services', 'with_tva', 'created_by']

    def get_created_by(self, instance): # Methode qui selectionnel l'utilisateur qui à créer la facture
        queryset = instance.created_by # Fait référence au propriéte "created_by" défini au debut de la class
        if queryset: # Vu que created by peut être null, on lui  fait passér une vérification pour évité les erreurs
            serializer = UserSerializer(queryset) # Sérialise l'instance de 'created_by' par le UserSerializer
            return serializer.data
        return None