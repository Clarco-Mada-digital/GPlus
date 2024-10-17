

from django.urls import path
from caisse import views


"""
Définit le modèle d'URL pour la vue de l'application caisse.
"""
urlpatterns = [
    path('', views.index, name="index"),
    #path('operations/', views.operations, name="operations"),  # Nouvelle URL
    path('listes/', views.listes, name="listes"),  # Nouvelle URL
    path('depenses/', views.depenses, name="depenses"),  # Nouvelle URL
    path('acteurs/', views.acteurs, name="acteurs"),  # Nouvelle URL
    path('operations/', views.ajouts_entree, name="operation"),
]