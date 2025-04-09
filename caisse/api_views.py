from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Categorie, OperationEntrer, OperationSortir, Personnel, Fournisseur, Beneficiaire
from .serializers import (
    CategorieSerializer, CategorieDetailSerializer,
    OperationEntrerSerializer, OperationEntrerCreateSerializer,
    OperationEntrerUpdateSerializer,
    OperationSortirSerializer, OperationSortirCreateSerializer,
    OperationSortirUpdateSerializer,
    PersonnelSerializer, PersonnelDetailSerializer,
    FournisseurSerializer, FournisseurDetailSerializer,
    BeneficiaireSerializer, BeneficiaireDetailSerializer,
)
from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncMonth, TruncYear
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.utils import timezone
from collections import defaultdict
from django.utils.dateparse import parse_date
from babel.dates import format_date


# Vues pour le modèle Categorie
class CategorieListCreate(generics.ListCreateAPIView):
    queryset = Categorie.objects.all().order_by('-id')
    serializer_class = CategorieSerializer



class CategorieRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer

class CategorieDetailView(generics.RetrieveAPIView):
    queryset = Categorie.objects.all()
    serializer_class = CategorieDetailSerializer

# Vues pour le modèle OperationEntrer
class OperationEntrerListCreate(generics.ListCreateAPIView):
    queryset = OperationEntrer.objects.all().order_by('-date_transaction')
    filterset_fields = ['categorie', 'date_transaction', 'beneficiaire', 'client']
    search_fields = ['description']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OperationEntrerCreateSerializer
        return OperationEntrerSerializer

class OperationEntrerRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = OperationEntrer.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return OperationEntrerUpdateSerializer
        return OperationEntrerSerializer

# Vues pour le modèle OperationSortir
class OperationSortirListCreate(generics.ListCreateAPIView):
    queryset = OperationSortir.objects.all().order_by('-date_de_sortie')
    filterset_fields = ['categorie', 'date_de_sortie', 'fournisseur', 'beneficiaire']
    search_fields = ['description']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OperationSortirCreateSerializer
        return OperationSortirSerializer

class OperationSortirRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = OperationSortir.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return OperationSortirUpdateSerializer
        return OperationSortirSerializer

# Vues pour le modèle Personnel
class PersonnelListCreate(generics.ListCreateAPIView):
    queryset = Personnel.objects.all().order_by('-id')
    serializer_class = PersonnelSerializer

class PersonnelRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Personnel.objects.all()
    serializer_class = PersonnelDetailSerializer

# Vues pour le modèle Fournisseur
class FournisseurListCreate(generics.ListCreateAPIView):
    queryset = Fournisseur.objects.all().order_by('-id')
    serializer_class = FournisseurSerializer

class FournisseurRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurDetailSerializer

# Vues pour le modèle Beneficiaire
class BeneficiaireListCreate(generics.ListCreateAPIView):
    queryset = Beneficiaire.objects.all().order_by('-id')
    serializer_class = BeneficiaireSerializer

class BeneficiaireRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Beneficiaire.objects.all()
    serializer_class = BeneficiaireDetailSerializer

