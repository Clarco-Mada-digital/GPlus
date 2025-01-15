from django.urls import path
from . import views

app_name='client'

urlpatterns = [
  # Mes differents urls pour le facture et devies
  path('', views.index, name="index"),
  path('client/', views.client, name="client"),
]