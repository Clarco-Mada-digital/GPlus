from django.urls import path
from . import views


"""
Définit le modèle d'URL pour la vue de l'application caisse.
"""
urlpatterns = [
    # Pages principales
    path('', views.index, name="index"),
    path('operations/', views.operations, name="operation"),
    path('listes/', views.listes, name="listes"),
    path('depenses/', views.depenses, name="depenses"),
    
    # Gestion des acteurs
    path('acteurs/', views.acteurs, name="acteurs"),
    path('acteurs/ajouter/', views.ajouter_acteur, name="ajouter_acteur"),
    path('acteurs/ajouter-fournisseur/', views.ajouter_fournisseur, name="ajouter_fournisseur"),
    path('acteurs/modifier/<str:type_acteur>/<int:pk>/', views.modifier_acteur, name="modifier_acteur"),
    path('acteurs/supprimer/<str:type_acteur>/<int:pk>/', views.supprimer_acteur, name="supprimer_acteur"),
    
    # Gestion des catégories
    path('categories/', views.categories, name="categories"),
    path('categories/ajouter/', views.ajouter_categorie, name="ajouter_categorie"),
    path('categories/modifier/<int:pk>/', views.modifier_categorie, name="modifier_categorie"),
    path('categories/supprimer/<int:pk>/', views.supprimer_categorie, name="supprimer_categorie"),
    
    # Opérations financières
    path('ajouts-entree/', views.ajouts_entree, name="ajouts_entree"),



    path('operations/', views.operations, name="operations"),  # Nouvelle URL
]
