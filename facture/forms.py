from django import forms
from .models import Facture, Service, Entreprise

class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ('date_facture', 'intitule', 'reglement', 'condition', 'etat_facture', 'montant', 'client', 'services', 'type', 'with_tva')

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('nom_service', 'prix_unitaire', 'description')

class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ('logo', 'nom', 'tel', 'email', 'adresse', 'region', 'code_postal', 'nif', 'stat', 'taux_tva')