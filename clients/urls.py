from django.urls import path
from . import views

app_name='client'

urlpatterns = [
  # Mes differents urls pour le facture et devies
  path('', views.index, name="index"),
  path('list/', views.client_list, name="client"),
  path('new/', views.new_client, name="new_client"),
  path('edit/<int:pk>/', views.edit_client, name="edit_client"),
  path('del/<int:pk>/', views.supprimer_client, name="del_client"),
]