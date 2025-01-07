from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Categorie, OperationEntrer, OperationSortir, Personnel, Fournisseur, Beneficiaire
from .serializers import (
    CategorieSerializer, CategorieDetailSerializer,
    OperationEntrerSerializer, OperationEntrerCreateSerializer,
    OperationSortirSerializer, OperationSortirCreateSerializer,
    PersonnelSerializer, PersonnelDetailSerializer,
    FournisseurSerializer, FournisseurDetailSerializer,
    BeneficiaireSerializer, BeneficiaireDetailSerializer,
)
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.utils import timezone


# Vues pour le modèle Categorie
class CategorieListCreate(generics.ListCreateAPIView):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer



class CategorieRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer

class CategorieDetailView(generics.RetrieveAPIView):
    queryset = Categorie.objects.all()
    serializer_class = CategorieDetailSerializer

# Vues pour le modèle OperationEntrer
class OperationEntrerListCreate(generics.ListCreateAPIView):
    queryset = OperationEntrer.objects.all()

    filterset_fields = ['categorie', 'date_transaction']
    search_fields = ['description']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OperationEntrerCreateSerializer
        return OperationEntrerSerializer

class OperationEntrerRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = OperationEntrer.objects.all()
    serializer_class = OperationEntrerSerializer
    
# Vues pour le modèle OperationSortir
class OperationSortirListCreate(generics.ListCreateAPIView):
    queryset = OperationSortir.objects.all()

    filterset_fields = ['categorie', 'date_de_sortie', 'fournisseur', 'beneficiaire']
    search_fields = ['description']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OperationSortirCreateSerializer
        return OperationSortirSerializer

class OperationSortirRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = OperationSortir.objects.all()
    serializer_class = OperationSortirSerializer

# Vues pour le modèle Personnel
class PersonnelListCreate(generics.ListCreateAPIView):
    queryset = Personnel.objects.all()
    serializer_class = PersonnelSerializer

class PersonnelRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Personnel.objects.all()
    serializer_class = PersonnelDetailSerializer

# Vues pour le modèle Fournisseur
class FournisseurListCreate(generics.ListCreateAPIView):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer

class FournisseurRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurDetailSerializer

# Vues pour le modèle Beneficiaire
class BeneficiaireListCreate(generics.ListCreateAPIView):
    queryset = Beneficiaire.objects.all()
    serializer_class = BeneficiaireSerializer

class BeneficiaireRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Beneficiaire.objects.all()
    serializer_class = BeneficiaireDetailSerializer

