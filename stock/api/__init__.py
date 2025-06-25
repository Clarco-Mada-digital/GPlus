"""
Package pour l'API REST du module stock.

Ce package contient les vues et sérialiseurs pour l'API REST 
permettant de gérer les produits, catégories, fournisseurs et mouvements de stock.
"""

# Import des vues API
from .views import (
    ProduitViewSet, CategorieViewSet, FournisseurViewSet,
    EntreeStockViewSet, SortieStockViewSet, MouvementStockViewSet
)

# Import des sérialiseurs
from .serializers import (
    ProduitSerializer, ProduitDetailSerializer,
    CategorieSerializer, FournisseurSerializer,
    EntreeStockSerializer, SortieStockSerializer,
    AjustementStockSerializer, UserSerializer
)

__all__ = [
    # Vues API
    'ProduitViewSet', 'CategorieViewSet', 'FournisseurViewSet',
    'EntreeStockViewSet', 'SortieStockViewSet', 'MouvementStockViewSet',
    
    # Sérialiseurs
    'ProduitSerializer', 'ProduitDetailSerializer',
    'CategorieSerializer', 'FournisseurSerializer',
    'EntreeStockSerializer', 'SortieStockSerializer',
    'AjustementStockSerializer', 'UserSerializer'
]