class TableauBordResume(APIView):
    def get(self, request):
        """Vue API du tableau de bord"""
        today = timezone.now()
        
        # Obtenir l'année sélectionnée (par défaut, l'année en cours)
        selected_year = int(request.GET.get('year', today.year))
        
        # Calculer le premier et dernier jour de l'année sélectionnée
        first_day_of_year = datetime(selected_year, 1, 1)
        last_day_of_year = datetime(selected_year, 12, 31)
        
        # Calculer les totaux de l'année sélectionnée
        total_entrees_mois = OperationEntrer.objects.filter(
            date_transaction__gte=first_day_of_year,
            date_transaction__lte=last_day_of_year
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        total_sorties_mois = OperationSortir.objects.filter(
            date_de_sortie__gte=first_day_of_year,
            date_de_sortie__lte=last_day_of_year
        ).aggregate(Sum('montant'))['montant__sum'] or 0
        
        # Données des entrées par mois
        entrees_par_mois = list(OperationEntrer.objects.filter(
            date_transaction__gte=first_day_of_year,
            date_transaction__lte=last_day_of_year
        ).annotate(
            mois=TruncMonth('date_transaction')
        ).values('mois').annotate(
            total=Sum('montant')
        ).order_by('mois'))

        # Données des sorties par mois
        sorties_par_mois = list(OperationSortir.objects.filter(
            date_de_sortie__gte=first_day_of_year,
            date_de_sortie__lte=last_day_of_year
        ).annotate(
            mois=TruncMonth('date_de_sortie')
        ).values('mois').annotate(
            total=Sum('montant')
        ).order_by('mois'))

        # Créer un dictionnaire pour faciliter l'accès aux totaux par mois
        entrees_dict = {item['mois'].strftime('%Y-%m'): item['total'] or 0 for item in entrees_par_mois}
        sorties_dict = {item['mois'].strftime('%Y-%m'): item['total'] or 0 for item in sorties_par_mois}

        # Obtenir tous les mois uniques
        all_months = sorted(set(entrees_dict.keys()) | set(sorties_dict.keys()))

        # Calculer les soldes cumulatifs
        solde_cumule = 0
        soldes_par_mois = []
        formatted_entrees = []
        formatted_sorties = []
        
        # Calculer le solde initial
        solde_initial = (
            OperationEntrer.objects.filter(date_transaction__lt=first_day_of_year).aggregate(Sum('montant'))['montant__sum'] or 0
        ) - (
            OperationSortir.objects.filter(date_de_sortie__lt=first_day_of_year).aggregate(Sum('montant'))['montant__sum'] or 0
        )
        
        solde_cumule = solde_initial

        for mois_str in all_months:
            mois_date = datetime.strptime(mois_str, '%Y-%m')
            entree_mois = entrees_dict.get(mois_str, 0)
            sortie_mois = sorties_dict.get(mois_str, 0)
            solde_mois = entree_mois - sortie_mois
            solde_cumule += solde_mois
            
            mois_format = format_date(mois_date, format='MMMM yyyy', locale='fr_FR')
            
            soldes_par_mois.append({
                'mois': mois_format,
                'solde': float(solde_cumule)
            })
            formatted_entrees.append({
                'mois': mois_format,
                'total': float(entree_mois)
            })
            formatted_sorties.append({
                'mois': mois_format,
                'total': float(sortie_mois)
            })

        # Données pour le graphique des catégories de sorties
        sorties_categories = list(OperationSortir.objects.filter(
            date_de_sortie__gte=first_day_of_year,
            date_de_sortie__lte=last_day_of_year
        ).values(
            'categorie__name'
        ).annotate(
            total=Sum('montant')
        ).order_by('-total')[:5])

        # Formater les données des catégories
        formatted_categories = [{
            'categorie': item['categorie__name'],
            'total': float(item['total'] or 0)
        } for item in sorties_categories]

        return Response({
            'solde_actuel': float(solde_cumule),
            'total_entrees': float(total_entrees_mois),
            'total_sorties': float(total_sorties_mois),
            'entrees_par_mois': formatted_entrees,
            'sorties_par_mois': formatted_sorties,
            'soldes_par_mois': soldes_par_mois,
            'sorties_categories': formatted_categories,
            'entrees_4_mois': formatted_entrees[-4:][::-1] if formatted_entrees else [],
            'selected_year': selected_year,
            'years': list(range(today.year - 5, today.year + 1))
        })

class DetailsEntreesAPI(APIView):
    def get(self, request):
        selected_year = int(request.GET.get('year', timezone.now().year))
        
        entrees = OperationEntrer.objects.filter(
            date_transaction__year=selected_year
        ).annotate(
            mois=TruncMonth('date_transaction')
        ).values('mois').annotate(
            total=Sum('montant'),
            nombre_operations=Count('id')
        ).order_by('-mois')

        data = []
        for entree in entrees:
            operations = OperationEntrer.objects.filter(
                date_transaction__month=entree['mois'].month,
                date_transaction__year=entree['mois'].year
            ).order_by('-date_transaction')
            
            data.append({
                'mois': entree['mois'].strftime('%Y-%m'),
                'mois_format': format_date(entree['mois'], format='MMMM yyyy', locale='fr_FR'),
                'total': entree['total'],
                'nombre_operations': entree['nombre_operations'],
                'operations': OperationEntrerSerializer(operations, many=True).data
            })

        return Response({
            'entrees': data,
            'total_general': sum(entree['total'] for entree in entrees),
            'selected_year': selected_year
        })

class DetailsSortiesAPI(APIView):
    def get(self, request):
        selected_year = int(request.GET.get('year', timezone.now().year))
        
        sorties = OperationSortir.objects.filter(
            date_de_sortie__year=selected_year
        ).annotate(
            mois=TruncMonth('date_de_sortie')
        ).values('mois').annotate(
            total=Sum('montant'),
            nombre_operations=Count('id')
        ).order_by('-mois')

        data = []
        for sortie in sorties:
            operations = OperationSortir.objects.filter(
                date_de_sortie__month=sortie['mois'].month,
                date_de_sortie__year=sortie['mois'].year
            ).order_by('-date_de_sortie')
            
            data.append({
                'mois': sortie['mois'].strftime('%Y-%m'),
                'mois_format': format_date(sortie['mois'], format='MMMM yyyy', locale='fr_FR'),
                'total': sortie['total'],
                'nombre_operations': sortie['nombre_operations'],
                'operations': OperationSortirSerializer(operations, many=True).data
            })

        return Response({
            'sorties': data,
            'total_general': sum(sortie['total'] for sortie in sorties),
            'selected_year': selected_year
        })

class DetailsSoldeAPI(APIView):
    def get(self, request):
        selected_year = int(request.GET.get('year', timezone.now().year))
        
        # Calculer le solde initial
        solde_initial = (
            OperationEntrer.objects.filter(
                date_transaction__lt=f"{selected_year}-01-01"
            ).aggregate(Sum('montant'))['montant__sum'] or 0
        ) - (
            OperationSortir.objects.filter(
                date_de_sortie__lt=f"{selected_year}-01-01"
            ).aggregate(Sum('montant'))['montant__sum'] or 0
        )

        # Calculer les entrées et sorties mensuelles
        entrees = OperationEntrer.objects.filter(
            date_transaction__year=selected_year
        ).annotate(
            mois=TruncMonth('date_transaction')
        ).values('mois').annotate(
            total_entrees=Sum('montant')
        ).order_by('mois')

        sorties = OperationSortir.objects.filter(
            date_de_sortie__year=selected_year
        ).annotate(
            mois=TruncMonth('date_de_sortie')
        ).values('mois').annotate(
            total_sorties=Sum('montant')
        ).order_by('mois')

        # Créer des dictionnaires pour un accès facile
        entrees_dict = {e['mois'].strftime('%Y-%m'): e['total_entrees'] or 0 for e in entrees}
        sorties_dict = {s['mois'].strftime('%Y-%m'): s['total_sorties'] or 0 for s in sorties}
        
        # Obtenir tous les mois uniques
        tous_mois = sorted(set(list(entrees_dict.keys()) + list(sorties_dict.keys())))
        
        # Calculer les soldes mensuels
        soldes_mensuels = []
        solde_cumule = solde_initial
        total_entrees = 0
        total_sorties = 0
        
        for mois_str in tous_mois:
            mois_date = datetime.strptime(mois_str, '%Y-%m')
            entrees_mois = entrees_dict.get(mois_str, 0)
            sorties_mois = sorties_dict.get(mois_str, 0)
            solde_mois = entrees_mois - sorties_mois
            solde_cumule += solde_mois
            
            total_entrees += entrees_mois
            total_sorties += sorties_mois
            
            soldes_mensuels.append({
                'mois': mois_str,
                'mois_format': format_date(mois_date, format='MMMM yyyy', locale='fr_FR'),
                'entrees': entrees_mois,
                'sorties': sorties_mois,
                'solde_mois': solde_mois,
                'solde_cumule': solde_cumule
            })

        return Response({
            'soldes': list(reversed(soldes_mensuels)),
            'total_entrees': total_entrees,
            'total_sorties': total_sorties,
            'solde_final': solde_cumule,
            'selected_year': selected_year
        })

class DepensesAPI(APIView):
    def get(self, request):
        # Récupérer le mois sélectionné ou utiliser le mois courant
        mois_selectionne = request.GET.get('mois', timezone.now().strftime('%Y-%m'))
        
        try:
            date_debut = datetime.strptime(f"{mois_selectionne}-01", '%Y-%m-%d')
            date_fin = (date_debut + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        except ValueError:
            date_debut = timezone.now().replace(day=1)
            date_fin = (date_debut + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        operations = OperationSortir.objects.filter(
            date_de_sortie__gte=date_debut,
            date_de_sortie__lte=date_fin
        )

        # Dépenses par employé
        depenses_par_employe = operations.values(
            'beneficiaire__personnel__first_name', 
            'beneficiaire__personnel__last_name'
        ).annotate(
            total_depenses=Sum('montant'),
            nombre_depenses=Count('id'),
            categorie_plus_depensee=F('categorie__name')
        ).order_by('-total_depenses')

        # Dépenses par catégorie
        depenses_par_categorie = operations.values(
            'categorie__name'
        ).annotate(
            total_depenses=Sum('montant'),
            nombre_depenses=Count('id')
        ).order_by('-total_depenses')

        # Dépenses par année
        depenses_par_annee = OperationSortir.objects.annotate(
            year=TruncYear('date_de_sortie')
        ).values('year').annotate(
            total_depenses=Sum('montant')
        ).order_by('year')

        # Générer la liste des mois
        mois_liste = []
        date_courante = timezone.now()
        for i in range(12):
            date = date_courante - timedelta(days=30*i)
            mois_liste.append({
                'value': date.strftime('%Y-%m'),
                'label': format_date(date, format='MMMM yyyy', locale='fr_FR')
            })

        # Ajouter des couleurs pour le graphique
        colors = [
            '#3B82F6', '#EF4444', '#F59E0B', '#10B981', '#6366F1',
            '#EC4899', '#8B5CF6', '#14B8A6', '#F97316', '#06B6D4'
        ]
        
        categories_data = []
        for i, depense in enumerate(depenses_par_categorie):
            categories_data.append({
                **depense,
                'color': colors[i % len(colors)]
            })

        return Response({
            'depenses_par_employe': list(depenses_par_employe),
            'depenses_par_categorie': categories_data,
            'depenses_par_annee': list(depenses_par_annee),
            'mois_selectionne': mois_selectionne,
            'mois_liste': mois_liste
        })