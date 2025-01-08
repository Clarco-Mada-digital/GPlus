from django.urls import path
from .api_views import (
    CategorieListCreate, CategorieRetrieveUpdateDestroy, CategorieDetailView,
    OperationEntrerListCreate, OperationEntrerRetrieveUpdateDestroy,
    OperationSortirListCreate, OperationSortirRetrieveUpdateDestroy,
    PersonnelListCreate, PersonnelRetrieveUpdateDestroy,
    FournisseurListCreate, FournisseurRetrieveUpdateDestroy,
    BeneficiaireListCreate, BeneficiaireRetrieveUpdateDestroy,
    TableauBordResume
)

urlpatterns = [
    # URLs pour les catégories
    path('categories/', CategorieListCreate.as_view(), name='categorie-list-create'),
    path('categories/<int:pk>/', CategorieRetrieveUpdateDestroy.as_view(), name='categorie-retrieve-update-destroy'),
    path('categories/<int:pk>/detail/', CategorieDetailView.as_view(), name='categorie-detail'),

    # URLs pour les opérations d'entrée
    path('operations-entrer/', OperationEntrerListCreate.as_view(), name='operation-entrer-list-create'),
    path('operations-entrer/<int:pk>/', OperationEntrerRetrieveUpdateDestroy.as_view(), name='operation-entrer-retrieve-update-destroy'),

    # URLs pour les opérations de sortie
    path('operations-sortir/', OperationSortirListCreate.as_view(), name='operation-sortir-list-create'),
    path('operations-sortir/<int:pk>/', OperationSortirRetrieveUpdateDestroy.as_view(), name='operation-sortir-retrieve-update-destroy'),

    # URLs pour le personnel
    path('personnel/', PersonnelListCreate.as_view(), name='personnel-list-create'),
    path('personnel/<int:pk>/', PersonnelRetrieveUpdateDestroy.as_view(), name='personnel-retrieve-update-destroy'),

    # URLs pour les fournisseurs
    path('fournisseurs/', FournisseurListCreate.as_view(), name='fournisseur-list-create'),
    path('fournisseurs/<int:pk>/', FournisseurRetrieveUpdateDestroy.as_view(), name='fournisseur-retrieve-update-destroy'),

    # URLs pour les bénéficiaires
    path('beneficiaires/', BeneficiaireListCreate.as_view(), name='beneficiaire-list-create'),
    path('beneficiaires/<int:pk>/', BeneficiaireRetrieveUpdateDestroy.as_view(), name='beneficiaire-retrieve-update-destroy'),

    path('tableau-bord/resume/', TableauBordResume.as_view(), name='tableau-bord-resume'),
]