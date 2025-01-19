from django.urls import path
from . import views

app_name='facture'

urlpatterns = [
  # Mes differents urls pour le facture et devies
  path('', views.index, name="index"),
  path('facture/', views.facture, name="facture"),
]