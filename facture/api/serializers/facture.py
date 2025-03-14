from django.utils import timezone
from django.db import transaction
from rest_framework import serializers

from facture.models import Facture


# Utilisée pour sérialiser la liste de facture
class FactureSerializer(serializers.ModelSerializer):
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
    
    # Surchage de la methode de mis à jour pour permetre la mis à jour du camp updated_at
    def update(self, instance, validated_data):
        # Ajout du champ updated_at pour permetre la suivie des mis à jours
        validated_data['updated_at'] = timezone.now()

        return super().update(instance, validated_data)

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