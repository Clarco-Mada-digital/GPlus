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
    path('entrees/', views.liste_entrees, name='liste_entrees'),
    path('sorties/', views.liste_sorties, name='liste_sorties'),
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
    path('parametres/update-profile/', views.update_profile, name='update_profile'),
    path('parametres/change-password/', views.change_password, name='change_password'),
    
    #Pour générer un rapport en EXCEL (.xlsx)
    path('export/excel/', views.generer_excel_operations, name='generer_excel_operations'), 
    path('export-entree/excel/', views.generer_excel_operations_entrees, name='generer_excel_operations_entrees'),
    path('export-sortie/excel/',views.generer_excel_operations_sorties, name="generer_excel_operations_sorties"),
    # Ajouter ces lignes dans urlpatterns
    path('beneficiaires/', views.beneficiaires, name='beneficiaires'),
    path('beneficiaires/creer/', views.creer_beneficiaire, name='creer_beneficiaire'),
    path('beneficiaires/modifier/<int:pk>/', views.modifier_beneficiaire, name='modifier_beneficiaire'),
    path('beneficiaires/supprimer/<int:pk>/', views.supprimer_beneficiaire, name='supprimer_beneficiaire'),
    path('beneficiaires/editer/<int:pk>/', views.editer_beneficiaire, name='editer_beneficiaire'),
]
