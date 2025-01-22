from django import forms
from .models import Facture, Service

class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ('intitule', 'reglement', 'condition', 'etat', 'montant', 'client', 'service')

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('nom_service', 'prix_unitaire', 'description')

