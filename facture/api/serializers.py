from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from clients.models import Client
from accounts.models import User
from facture.models import Entreprise, Service, Facture


class FactureServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'photo', 'date_joined']
    
    def update(self, instance, validated_data):
        # Si photo n'est pas fournie dans la requête, on conserve l'existante
        if 'photo' in validated_data and not validated_data['photo']:
            validated_data.pop('photo')
        
        # Appliquer les autres modifications
        return super().update(instance, validated_data)


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class EntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entreprise
        fields = ['logo', 'nom', 'adresse', 'tel', 'email', 'code_postal', 'region', 'nif', 'stat', 'taux_tva']


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
        facture_year = str(timezone.now().year) # Récupère l'année actuelle
        facture.ref = self.generate_ref(facture=facture, facture_year=facture_year)  # Regénérer le ref avec l'ID réel
        facture.save()  # Sauvegarder la facture avec la référence mis à jour
        
        return facture
    
    # Surchage de la methode de mis à jour pour permetre la mis à jour du camp updated_at
    def update(self, instance, validated_data):
        facture_id = instance.pk

        # Récupération des champs modifiables
        new_date_facture = validated_data.get("date_facture")
        new_etat_facture = validated_data.get("etat_facture")

        if not new_date_facture or not new_etat_facture:
            raise ValidationError("Les champs 'date_facture' et 'etat_facture' sont obligatoires.")


        # print(f"Type de date_facture: {type(new_date_facture_str)} - Valeur: {new_date_facture_str}")
        new_facture_year = str(new_date_facture.year)

        # Récupération de la facture actuelle pour avoir son type
        current_facture = Facture.objects.get(pk=facture_id)

        # Génération de la nouvelle référence
        validated_data["ref"] = self.generate_ref(
            facture_id=facture_id,
            facture_year=new_facture_year,
            etat_facture=new_etat_facture,
            facture_type=current_facture.type
        )

        # Mise à jour de la date de modification
        validated_data['updated_at'] = timezone.now()

        return super().update(instance, validated_data)

    @staticmethod
    def generate_ref(facture=None, facture_id=None, facture_year=None, etat_facture=None, facture_type=None):
        if facture:
            facture_id = facture.id
            etat_facture = facture.etat_facture
            facture_type = facture.type

        if None in [facture_id, facture_year, etat_facture, facture_type]:
            raise ValueError("Informations insuffisantes pour générer la référence")

        facture_ref_end = f"{facture_year}-" + str(facture_id).zfill(6)

        if etat_facture == 'Brouillon':
            return ("FPROV" if facture_type == 'Facture' else "DPROV") + facture_ref_end
        else:
            return ("F" if facture_type == 'Facture' else "D") + facture_ref_end
