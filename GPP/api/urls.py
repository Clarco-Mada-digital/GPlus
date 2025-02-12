# GPP/api/urls.py

from rest_framework import routers

from facture.api.views import FactureViewset, ClientViewSet

router = routers.SimpleRouter()

router.register('facture', FactureViewset, basename='facture')
router.register('facture-client', ClientViewSet, basename='facture_client')