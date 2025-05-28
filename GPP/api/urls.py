# GPP/api/urls.py

from rest_framework import routers

from facture.api.views import FactureViewset, FactureServiceViewset

router = routers.SimpleRouter()

router.register('facture', FactureViewset, basename='facture')
router.register('facture-service', FactureServiceViewset, basename='facture-service')