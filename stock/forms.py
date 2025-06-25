"""
Formulaires pour le module de gestion de stock.

Ce module contient les formulaires Django utilisés pour la validation des données
dans les vues basées sur les fonctions et les vues basées sur les classes.
"""

from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import (
    Categorie, Produit, Fournisseur, EntreeStock, SortieStock
)

class CategorieForm(ModelForm):
    """
    Formulaire pour la création et la mise à jour des catégories.
    """
    class Meta:
        model = Categorie
        fields = ['nom', 'description']
        labels = {
            'nom': _('Nom de la catégorie'),
            'description': _('Description')
        }
        help_texts = {
            'nom': _('Entrez un nom unique pour cette catégorie'),
            'description': _('Une description détaillée de la catégorie (optionnelle)')
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def clean_nom(self):
        """Valide que le nom de la catégorie est unique."""
        nom = self.cleaned_data.get('nom')
        if not nom:
            raise forms.ValidationError(_("Le nom de la catégorie est obligatoire."))
            
        # Vérification de l'unicité du nom (en ignorant la casse)
        queryset = Categorie.objects.filter(nom__iexact=nom)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
            
        if queryset.exists():
            raise forms.ValidationError(_("Une catégorie avec ce nom existe déjà."))
            
        return nom


class ProduitForm(ModelForm):
    """
    Formulaire pour la création et la mise à jour des produits.
    """
    class Meta:
        model = Produit
        fields = [
            'code', 'designation', 'description', 'categorie',
            'fournisseur', 'quantite_stock', 'seuil_alerte',
            'prix_achat', 'prix_vente', 'photo'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'quantite_stock': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'seuil_alerte': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'prix_achat': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'class': 'form-control'}),
            'prix_vente': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """Validation croisée des champs."""
        cleaned_data = super().clean()
        prix_achat = cleaned_data.get('prix_achat')
        prix_vente = cleaned_data.get('prix_vente')
        
        if prix_achat and prix_vente and prix_vente <= prix_achat:
            self.add_error(
                'prix_vente',
                _('Le prix de vente doit être supérieur au prix d\'achat.')
            )
        
        # Validation du code unique
        code = cleaned_data.get('code')
        if code:
            queryset = Produit.objects.filter(code__iexact=code)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                self.add_error('code', _('Un produit avec ce code existe déjà.'))
        
        return cleaned_data


class FournisseurForm(ModelForm):
    """
    Formulaire pour la création et la mise à jour des fournisseurs.
    """
    class Meta:
        model = Fournisseur
        fields = ['nom', 'adresse', 'telephone', 'email', 'contact']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_telephone(self):
        """Valide le numéro de téléphone."""
        telephone = self.cleaned_data.get('telephone')
        if telephone and not telephone.isdigit():
            raise forms.ValidationError(_("Le numéro de téléphone ne doit contenir que des chiffres."))
        return telephone


class EntreeStockForm(ModelForm):
    """
    Formulaire pour la création des entrées de stock.
    """
    def __init__(self, *args, **kwargs):
        """Initialise le formulaire avec l'utilisateur actuel."""
        self.user = kwargs.pop('utilisateur', None)
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = EntreeStock
        fields = [
            'produit', 'quantite', 'prix_unitaire',
            'reference', 'fournisseur', 'notes'
        ]
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'prix_unitaire': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def clean_quantite(self):
        """Valide que la quantité est positive."""
        quantite = self.cleaned_data.get('quantite')
        if quantite is not None and quantite <= 0:
            raise forms.ValidationError(_("La quantité doit être supérieure à zéro."))
        return quantite
    
    def clean_prix_unitaire(self):
        """Valide que le prix unitaire est positif."""
        prix_unitaire = self.cleaned_data.get('prix_unitaire')
        if prix_unitaire is not None and prix_unitaire < 0:
            raise forms.ValidationError(_("Le prix unitaire ne peut pas être négatif."))
        return prix_unitaire
    
    def save(self, commit=True):
        """Sauvegarde l'entrée de stock avec l'utilisateur actuel."""
        instance = super().save(commit=False)
        if not instance.pk:  # Nouvelle entrée
            instance.utilisateur = self.user
        if commit:
            instance.save()
        return instance


