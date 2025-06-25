"""
URLs pour l'API du module stock.

Ce module définit les routes URL pour l'API REST du module de gestion de stock.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProduitViewSet, CategorieViewSet, FournisseurViewSet,
    EntreeStockViewSet, SortieStockViewSet, MouvementStockViewSet
)

# Création d'un routeur pour les vues ViewSet
router = DefaultRouter()

# Enregistrement des vues avec le routeur
router.register(r'produits', ProduitViewSet, basename='produit')
router.register(r'categories', CategorieViewSet, basename='categorie')
router.register(r'fournisseurs', FournisseurViewSet, basename='fournisseur')
router.register(r'entrees', EntreeStockViewSet, basename='entree')
router.register(r'sorties', SortieStockViewSet, basename='sortie')

# URLs de l'API
urlpatterns = [
    # Inclure les URLs du routeur
    path('', include(router.urls)),
    
    # Endpoints supplémentaires pour les opérations sur les mouvements
    path('mouvements/ajuster/', 
        MouvementStockViewSet.as_view({'post': 'ajustement'}), 
        name='mouvement-ajuster'),
        
    path('mouvements/stats/', 
        MouvementStockViewSet.as_view({'get': 'stats'}), 
        name='mouvement-stats'),
]
