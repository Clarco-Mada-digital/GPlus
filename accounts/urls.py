from django.urls import include, path
from accounts.views import index, logout_user, signup

"""
Ce partie définit les modèles d'URL pour l'application de comptes. 
Il sert de mécanisme de routage pour diriger les requêtes entrantes vers les vues appropriées.

"""

urlpatterns = [
    path("", index, name="index"),
    path("login", signup, name="login_user"),
    path("logout", logout_user, name="logout_user"),
]