class TableauBordResume(APIView):
    def get(self, request):
        # Calculer la date il y a 12 mois
        date_debut = timezone.now() - timedelta(days=365)
        
        # Résumé global
        total_entrees = OperationEntrer.objects.aggregate(total=Sum('montant'))['total'] or 0
        total_sorties = OperationSortir.objects.aggregate(total=Sum('montant'))['total'] or 0
        nombre_transactions = OperationEntrer.objects.count() + OperationSortir.objects.count()
        
        # Transactions par mois
        entrees_par_mois = OperationEntrer.objects.filter(
            date_transaction__gte=date_debut
        ).annotate(
            mois=TruncMonth('date_transaction')
        ).values('mois').annotate(
            total_entrees=Sum('montant'),
            nombre_transactions=Count('id')
        ).order_by('mois')

        sorties_par_mois = OperationSortir.objects.filter(
            date_de_sortie__gte=date_debut
        ).annotate(
            mois=TruncMonth('date_de_sortie')
        ).values('mois').annotate(
            total_sorties=Sum('montant'),
            nombre_transactions=Count('id')
        ).order_by('mois')

        # Transactions par catégorie
        categories_stats = Categorie.objects.annotate(
            total_entrees=Sum('operationentrer__montant'),
            total_sorties=Sum('operationsortir__montant'),
            nombre_entrees=Count('operationentrer'),
            nombre_sorties=Count('operationsortir')
        )

        # Préparer les données par mois
        transactions_par_mois = []
        solde_cumule = 0
        
        # Créer un dictionnaire des sorties par mois pour un accès facile
        sorties_dict = {s['mois'].strftime('%Y-%m'): s for s in sorties_par_mois}
        
        for entree in entrees_par_mois:
            mois_str = entree['mois'].strftime('%Y-%m')
            sortie = sorties_dict.get(mois_str, {'total_sorties': 0, 'nombre_transactions': 0})
            
            reste_mois = entree['total_entrees'] - sortie['total_sorties']
            solde_cumule += reste_mois
            
            # Détails des catégories pour ce mois
            details_categories = []
            for cat in categories_stats:
                entrees_cat = OperationEntrer.objects.filter(
                    categorie=cat,
                    date_transaction__month=entree['mois'].month,
                    date_transaction__year=entree['mois'].year
                ).aggregate(total=Sum('montant'), count=Count('id'))
                
                sorties_cat = OperationSortir.objects.filter(
                    categorie=cat,
                    date_de_sortie__month=entree['mois'].month,
                    date_de_sortie__year=entree['mois'].year
                ).aggregate(total=Sum('montant'), count=Count('id'))
                
                if entrees_cat['total'] or sorties_cat['total']:
                    details_categories.append({
                        'categorie': cat.name,
                        'type': cat.type,
                        'total': entrees_cat['total'] or sorties_cat['total'] or 0,
                        'nombre_transactions': entrees_cat['count'] + sorties_cat['count']
                    })
            
            transactions_par_mois.append({
                'mois': mois_str,
                'total_entrees': entree['total_entrees'],
                'total_sorties': sortie['total_sorties'],
                'reste_mois': reste_mois,
                'solde_cumule': solde_cumule,
                'details_categories': details_categories
            })

        # Préparer les transactions par catégorie
        transactions_par_categorie = []
        for cat in categories_stats:
            details_mois = []
            for mois in entrees_par_mois:
                mois_data = {
                    'mois': mois['mois'].strftime('%Y-%m'),
                    'total': 0,
                    'nombre_transactions': 0
                }
                if cat.type == 'entree':
                    total = OperationEntrer.objects.filter(
                        categorie=cat,
                        date_transaction__month=mois['mois'].month,
                        date_transaction__year=mois['mois'].year
                    ).aggregate(total=Sum('montant'), count=Count('id'))
                else:
                    total = OperationSortir.objects.filter(
                        categorie=cat,
                        date_de_sortie__month=mois['mois'].month,
                        date_de_sortie__year=mois['mois'].year
                    ).aggregate(total=Sum('montant'), count=Count('id'))
                
                if total['total']:
                    mois_data.update({
                        'total': total['total'],
                        'nombre_transactions': total['count']
                    })
                    details_mois.append(mois_data)
            
            if details_mois:
                transactions_par_categorie.append({
                    'categorie': cat.name,
                    'type': cat.type,
                    'total': cat.total_entrees or cat.total_sorties or 0,
                    'nombre_transactions': cat.nombre_entrees + cat.nombre_sorties,
                    'details_mois': details_mois
                })

        # Calculer les indicateurs clés
        moyenne_entrees = OperationEntrer.objects.aggregate(avg=Avg('montant'))['avg'] or 0
        moyenne_sorties = OperationSortir.objects.aggregate(avg=Avg('montant'))['avg'] or 0
        
        # Trouver la catégorie la plus utilisée
        categorie_plus_utilisee = max(
            categories_stats,
            key=lambda x: (x.nombre_entrees + x.nombre_sorties)
        ).name if categories_stats else None

        # Trouver le mois le plus actif
        mois_plus_actif = max(
            transactions_par_mois,
            key=lambda x: x['total_entrees'] + x['total_sorties']
        )['mois'] if transactions_par_mois else None

        return Response({
            'resume_global': {
                'total_entrees': total_entrees,
                'total_sorties': total_sorties,
                'solde_net': total_entrees - total_sorties,
                'nombre_transactions': nombre_transactions
            },
            'transactions_par_mois': transactions_par_mois,
            'transactions_par_categorie': transactions_par_categorie,
            'indicateurs_cles': {
                'moyenne_entrees_mensuelles': moyenne_entrees,
                'moyenne_sorties_mensuelles': moyenne_sorties,
                'categorie_plus_utilisee': categorie_plus_utilisee,
                'mois_plus_actif': mois_plus_actif
            }
        })