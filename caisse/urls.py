

from django.urls import path
from caisse import views


"""
Définit le modèle d'URL pour la vue de l'application caisse.
"""
urlpatterns = [
    path('', views.index, name="index"),
]