from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['photo', 'name', 'commercial_name', 'post', 'tel', 'tel2', 'email', 'adresse', 'type_client', 'disponibilite', 'description_facture']

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['disponibilite'].widget = forms.DateTimeField(attrs={'type': 'date-time'}) 
        
  