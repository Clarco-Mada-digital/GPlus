from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, F, Value, Case, When, IntegerField, FloatField
from django.db.models.functions import Coalesce

from .models import (
    Produit, Categorie, Fournisseur, EntreeStock, SortieStock
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle User"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class CategorieSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle Categorie"""
    nb_produits = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'description', 'date_creation', 'date_mise_a_jour', 'nb_produits']
        read_only_fields = ['id', 'date_creation', 'date_mise_a_jour']


class FournisseurSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle Fournisseur"""
    nb_produits = serializers.IntegerField(read_only=True)
    nb_entrees = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Fournisseur
        fields = [
            'id', 'nom', 'email', 'telephone', 'adresse', 'contact',
            'date_creation', 'date_mise_a_jour', 'nb_produits', 'nb_entrees'
        ]
        read_only_fields = ['id', 'date_creation', 'date_mise_a_jour']


class ProduitSerializer(serializers.ModelSerializer):
    """Sérialiseur de base pour le modèle Produit"""
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    fournisseur_nom = serializers.CharField(source='fournisseur.nom', read_only=True)
    statut_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Produit
        fields = [
            'id', 'code', 'designation', 'description', 'categorie', 'categorie_nom',
            'fournisseur', 'fournisseur_nom', 'prix_achat', 'prix_vente',
            'quantite_stock', 'seuil_alerte', 'statut_stock', 'photo',
            'date_creation', 'date_mise_a_jour'
        ]
        read_only_fields = ['id', 'date_creation', 'date_mise_a_jour', 'statut_stock']
    
    def get_statut_stock(self, obj):
        """Détermine le statut du stock (disponible, alerte, épuisé)"""
        if obj.quantite_stock == 0:
            return 'épuisé'
        elif obj.quantite_stock <= obj.seuil_alerte:
            return 'alerte'
        return 'disponible'


class ProduitDetailSerializer(ProduitSerializer):
    """Sérialiseur détaillé pour le modèle Produit avec statistiques"""
    statut_stock = serializers.SerializerMethodField()
    mouvements = serializers.SerializerMethodField()
    
    class Meta(ProduitSerializer.Meta):
        fields = ProduitSerializer.Meta.fields + ['mouvements']
    
    def get_mouvements(self, obj):
        """Récupère les statistiques des mouvements du produit"""
        # Récupérer les 5 derniers mouvements
        entrees = obj.entrees.filter(annulee=False).order_by('-date')[:5]
        sorties = obj.sorties.order_by('-date')[:5]
        
        # Sérialiser les mouvements
        entree_serializer = EntreeStockSerializer(entrees, many=True)
        sortie_serializer = SortieStockSerializer(sorties, many=True)
        
        # Calculer les totaux
        total_entrees = obj.entrees.filter(annulee=False).aggregate(
            quantite=Coalesce(Sum('quantite'), 0),
            montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0)
        )
        
        total_sorties = obj.sorties.aggregate(
            quantite=Coalesce(Sum('quantite'), 0),
            montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0)
        )
        
        return {
            'entrees': entree_serializer.data,
            'sorties': sortie_serializer.data,
            'totaux': {
                'entrees': {
                    'quantite': float(total_entrees['quantite']),
                    'montant': float(total_entrees['montant'])
                },
                'sorties': {
                    'quantite': float(total_sorties['quantite']),
                    'montant': float(total_sorties['montant'])
                },
                'solde': {
                    'quantite': float(total_entrees['quantite'] - total_sorties['quantite']),
                    'montant': float(total_entrees['montant'] - total_sorties['montant'])
                }
            }
        }


class EntreeStockSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle EntreeStock"""
    produit_nom = serializers.CharField(source='produit.designation', read_only=True)
    produit_code = serializers.CharField(source='produit.code', read_only=True)
    fournisseur_nom = serializers.CharField(source='fournisseur.nom', read_only=True, allow_null=True)
    utilisateur_nom = serializers.SerializerMethodField()
    utilisateur_annulation_nom = serializers.SerializerMethodField()
    montant_total = serializers.SerializerMethodField()
    
    class Meta:
        model = EntreeStock
        fields = [
            'id', 'produit', 'produit_nom', 'produit_code', 'quantite', 'prix_unitaire',
            'montant_total', 'date', 'reference', 'fournisseur', 'fournisseur_nom',
            'utilisateur', 'utilisateur_nom', 'notes', 'annulee', 'motif_annulation',
            'utilisateur_annulation', 'utilisateur_annulation_nom', 'date_annulation',
            'date_creation', 'date_mise_a_jour'
        ]
        read_only_fields = [
            'id', 'produit_nom', 'produit_code', 'fournisseur_nom', 'utilisateur_nom',
            'utilisateur_annulation_nom', 'date_creation', 'date_mise_a_jour',
            'montant_total'
        ]
    
    def get_utilisateur_nom(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        if obj.utilisateur:
            return f"{obj.utilisateur.first_name} {obj.utilisateur.last_name}".strip() or obj.utilisateur.username
        return None
    
    def get_utilisateur_annulation_nom(self, obj):
        """Retourne le nom complet de l'utilisateur qui a annulé"""
        if obj.utilisateur_annulation:
            return f"{obj.utilisateur_annulation.first_name} {obj.utilisateur_annulation.last_name}".strip() or obj.utilisateur_annulation.username
        return None
    
    def get_montant_total(self, obj):
        """Calcule le montant total de l'entrée"""
        return float(obj.quantite * obj.prix_unitaire)
    
    def validate(self, data):
        """Validation des données d'entrée"""
        if self.instance and self.instance.annulee:
            raise serializers.ValidationError({"non_field_errors": ["Une entrée annulée ne peut pas être modifiée."]})
        
        if data.get('quantite', 0) <= 0:
            raise serializers.ValidationError({"quantite": ["La quantité doit être supérieure à zéro."]})
        
        if data.get('prix_unitaire', 0) < 0:
            raise serializers.ValidationError({"prix_unitaire": ["Le prix unitaire ne peut pas être négatif."]})
        
        return data


class SortieStockSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle SortieStock"""
    produit_nom = serializers.CharField(source='produit.designation', read_only=True)
    produit_code = serializers.CharField(source='produit.code', read_only=True)
    utilisateur_nom = serializers.SerializerMethodField()
    montant_total = serializers.SerializerMethodField()
    
    class Meta:
        model = SortieStock
        fields = [
            'id', 'produit', 'produit_nom', 'produit_code', 'quantite', 'prix_unitaire',
            'montant_total', 'date', 'reference', 'client', 'utilisateur', 'utilisateur_nom',
            'notes', 'date_creation', 'date_mise_a_jour'
        ]
        read_only_fields = [
            'id', 'produit_nom', 'produit_code', 'utilisateur_nom', 'date_creation',
            'date_mise_a_jour', 'montant_total'
        ]
    
    def get_utilisateur_nom(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        if obj.utilisateur:
            return f"{obj.utilisateur.first_name} {obj.utilisateur.last_name}".strip() or obj.utilisateur.username
        return None
    
    def get_montant_total(self, obj):
        """Calcule le montant total de la sortie"""
        return float(obj.quantite * obj.prix_unitaire)
    
    def validate(self, data):
        """Validation des données de sortie"""
        if 'produit' not in data:
            raise serializers.ValidationError({"produit": ["Le produit est requis."]})
        
        produit = data['produit']
        quantite = data.get('quantite', 0)
        
        if quantite <= 0:
            raise serializers.ValidationError({"quantite": ["La quantité doit être supérieure à zéro."]})
        
        if 'prix_unitaire' in data and data['prix_unitaire'] < 0:
            raise serializers.ValidationError({"prix_unitaire": ["Le prix unitaire ne peut pas être négatif."]})
        
        # Vérifier le stock disponible (sauf pour les mises à jour partielles)
        if self.partial and 'quantite' not in data:
            return data
            
        stock_disponible = produit.quantite_stock
        
        # Pour une mise à jour, soustraire l'ancienne quantité
        if self.instance:
            stock_disponible += self.instance.quantite
        
        if quantite > stock_disponible:
            raise serializers.ValidationError({
                "quantite": [
                    f"Stock insuffisant. Quantité disponible : {stock_disponible}"
                ]
            })
        
        return data


class MouvementStockSerializer(serializers.Serializer):
    """Sérialiseur pour les opérations sur les mouvements de stock"""
    produit_id = serializers.IntegerField(required=True)
    quantite = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=True, min_value=0
    )
    motif = serializers.CharField(required=False, allow_blank=True, default="")
    
    def validate_produit_id(self, value):
        """Vérifie que le produit existe"""
        try:
            return Produit.objects.get(pk=value)
        except Produit.DoesNotExist:
            raise serializers.ValidationError("Produit non trouvé.")
    
    def create(self, validated_data):
        # Cette méthode ne sera pas utilisée directement
        pass
    
    def update(self, instance, validated_data):
        # Cette méthode ne sera pas utilisée directement
        pass


class StatistiquesStockSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques de stock"""
    total_produits = serializers.IntegerField()
    total_quantite = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_valeur_achat = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_valeur_vente = serializers.DecimalField(max_digits=15, decimal_places=2)
    produits_alerte = serializers.IntegerField()
    produits_epuises = serializers.IntegerField()
    produits_disponibles = serializers.IntegerField()
    
    class Meta:
        fields = [
            'total_produits', 'total_quantite', 'total_valeur_achat',
            'total_valeur_vente', 'produits_alerte', 'produits_epuises',
            'produits_disponibles'
        ]
