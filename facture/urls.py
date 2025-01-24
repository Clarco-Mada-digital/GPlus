from django.urls import path
from . import views

app_name='facture'

urlpatterns = [
  # Mes differents urls pour le facture et devies
  path('', views.index, name="index"),
  path('new/', views.facture, name="facture"),
  path('edit/<int:pk>/', views.modifier_facture, name="modifier_facture"),
  path('del/<int:pk>/', views.supprimer_facture, name="supprimer_facture"),  
  path('service/', views.service, name="service"),  # Lien pour la list des service
  path('new/service/', views.ajouter_service, name="new_service"), # Lien pur ajout d'service
  path('new/facture/', views.ajouter_facture, name="new_facture"), # Lien pur ajout de facture
  path('edit/<int:pk>/', views.modifier_facture, name="edit_facture"),
  path('del/<int:pk>/', views.supprimer_facture, name="del_facture"),  
  path('new/service/', views.ajouter_service, name="new_service"), # Lien pour ajout de service
  path('edit_service/<int:pk>/', views.modifier_service, name="edit_service"), # Lien pour modification de service
  path('del_service/<int:pk>/', views.supprimer_service, name="del_service"), # Lien pour supprimer de service
  path('new/devis/', views.ajouter_Devis, name="new_devis"), # Lien pur ajout de facture
  # path('settings/', views.ajouter_facture, name="new_facture"), # Lien pur ajout de facture
]