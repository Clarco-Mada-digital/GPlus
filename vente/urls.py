from django.urls import path
from . import views

app_name = 'vente'

urlpatterns = [
    path('', views.index, name='index'),
    path('historique/', views.HistoriqueVenteView.as_view(), name='historique_vente'),
    path('rapports/', views.RapportsView.as_view(), name='rapports'),
    path('vente/<int:vente_id>/', views.DetailVenteView.as_view(), name='detail_vente'),
    path('api/produits/suggestions/', views.ProduitSuggestionsView.as_view(), name='produit_suggestions'),
    path('api/valider-vente/', views.valider_vente, name='valider_vente'),
    path('api/rapports/ventes-par-jour/', views.ventes_par_jour, name='api_ventes_par_jour'),
    path('api/rapports/ventes-par-categorie/', views.ventes_par_categorie, name='api_ventes_par_categorie'),
    path('api/rapports/meilleurs-produits/', views.meilleurs_produits, name='api_meilleurs_produits'),
    path('api/annuler-vente/<str:reference>/', views.annuler_vente, name='annuler_vente'),
]
