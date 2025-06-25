"""
Fichier de compatibilité pour les URLs de l'API.

Ce fichier est maintenu pour la rétrocompatibilité.
Les URLs de l'API sont maintenant définies dans le module api.urls.
"""

from django.urls import path, include
from .api.urls import urlpatterns as api_urls

# Liste des URLs de l'API
urlpatterns = api_urls
