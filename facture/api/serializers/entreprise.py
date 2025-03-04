from rest_framework import serializers
from facture.models import Entreprise


class EntrepriseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Entreprise
        fields = ['logo', 'nom', 'adresse', 'tel', 'email', 'code_postal', 'region', 'nif', 'stat', 'taux_tva']