from django.urls import path
from . import views

app_name='caisse'
"""
Définit le modèle d'URL pour la vue de l'application caisse.
"""
urlpatterns = [
    # Pages principales
    path('', views.index, name="index"), # Affiche le tableau de bord
    path('operations/', views.operations, name="operation"), # Ajouts des opérations (entrées et sorties)
    path('listes/', views.listes, name="listes"), # Liste toutes les opérations
    path('depenses/', views.depenses, name="depenses"), # Gère les dépenses
    
    # Gestion des acteurs
    path('acteurs/', views.acteurs, name="acteurs"),  # Affiche la liste des acteurs
    path('acteurs/ajouter/', views.ajouter_acteur, name="ajouter_acteur"),  # Ajoute un nouvel acteur
    path('acteurs/ajouter-fournisseur/', views.ajouter_fournisseur, name="ajouter_fournisseur"),  # Ajoute un fournisseur comme acteur
    path('acteurs/modifier/<str:type_acteur>/<int:pk>/', views.modifier_acteur, name="modifier_acteur"),  # Modifie un acteur existant
    path('acteurs/supprimer/<str:type_acteur>/<int:pk>/', views.supprimer_acteur, name="supprimer_acteur"),  # Supprime un acteur
    path('acteurs/editer/<str:type_acteur>/<int:pk>/', views.editer_acteur, name="editer_acteur"),  # Édite un acteur
    
    # Gestion des catégories
    path('categories/', views.categories, name="categories"),  # Affiche la liste des catégories
    path('categories/ajouter/', views.ajouter_categorie, name="ajouter_categorie"),  # Ajoute une nouvelle catégorie
    path('categories/modifier/<int:pk>/', views.modifier_categorie, name="modifier_categorie"),  # Modifie une catégorie existante
    path('categories/supprimer/<int:pk>/', views.supprimer_categorie, name="supprimer_categorie"),  # Supprime une catégorie
    path('categories/creer/', views.creer_categorie, name="creer_categorie"),  # Crée une nouvelle catégorie
    path('categories/editer/<int:pk>/', views.editer_categorie, name="editer_categorie"),  # Édite une catégorie
    
    # Opérations financières
    path('ajouts-entree/', views.ajouts_entree, name="ajouts_entree"),  # Ajoute une nouvelle entrée financière
    path('ajouts-sortie/', views.ajouts_sortie, name="ajouts_sortie"),  # Ajoute une nouvelle sortie financière
    path('entrees/', views.liste_entrees, name='liste_entrees'),  # Affiche la liste des entrées financières
    path('sorties/', views.liste_sorties, name='liste_sorties'),  # Affiche la liste des sorties financières
    path('operations/modifier/entree/<int:pk>/', views.modifier_entree, name='modifier_entree'),  # Modifie une entrée financière existante
    path('operations/modifier/sortie/<int:pk>/', views.modifier_sortie, name='modifier_sortie'),  # Modifie une sortie financière existante
    path('caisse/operations/supprimer_sortir/<int:pk>/', views.supprimer_sortie, name="supprimer_sortie"),  # Supprime une sortie financière
    path('caisse/operations/supprimer_entrer/<int:pk>/', views.supprimer_entree, name="supprimer_entree"),  # Supprime une entrée financière

    path('operations/', views.operations, name="operations"),  # Nouvelle URL
    
    # Paramètres 
    path('parametres/', views.parametres, name="parametres"),
    
    # Gestion des utilisateurs
    path('utilisateurs/', views.utilisateurs, name='utilisateurs'),  # Affiche la liste des utilisateurs
    path('utilisateurs/creer/', views.creer_utilisateur, name='creer_utilisateur'),  # Crée un nouvel utilisateur
    path('utilisateurs/modifier/<int:pk>/', views.modifier_utilisateur, name='modifier_utilisateur'),  # Modifie un utilisateur existant
    path('utilisateurs/supprimer/<int:pk>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),  # Supprime un utilisateur
    path('utilisateurs/editer/<int:pk>/', views.editer_utilisateur, name='editer_utilisateur'),  # Édite un utilisateur
    
    #Historique
    path('historique/', views.historique, name='historique'),
    path('parametres/update-profile/', views.update_profile, name='update_profile'),
    path('parametres/change-password/', views.change_password, name='change_password'),
    
    #Pour générer un rapport en EXCEL (.xlsx)
    path('export/excel/', views.generer_excel_operations, name='generer_excel_operations'), 
    path('export-entree/excel/', views.generer_excel_operations_entrees, name='generer_excel_operations_entrees'),
    path('export-sortie/excel/',views.generer_excel_operations_sorties, name="generer_excel_operations_sorties"),
  
     # Ajouter ces nouvelles URLs dans urlpatterns
    path('details/entrees/', views.details_entrees, name='details_entrees'),
    path('details/sorties/', views.details_sorties, name='details_sorties'),
    path('details/solde/', views.details_solde, name='details_solde'),
    # API de vérification pour l'ajouts des opérations
    path('ajouter-element/', views.ajouter_element, name='ajouter_element'),
    
    # Routes API pour la vérification
    path('api/verifier-categorie/<str:id>/', views.verifier_categorie, name='verifier_categorie'),
    path('api/verifier-beneficiaire/<str:id>/', views.verifier_beneficiaire, name='verifier_beneficiaire'),
    path('api/verifier-fournisseur/<str:id>/', views.verifier_fournisseur, name='verifier_fournisseur'),
    
    # Gestion des bénéficiaires
    path('beneficiaires/', views.beneficiaires, name='beneficiaires'),
    path('beneficiaires/creer/', views.creer_beneficiaire, name='creer_beneficiaire'),
    path('beneficiaires/modifier/<int:pk>/', views.modifier_beneficiaire, name='modifier_beneficiaire'),
    path('beneficiaires/supprimer/<int:pk>/', views.supprimer_beneficiaire, name='supprimer_beneficiaire'),
    path('beneficiaires/editer/<int:pk>/', views.editer_beneficiaire, name='editer_beneficiaire'),
]
