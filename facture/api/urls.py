from rest_framework import routers

from facture.api.views import FactureViewset

router = routers.SimpleRouter()

router.register('facture', FactureViewset, basename='facture')