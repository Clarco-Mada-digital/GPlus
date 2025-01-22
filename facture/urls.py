from django.urls import path
from . import views

app_name='facture'

urlpatterns = [
  # Mes differents urls pour le facture et devies
  path('', views.index, name="index"),
  path('new/', views.facture, name="facture"),
  path('edit/<int:pk>/', views.modifier_facture, name="modifier_facture"),
  path('del/<int:pk>/', views.supprimer_facture, name="supprimer_facture"),  
  path('new/service/', views.ajouter_service, name="new_service"), # Lien pur ajout d'service
  path('new/facture/', views.ajouter_facture, name="new_facture"), # Lien pur ajout de facture
  # path('settings/', views.ajouter_facture, name="new_facture"), # Lien pur ajout de facture
]