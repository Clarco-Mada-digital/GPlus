from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from . import views
from .views.accueil import get_chart_data
from .api_urls import urlpatterns as api_urls

app_name = 'stock'

urlpatterns = [
    # Tableau de bord
    path('', login_required(views.accueil.TableauBordView.as_view()), name='tableau_bord'),
    
    # Produits
    path('produits/', login_required(views.produits.ListeProduitsView.as_view()), name='liste_produits'),
    path('produits/ajouter/', login_required(views.produits.AjouterProduitView.as_view()), name='ajouter_produit'),
    path('produits/<int:pk>/', login_required(views.produits.DetailProduitView.as_view()), name='detail_produit'),
    path('produits/modifier/<int:pk>/', login_required(views.produits.ModifierProduitView.as_view()), name='modifier_produit'),
    path('produits/supprimer/<int:pk>/', login_required(views.produits.SupprimerProduitView.as_view()), name='supprimer_produit'),
    path('produits/stock-faible/', login_required(views.produits.StockFaibleView.as_view()), name='stock_faible'),
    
    # Catégories
    path('categories/', login_required(views.categories.ListeCategoriesView.as_view()), name='liste_categories'),
    path('categories/ajouter/', login_required(views.categories.AjouterCategorieView.as_view()), name='ajouter_categorie'),
    path('categories/modifier/<int:pk>/', login_required(views.categories.ModifierCategorieView.as_view()), name='modifier_categorie'),
    path('categories/supprimer/<int:pk>/', login_required(views.categories.SupprimerCategorieView.as_view()), name='supprimer_categorie'),
    
    # Fournisseurs
    path('fournisseurs/', login_required(views.fournisseurs.ListeFournisseursView.as_view()), name='liste_fournisseurs'),
    path('fournisseurs/ajouter/', login_required(views.fournisseurs.AjouterFournisseurView.as_view()), name='ajouter_fournisseur'),
    path('fournisseurs/<int:pk>/', login_required(views.fournisseurs.DetailFournisseurView.as_view()), name='detail_fournisseur'),
    path('fournisseurs/modifier/<int:pk>/', login_required(views.fournisseurs.ModifierFournisseurView.as_view()), name='modifier_fournisseur'),
    path('fournisseurs/supprimer/<int:pk>/', login_required(views.fournisseurs.SupprimerFournisseurView.as_view()), name='supprimer_fournisseur'),
    
    # Mouvements de stock
    path('entrees/', login_required(views.mouvements.ListeEntreesView.as_view()), name='liste_entrees'),
    path('entrees/ajouter/', login_required(views.mouvements.AjouterEntreeView.as_view()), name='ajouter_entree'),
    path('entrees/<int:pk>/', login_required(views.mouvements.DetailEntreeView.as_view()), name='detail_entree'),
    path('entrees/modifier/<int:pk>/', login_required(views.mouvements.ModifierEntreeView.as_view()), name='modifier_entree'),
    path('entrees/annuler/<int:pk>/', login_required(views.mouvements.AnnulerEntreeView.as_view()), name='annuler_entree'),
    path('sorties/', login_required(views.mouvements.ListeSortiesView.as_view()), name='liste_sorties'),
    path('sorties/ajouter/', login_required(views.mouvements.AjouterSortieView.as_view()), name='ajouter_sortie'),
    path('sorties/<int:pk>/', login_required(views.mouvements.DetailSortieView.as_view()), name='detail_sortie'),
    path('sorties/modifier/<int:pk>/', login_required(views.mouvements.ModifierSortieView.as_view()), name='modifier_sortie'),
    path('sorties/annuler/<int:pk>/', login_required(views.mouvements.AnnulerSortieView.as_view()), name='annuler_sortie'),
    
    # Historique et rapports
    path('historique/', login_required(views.historique.HistoriqueMouvementsView.as_view()), name='historique'),
    path('rapports/etat-stock/', login_required(views.rapports.EtatStockView.as_view()), name='etat_stock'),
    path('rapports/mouvements/', login_required(views.rapports.RapportMouvementsView.as_view()), name='rapport_mouvements'),
    
    # API et données
    path('api/', include(api_urls)),
    path('api/chart-data/', get_chart_data, name='chart_data'),
    
    # Rapports
    path('rapports/stock-faible/', login_required(views.produits.StockFaibleView.as_view()), name='rapport_stock_faible'),
    path('rapports/mouvements/', login_required(views.rapports.RapportMouvementsView.as_view()), name='rapport_mouvements'),
    path('rapports/', TemplateView.as_view(template_name='stock/rapports/accueil.html'), name='rapports'),
]
