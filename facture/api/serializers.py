from rest_framework import serializers

from accounts.models import User
from facture.models import Facture


"""
Les classes sérialiseurs est utilisée pour sérialiser les donnée envoyer ou reçu vie à l'api
Elle permet le traîtement des JSONs
"""

#### Serialisateurs de User #####

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User # Modèle User de Django
        fields = ['id', 'username', 'first_name', 'last_name']


#### Serialisateurs de Facture #####

# Utilisée pour sérialiser la liste des factures
class FactureListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Facture
        fields = ['id', 'ref', 'intitule', 'type', 'montant', 'etat_facture', 'date_facture']

# Utilisée pour sérialiser les détails d'une facture
class FactureDetailSerializer(serializers.ModelSerializer):

    created_by = serializers.SerializerMethodField() # Vas permettre l'obtention des information de l'utilisateur

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