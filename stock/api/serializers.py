"""
Sérialiseurs pour l'API du module de gestion de stock.

Ce module contient les sérialiseurs Django REST Framework pour les modèles
du module de gestion de stock, permettant la conversion entre les objets Python
et les formats de données JSON pour l'API.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Sum, F

from ..models import (
    Produit, Categorie, Fournisseur, EntreeStock, SortieStock
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle User."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']

class CategorieSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle Categorie."""
    nb_produits = serializers.SerializerMethodField()
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'description', 'date_creation', 'date_maj', 'nb_produits']
        read_only_fields = ['id', 'date_creation', 'date_maj', 'nb_produits']
    
    def get_nb_produits(self, obj):
        """Retourne le nombre de produits dans cette catégorie."""
        return obj.produits.count()

class FournisseurSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle Fournisseur."""
    nb_produits = serializers.SerializerMethodField()
    
    class Meta:
        model = Fournisseur
        fields = [
            'id', 'nom', 'adresse', 'telephone', 'email', 
            'contact', 'date_creation', 'date_maj', 'nb_produits'
        ]
        read_only_fields = ['id', 'date_creation', 'date_maj', 'nb_produits']
    
    def get_nb_produits(self, obj):
        """Retourne le nombre de produits fournis par ce fournisseur."""
        return obj.produits.count()

class ProduitSerializer(serializers.ModelSerializer):
    """Sérialiseur de base pour le modèle Produit."""
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    fournisseur_nom = serializers.CharField(source='fournisseur.nom', read_only=True)
    
    class Meta:
        model = Produit
        fields = [
            'id', 'code', 'designation', 'description', 'categorie', 'categorie_nom',
            'fournisseur', 'fournisseur_nom', 'quantite_stock', 'seuil_alerte',
            'prix_achat', 'prix_vente', 'photo',
            'date_creation', 'date_mise_a_jour'
        ]
        read_only_fields = ['id', 'date_creation', 'date_maj']
    
    def validate_quantite_stock(self, value):
        """Valide que la quantité en stock n'est pas négative."""
        if value < 0:
            raise serializers.ValidationError("La quantité en stock ne peut pas être négative.")
        return value
    
    def validate_prix_achat(self, value):
        """Valide que le prix d'achat est positif."""
        if value <= 0:
            raise serializers.ValidationError("Le prix d'achat doit être supérieur à zéro.")
        return value
    
    def validate_prix_vente(self, value):
        """Valide que le prix de vente est positif."""
        if value <= 0:
            raise serializers.ValidationError("Le prix de vente doit être supérieur à zéro.")
        return value
    
    def validate(self, data):
        """Valide que le prix de vente est supérieur au prix d'achat."""
        if 'prix_vente' in data and 'prix_achat' in data:
            if data['prix_vente'] <= data['prix_achat']:
                raise serializers.ValidationError(
                    "Le prix de vente doit être supérieur au prix d'achat."
                )
        return data

class ProduitDetailSerializer(ProduitSerializer):
    """Sérialiseur détaillé pour le modèle Produit avec des champs supplémentaires."""
    mouvements_recents = serializers.SerializerMethodField()
    total_entrees = serializers.SerializerMethodField()
    total_sorties = serializers.SerializerMethodField()
    
    class Meta(ProduitSerializer.Meta):
        fields = ProduitSerializer.Meta.fields + [
            'mouvements_recents', 'total_entrees', 'total_sorties'
        ]
    
    def get_mouvements_recents(self, obj):
        """Récupère les 5 derniers mouvements du produit."""
        entrees = EntreeStock.objects.filter(produit=obj).order_by('-date')[:3]
        sorties = SortieStock.objects.filter(produit=obj).order_by('-date')[:3]
        
        return {
            'entrees': EntreeStockSerializer(entrees, many=True).data,
            'sorties': SortieStockSerializer(sorties, many=True).data
        }
    
    def get_total_entrees(self, obj):
        """Calcule le total des entrées de stock pour ce produit."""
        from django.db.models import Sum, F
        result = EntreeStock.objects.filter(produit=obj).aggregate(
            total_quantite=Sum('quantite'),
            total_montant=Sum(F('quantite') * F('prix_unitaire'))
        )
        return {
            'total_quantite': result['total_quantite'] or 0,
            'total_montant': float(result['total_montant'] or 0)
        }
    
    def get_total_sorties(self, obj):
        """Calcule le total des sorties de stock pour ce produit."""
        from django.db.models import Sum
        result = SortieStock.objects.filter(produit=obj).aggregate(
            total_quantite=Sum('quantite')
        )
        return {
            'total_quantite': result['total_quantite'] or 0
        }

class EntreeStockSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle EntreeStock."""
    produit_designation = serializers.CharField(source='produit.designation', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    montant_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
        source='get_montant_total'
    )
    
    class Meta:
        model = EntreeStock
        fields = [
            'id', 'produit', 'produit_designation', 'quantite', 'prix_unitaire',
            'montant_total', 'date', 'utilisateur', 'utilisateur_nom',
            'reference', 'notes', 'fournisseur', 'annulee'
        ]
        read_only_fields = [
            'id', 'date', 'montant_total', 'utilisateur', 'annulee'
        ]
    
    def validate_quantite(self, value):
        """Valide que la quantité est positive."""
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être supérieure à zéro.")
        return value
    
    def validate_prix_unitaire(self, value):
        """Valide que le prix unitaire est positif."""
        if value <= 0:
            raise serializers.ValidationError("Le prix unitaire doit être supérieur à zéro.")
        return value
    
    def create(self, validated_data):
        """Crée une nouvelle entrée de stock et met à jour le stock du produit."""
        # Récupérer l'utilisateur actuel depuis le contexte de la requête
        validated_data['utilisateur'] = self.context['request'].user
        
        # Créer l'entrée de stock
        entree = super().create(validated_data)
        
        # Mettre à jour le stock du produit
        produit = entree.produit
        produit.quantite_stock += entree.quantite
        produit.save()
        
        return entree

class SortieStockSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle SortieStock."""
    produit_designation = serializers.CharField(source='produit.designation', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    
    class Meta:
        model = SortieStock
        fields = [
            'id', 'produit', 'produit_designation', 'quantite', 'date',
            'utilisateur', 'utilisateur_nom', 'client', 'motif',
            'date_creation', 'date_maj', 'annulee'
        ]
        read_only_fields = ['id', 'date_creation', 'date_maj', 'utilisateur', 'annulee']
    
    def validate_quantite(self, value):
        """Valide que la quantité est positive et que le stock est suffisant."""
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être supérieure à zéro.")
        
        # Vérifier le stock disponible uniquement à la création
        if self.instance is None:  # Nouvelle sortie
            produit = self.initial_data.get('produit')
            if produit and produit.quantite_stock < value:
                raise serializers.ValidationError(
                    f"Stock insuffisant. Stock disponible: {produit.quantite_stock}"
                )
        
        return value
    
    def create(self, validated_data):
        """Crée une nouvelle sortie de stock et met à jour le stock du produit."""
        # Récupérer l'utilisateur actuel depuis le contexte de la requête
        validated_data['utilisateur'] = self.context['request'].user
        produit = validated_data['produit']
        quantite = validated_data['quantite']
        
        # Vérifier à nouveau le stock (au cas où)
        if produit.quantite_stock < quantite:
            raise serializers.ValidationError(
                f'Stock insuffisant. Stock disponible: {produit.quantite_stock}'
            )
        
        # Créer la sortie de stock
        sortie = super().create(validated_data)
        
        # Mettre à jour le stock du produit
        produit.quantite_stock -= quantite
        produit.save()
        
        return sortie

class AjustementStockSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'ajustement manuel du stock.
    Permet d'ajouter ou de retirer une quantité spécifique de stock.
    """
    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    quantite = serializers.DecimalField(max_digits=10, decimal_places=2)
    motif = serializers.CharField(max_length=255)
    
    def validate_quantite(self, value):
        """Valide que la quantité n'est pas nulle."""
        if value == 0:
            raise serializers.ValidationError("La quantité ne peut pas être zéro.")
        return value
    
    def validate(self, data):
        """Valide que le stock est suffisant pour une sortie."""
        produit = data['produit']
        quantite = data['quantite']
        
        # Pour une sortie (quantité négative), vérifier le stock
        if quantite < 0 and produit.quantite_stock < abs(quantite):
            raise serializers.ValidationError({
                'quantite': f'Stock insuffisant. Stock disponible: {produit.quantite_stock}'
            })
        
        return data
