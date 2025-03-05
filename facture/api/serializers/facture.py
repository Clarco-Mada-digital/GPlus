from django.utils import timezone
from django.db import transaction
from rest_framework import serializers

from facture.models import Facture

from .user import UserSerializer
from .client import ClientDetailSerializer

class FactureDateSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    

# Utilisée pour sérialiser la liste de facture
class FactureListSerializer(serializers.ModelSerializer):
    """
    FactureListSerializer: Utilisée pour sérialiser la liste de facture
    Gère les requêtes GET et POST sur /api/facture/
    Pour une requête POST il est escentiel de mettre le '/' à la fin de l'url api/facture sinon il y aura une erreur
    """
    class Meta:
        model = Facture
        fields = '__all__'

    # Surcharge de la méthode create pour générer la référence de la facture
    @transaction.atomic
    def create(self, validated_data):
        # Générer une référence provisoire
        validated_data['ref'] = f"TEMP_REF-{str(timezone.now().date())}-{str(timezone.now().time())}"

        validated_data['created_by'] = self.context['request'].user
        
        # Créer la facture avec une référence provisoire
        facture = super().create(validated_data)
        
        # Mettre à jour la référence de la facture après l'enregistrement
        facture.ref = self.generate_ref(facture)  # Regénérer le ref avec l'ID réel
        facture.save()  # Sauvegarder la facture avec la référence mis à jour
        
        return facture

    # Génère la référence de la facture
    def generate_ref(self, facture): 
        # Récupère l'année actuelle
        facture_year = str(timezone.now().year)

        # Récupère l'ID
        facture_id = facture.id

        # Concatène l'année et l'id de la facture, zfill permet de compléter l'id avec des 0
        facture_ref_end = f"{facture_year}-"+str(facture_id).zfill(6)
        
        if facture.etat_facture == 'Brouillon':
            if facture.type == 'Facture':
                return "FPROV" + facture_ref_end
            elif facture.type == 'Devis':
                return "DPROV" + facture_ref_end
        else:
            if facture.type == 'Facture':
                return "F" + facture_ref_end
            elif facture.type == 'Devis':
                return "D" + facture_ref_end

# Utilisée pour sérialiser les détails d'une facture
class FactureDetailSerializer(serializers.ModelSerializer):
    """
    FactureDetailSerializer: Utilisée pour sérialiser les détails d'une facture
    Gère les requêtes GET, PUT et DELETE sur /api/facture/<pk>/
    Pour une requête PUT & DELETE il est escentiel de mettre le '/' à la fin de l'url api/facture/<pk> sinon il y aura une erreur
    """
    created_by = serializers.SerializerMethodField() # Vas permettre l'obtention des information de l'utilisateur à l'auteur de la facture
    client = serializers.SerializerMethodField() # Vas permettre l'obtention des information du client de la facture
    
    class Meta:
        model = Facture
        fields = [
            'id', 'ref', 'intitule', 'type', 'client', 'date_facture', 
            'reglement', 'condition', 'etat_facture', 'services', 
            'with_tva', 'created_by',  'montant'
        ]
        read_only_fields = ['ref', 'created_by', 'client'] # Empêche la modification de ces champs

    def get_client(self, instance): # Methode qui selectionne le client de la facture
        queryset = instance.client
        if queryset:
            serializer = ClientDetailSerializer(queryset) # Sérialise l'instance de 'client' par le ClientDetailSerializer
            return serializer.data
        return None

    def get_created_by(self, instance): # Methode qui selectionnel l'utilisateur qui à créer la facture
        queryset = instance.created_by # Fait référence au propriéte "created_by" défini au debut de la class
        if queryset: # Vu que created by peut être null, on lui  fait passér une vérification pour évité les erreurs
            serializer = UserSerializer(queryset) # Sérialise l'instance de 'created_by' par le UserSerializer
            return serializer.data
        return None