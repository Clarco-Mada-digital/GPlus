# GPP/api/urls.py

from rest_framework import routers
from django.urls import path, include

from facture.api.views import FactureViewset, FactureServiceViewset, UserViewset, EntrepriseViewset

router = routers.SimpleRouter()

router.register('facture', FactureViewset, basename='facture')
router.register('facture-service', FactureServiceViewset, basename='facture-service')
router.register('facture-user', UserViewset, basename='facture-user')
router.register('facture-entreprise',EntrepriseViewset,  basename='facture-entreprise')


# Définir les urlpatterns pour inclure à la fois le router et d'autres URLs
urlpatterns = router.urls + [
    # Inclure les URLs de l'API caisse
    # path('caisse/', include('caisse.api_urls')),
]