class SortieStockForm(ModelForm):
    """
    Formulaire pour la création des sorties de stock.
    """
    class Meta:
        model = SortieStock
        fields = ['produit', 'quantite', 'prix_unitaire', 'client', 'reference', 'notes']
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'prix_unitaire': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'class': 'form-control'}),
            'client': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialise le formulaire avec l'utilisateur actuel."""
        # Gère à la fois 'user' et 'utilisateur' pour la rétrocompatibilité
        self.user = kwargs.pop('user', None)
        if self.user is None:
            self.user = kwargs.pop('utilisateur', None)
        super().__init__(*args, **kwargs)
    
    def clean_quantite(self):
        """Valide que la quantité est disponible en stock."""
        quantite = self.cleaned_data.get('quantite')
        produit = self.cleaned_data.get('produit')
        
        if not produit:
            return quantite
            
        if quantite is not None and quantite <= 0:
            raise forms.ValidationError(_("La quantité doit être supérieure à zéro."))
            
        if quantite and produit.quantite_stock < quantite:
            raise forms.ValidationError(
                _("Stock insuffisant. Stock disponible: %(stock)d") % {
                    'stock': produit.quantite_stock
                }
            )
            
        return quantite
    
    def clean_prix_unitaire(self):
        """Valide que le prix unitaire est positif."""
        prix_unitaire = self.cleaned_data.get('prix_unitaire')
        if prix_unitaire is not None and prix_unitaire < 0:
            raise forms.ValidationError(_("Le prix unitaire ne peut pas être négatif."))
        return prix_unitaire
    
    def save(self, commit=True):
        """Sauvegarde la sortie de stock avec l'utilisateur actuel."""
        instance = super().save(commit=False)
        if self.user:
            instance.utilisateur = self.user
        if commit:
            instance.save()
        return instance


class AnnulerEntreeForm(forms.Form):
    """
    Formulaire pour annuler une entrée de stock.
    """
    motif_annulation = forms.CharField(
        label=_('Motif de l\'annulation'),
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': _('Raison de l\'annulation de cette entrée de stock')
        }),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        """Initialise le formulaire avec l'entrée de stock à annuler."""
        self.entree = kwargs.pop('entree', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """Vérifie que l'entrée peut être annulée."""
        cleaned_data = super().clean()
        
        if not self.entree:
            raise ValidationError(_("Aucune entrée de stock spécifiée."))
            
        if self.entree.annulee:
            raise ValidationError(_("Cette entrée a déjà été annulée."))
            
        # Vérifier que le stock est suffisant pour annuler
        produit = self.entree.produit
        if produit.quantite_stock < self.entree.quantite:
            raise ValidationError(
                _("Stock insuffisant pour annuler cette entrée. "
                  "Stock actuel: %(stock)d, Quantité à annuler: %(quantite)d") % {
                    'stock': produit.quantite_stock,
                    'quantite': self.entree.quantite
                }
            )
            
        return cleaned_data
    
    def save(self):
        """Annule l'entrée de stock et met à jour le stock du produit."""
        if not self.is_valid():
            raise ValueError("Le formulaire n'est pas valide")
            
        # Marquer l'entrée comme annulée
        self.entree.annulee = True
        self.entree.notes = f"Annulée: {self.cleaned_data['motif_annulation']}"
        
        # Mettre à jour le stock du produit
        produit = self.entree.produit
        produit.quantite_stock -= self.entree.quantite
        
        # Sauvegarder les modifications
        with transaction.atomic():
            self.entree.save()
            produit.save()
            
        return self.entree
