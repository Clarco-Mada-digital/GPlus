from django.urls import path
from . import views

app_name='caisse'
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
    path('acteurs/editer/<str:type_acteur>/<int:pk>/', views.editer_acteur, name="editer_acteur"),
    
    # Gestion des catégories
    path('categories/', views.categories, name="categories"),
    path('categories/ajouter/', views.ajouter_categorie, name="ajouter_categorie"),
    path('categories/modifier/<int:pk>/', views.modifier_categorie, name="modifier_categorie"),
    path('categories/supprimer/<int:pk>/', views.supprimer_categorie, name="supprimer_categorie"),
    path('categories/creer/', views.creer_categorie, name="creer_categorie"),
    path('categories/editer/<int:pk>/', views.editer_categorie, name="editer_categorie"),
    
    # Opérations financières
    path('ajouts-entree/', views.ajouts_entree, name="ajouts_entree"),
    path('ajouts-sortie/', views.ajouts_sortie, name="ajouts_sortie"),
    
    path('operations/modifier/entree/<int:pk>/', views.modifier_entree, name='modifier_entree'),
    path('operations/modifier/sortie/<int:pk>/', views.modifier_sortie, name='modifier_sortie'),
    path('caisse/operations/supprimer_entrer/<int:pk>/', views.supprimer_entree, name="supprimer_entree"),
    path('caisse/operations/supprimer_sortir/<int:pk>/', views.supprimer_sortie, name="supprimer_sortie"),

    path('operations/', views.operations, name="operations"),  # Nouvelle URL
    
    
    path('parametres/', views.parametres, name="parametres"),
    # Ajouter ces lignes aux patterns existants
    path('utilisateurs/', views.utilisateurs, name='utilisateurs'),
    path('utilisateurs/creer/', views.creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/modifier/<int:pk>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/supprimer/<int:pk>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    # Ajouter cette ligne aux patterns existants
    path('utilisateurs/editer/<int:pk>/', views.editer_utilisateur, name='editer_utilisateur'),
    
    #Historique
    path('historique/', views.historique, name='historique'),
]
