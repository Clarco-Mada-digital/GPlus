from django.urls import path
from . import views


"""
Définit le modèle d'URL pour la vue de l'application caisse.
"""
urlpatterns = [
    path('', views.index, name="index"),
    path('operations/', views.operations, name="operations"),
    path('listes/', views.listes, name="listes"),
    path('depenses/', views.depenses, name="depenses"),
    path('acteurs/', views.acteurs, name="acteurs"),
    path('ajouter-acteur/', views.ajouter_acteur, name="ajouter_acteur"),
    path('ajouter-fournisseur/', views.ajouter_fournisseur, name="ajouter_fournisseur"),
    path('modifier-acteur/<str:type_acteur>/<int:pk>/', views.modifier_acteur, name="modifier_acteur"),
    path('supprimer-acteur/<str:type_acteur>/<int:pk>/', views.supprimer_acteur, name="supprimer_acteur"),
    path('ajouter-categorie/', views.ajouter_categorie, name="ajouter_categorie"),
    path('modifier-categorie/<int:pk>/', views.modifier_categorie, name="modifier_categorie"),
    path('supprimer-categorie/<int:pk>/', views.supprimer_categorie, name="supprimer_categorie"),
]
