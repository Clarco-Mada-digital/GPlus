from django import forms
from .models import Fournisseur, Categorie, Personnel

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['name', 'contact']

class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['name', 'description']

class PersonnelForm(forms.ModelForm):
    class Meta:
        model = Personnel
        fields = ['last_name', 'first_name', 'email', 'tel', 'sexe', 'date_naissance', 'photo', 'adresse', 'type_personnel']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_naissance'].widget = forms.DateInput(attrs={'type': 'date'})
