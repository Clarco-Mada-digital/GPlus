from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, F, Sum, Count, Case, When, IntegerField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

from ..models import Produit, Categorie, Fournisseur, EntreeStock, SortieStock
from ..serializers import (
    ProduitSerializer, CategorieSerializer, FournisseurSerializer,
    EntreeStockSerializer, SortieStockSerializer, ProduitDetailSerializer,
    MouvementStockSerializer
)


class ProduitViewSet(viewsets.ModelViewSet):
    """API pour gérer les produits"""
    queryset = Produit.objects.select_related('categorie', 'fournisseur').all()
    serializer_class = ProduitSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProduitDetailSerializer
        return self.serializer_class
    
    def get_queryset(self):
        queryset = self.queryset
        
        # Filtrage
        search = self.request.query_params.get('search', None)
        categorie = self.request.query_params.get('categorie', None)
        fournisseur = self.request.query_params.get('fournisseur', None)
        statut = self.request.query_params.get('statut', None)
        
        if search:
            queryset = queryset.filter(
                Q(designation__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
            
        if categorie:
            queryset = queryset.filter(categorie_id=categorie)
            
        if fournisseur:
            queryset = queryset.filter(fournisseur_id=fournisseur)
            
        if statut == 'alerte':
            queryset = queryset.filter(quantite_stock__lte=F('seuil_alerte'))
        elif statut == 'epuise':
            queryset = queryset.filter(quantite_stock=0)
        elif statut == 'disponible':
            queryset = queryset.filter(quantite_stock__gt=0)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def mouvements(self, request, pk=None):
        """Récupérer les mouvements d'un produit"""
        produit = self.get_object()
        
        # Récupérer les paramètres de filtre
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        type_mouvement = request.query_params.get('type')
        
        # Construire les filtres
        filtres_entrees = Q(produit=produit, annulee=False)
        filtres_sorties = Q(produit=produit)
        
        if date_debut:
            filtres_entrees &= Q(date__date__gte=date_debut)
            filtres_sorties &= Q(date__date__gte=date_debut)
            
        if date_fin:
            filtres_entrees &= Q(date__date__lte=date_fin)
            filtres_sorties &= Q(date__date__lte=date_fin)
        
        # Récupérer les mouvements
        entrees = EntreeStock.objects.filter(filtres_entrees).order_by('-date')
        sorties = SortieStock.objects.filter(filtres_sorties).order_by('-date')
        
        # Sérialiser les données
        entree_serializer = EntreeStockSerializer(entrees, many=True)
        sortie_serializer = SortieStockSerializer(sorties, many=True)
        
        # Calculer les totaux
        total_entrees = entrees.aggregate(
            quantite=Coalesce(Sum('quantite'), 0),
            montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0)
        )
        
        total_sorties = sorties.aggregate(
            quantite=Coalesce(Sum('quantite'), 0),
            montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0)
        )
        
        return Response({
            'entrees': entree_serializer.data,
            'sorties': sortie_serializer.data,
            'totaux': {
                'entrees': total_entrees,
                'sorties': total_sorties,
                'solde': {
                    'quantite': total_entrees['quantite'] - total_sorties['quantite'],
                    'montant': total_entrees['montant'] - total_sorties['montant']
                }
            }
        })
    
    @action(detail=False, methods=['get'])
    def etat_stock(self, request):
        """Rapport d'état des stocks"""
        # Récupérer les paramètres de filtre
        categorie_id = request.query_params.get('categorie')
        fournisseur_id = request.query_params.get('fournisseur')
        
        # Construire la requête
        produits = Produit.objects.select_related('categorie', 'fournisseur')
        
        if categorie_id:
            produits = produits.filter(categorie_id=categorie_id)
            
        if fournisseur_id:
            produits = produits.filter(fournisseur_id=fournisseur_id)
        
        # Calculer les totaux
        total_produits = produits.count()
        total_quantite = produits.aggregate(total=Coalesce(Sum('quantite_stock'), 0))['total']
        total_valeur_achat = produits.aggregate(
            total=Coalesce(Sum(F('quantite_stock') * F('prix_achat')), 0)
        )['total']
        total_valeur_vente = produits.aggregate(
            total=Coalesce(Sum(F('quantite_stock') * F('prix_vente')), 0)
        )['total']
        
        # Produits en alerte
        produits_alerte = produits.filter(
            quantite_stock__lte=F('seuil_alerte'),
            quantite_stock__gt=0
        ).count()
        
        produits_epuises = produits.filter(quantite_stock=0).count()
        
        # Sérialiser les produits
        serializer = self.get_serializer(produits, many=True)
        
        return Response({
            'total_produits': total_produits,
            'total_quantite': total_quantite,
            'total_valeur_achat': total_valeur_achat,
            'total_valeur_vente': total_valeur_vente,
            'produits_alerte': produits_alerte,
            'produits_epuises': produits_epuises,
            'produits': serializer.data
        })


class CategorieViewSet(viewsets.ModelViewSet):
    """API pour gérer les catégories"""
    queryset = Categorie.objects.annotate(
        nb_produits=Count('produit')
    ).order_by('nom')
    serializer_class = CategorieSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = self.queryset
        
        # Filtrage
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def produits(self, request, pk=None):
        """Récupérer les produits d'une catégorie"""
        categorie = self.get_object()
        produits = categorie.produit_set.select_related('fournisseur').all()
        
        # Appliquer les filtres
        search = request.query_params.get('search', None)
        fournisseur = request.query_params.get('fournisseur', None)
        
        if search:
            produits = produits.filter(
                Q(designation__icontains=search) |
                Q(code__icontains=search)
            )
            
        if fournisseur:
            produits = produits.filter(fournisseur_id=fournisseur)
        
        # Pagination
        page = self.paginate_queryset(produits)
        if page is not None:
            serializer = ProduitSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProduitSerializer(produits, many=True)
        return Response(serializer.data)


class FournisseurViewSet(viewsets.ModelViewSet):
    """API pour gérer les fournisseurs"""
    queryset = Fournisseur.objects.annotate(
        nb_produits=Count('produit', distinct=True),
        nb_entrees=Count('entreestock', distinct=True)  # Changé de 'entrees' à 'entreestock'
    ).order_by('nom')
    serializer_class = FournisseurSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = self.queryset
        
        # Filtrage
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(email__icontains=search) |
                Q(contact__icontains=search) |
                Q(telephone__icontains=search)
            )
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def produits(self, request, pk=None):
        """Récupérer les produits d'un fournisseur"""
        fournisseur = self.get_object()
        produits = fournisseur.produit_set.select_related('categorie').all()
        
        # Appliquer les filtres
        search = request.query_params.get('search', None)
        categorie = request.query_params.get('categorie', None)
        
        if search:
            produits = produits.filter(
                Q(designation__icontains=search) |
                Q(code__icontains=search)
            )
            
        if categorie:
            produits = produits.filter(categorie_id=categorie)
        
        # Pagination
        page = self.paginate_queryset(produits)
        if page is not None:
            serializer = ProduitSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProduitSerializer(produits, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def entrees(self, request, pk=None):
        """Récupérer les entrées d'un fournisseur"""
        fournisseur = self.get_object()
        entrees = fournisseur.entrees.select_related('produit', 'utilisateur')
        
        # Appliquer les filtres
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        produit = request.query_params.get('produit')
        
        if date_debut:
            entrees = entrees.filter(date__date__gte=date_debut)
            
        if date_fin:
            entrees = entrees.filter(date__date__lte=date_fin)
            
        if produit:
            entrees = entrees.filter(produit_id=produit)
        
        # Pagination
        page = self.paginate_queryset(entrees)
        if page is not None:
            serializer = EntreeStockSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = EntreeStockSerializer(entrees, many=True)
        return Response(serializer.data)


class EntreeStockViewSet(viewsets.ModelViewSet):
    """API pour gérer les entrées en stock"""
    queryset = EntreeStock.objects.select_related(
        'produit', 'fournisseur', 'utilisateur'
    ).order_by('-date')
    serializer_class = EntreeStockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Définir automatiquement l'utilisateur qui effectue l'entrée
        serializer.save(utilisateur=self.request.user)
    
    def get_queryset(self):
        queryset = self.queryset
        
        # Filtrage
        produit = self.request.query_params.get('produit')
        fournisseur = self.request.query_params.get('fournisseur')
        utilisateur = self.request.query_params.get('utilisateur')
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        annulee = self.request.query_params.get('annulee')
        
        if produit:
            queryset = queryset.filter(produit_id=produit)
            
        if fournisseur:
            queryset = queryset.filter(fournisseur_id=fournisseur)
            
        if utilisateur:
            queryset = queryset.filter(utilisateur_id=utilisateur)
            
        if date_debut:
            queryset = queryset.filter(date__date__gte=date_debut)
            
        if date_fin:
            queryset = queryset.filter(date__date__lte=date_fin)
            
        if annulee is not None:
            queryset = queryset.filter(annulee=(annulee.lower() == 'true'))
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annuler une entrée en stock"""
        entree = self.get_object()
        
        if entree.annulee:
            return Response(
                {"detail": "Cette entrée a déjà été annulée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier si le stock est suffisant pour annuler l'entrée
        if entree.produit.quantite_stock < entree.quantite:
            return Response(
                {
                    "detail": "Stock insuffisant pour annuler cette entrée. "
                             f"Stock actuel: {entree.produit.quantite_stock}, "
                             f"Quantité à annuler: {entree.quantite}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour le stock
        entree.produit.quantite_stock -= entree.quantite
        entree.produit.save()
        
        # Marquer l'entrée comme annulée
        entree.annulee = True
        entree.motif_annulation = request.data.get('motif_annulation', 'Annulée via l\'API')
        entree.utilisateur_annulation = request.user
        entree.date_annulation = timezone.now()
        entree.save()
        
        serializer = self.get_serializer(entree)
        return Response(serializer.data)


class SortieStockViewSet(viewsets.ModelViewSet):
    """API pour gérer les sorties de stock"""
    queryset = SortieStock.objects.select_related(
        'produit', 'utilisateur'
    ).order_by('-date')
    serializer_class = SortieStockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Définir automatiquement l'utilisateur qui effectue la sortie
        serializer.save(utilisateur=self.request.user)
    
    def get_queryset(self):
        queryset = self.queryset
        
        # Filtrage
        produit = self.request.query_params.get('produit')
        client = self.request.query_params.get('client')
        utilisateur = self.request.query_params.get('utilisateur')
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        
        if produit:
            queryset = queryset.filter(produit_id=produit)
            
        if client:
            queryset = queryset.filter(client__icontains=client)
            
        if utilisateur:
            queryset = queryset.filter(utilisateur_id=utilisateur)
            
        if date_debut:
            queryset = queryset.filter(date__date__gte=date_debut)
            
        if date_fin:
            queryset = queryset.filter(date__date__lte=date_fin)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Surcharge pour vérifier le stock avant de créer une sortie"""
        produit_id = request.data.get('produit')
        quantite = float(request.data.get('quantite', 0))
        
        if not produit_id or quantite <= 0:
            return Response(
                {"detail": "Produit et quantité valides requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            produit = Produit.objects.get(id=produit_id)
        except Produit.DoesNotExist:
            return Response(
                {"detail": "Produit non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier le stock disponible
        if produit.quantite_stock < quantite:
            return Response(
                {
                    "detail": f"Stock insuffisant. Stock disponible: {produit.quantite_stock}",
                    "stock_disponible": produit.quantite_stock,
                    "quantite_demandee": quantite
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer la sortie
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Mettre à jour le stock
        produit.quantite_stock -= quantite
        produit.save()
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def destroy(self, request, *args, **kwargs):
        """Surcharge pour restaurer le stock lors de la suppression d'une sortie"""
        sortie = self.get_object()
        
        # Restaurer le stock
        sortie.produit.quantite_stock += sortie.quantite
        sortie.produit.save()
        
        return super().destroy(request, *args, **kwargs)


class MouvementStockViewSet(viewsets.ViewSet):
    """API pour les opérations sur les mouvements de stock"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def ajustement(self, request):
        """Ajuster le stock d'un produit"""
        serializer = MouvementStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        produit_id = serializer.validated_data['produit_id']
        quantite = serializer.validated_data['quantite']
        motif = serializer.validated_data.get('motif', 'Ajustement de stock')
        
        try:
            produit = Produit.objects.get(id=produit_id)
        except Produit.DoesNotExist:
            return Response(
                {"detail": "Produit non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculer la différence
        difference = quantite - produit.quantite_stock
        
        # Créer un mouvement d'entrée ou de sortie selon le cas
        if difference > 0:
            # Entrée en stock
            entree = EntreeStock.objects.create(
                produit=produit,
                quantite=difference,
                prix_unitaire=produit.prix_achat,
                reference=f"AJUST-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                notes=f"Ajustement de stock: {motif}",
                utilisateur=request.user
            )
            
            # Mettre à jour le stock
            produit.quantite_stock = quantite
            produit.save()
            
            return Response({
                "detail": "Stock ajusté avec succès.",
                "type": "entree",
                "mouvement_id": entree.id,
                "nouveau_stock": produit.quantite_stock
            })
            
        elif difference < 0:
            # Vérifier si le stock est suffisant pour la sortie
            if produit.quantite_stock < abs(difference):
                return Response(
                    {
                        "detail": f"Stock insuffisant pour effectuer la sortie. "
                                 f"Stock actuel: {produit.quantite_stock}, "
                                 f"Quantité à sortir: {abs(difference)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Sortie de stock
            sortie = SortieStock.objects.create(
                produit=produit,
                quantite=abs(difference),
                prix_unitaire=produit.prix_vente,
                reference=f"AJUST-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                notes=f"Ajustement de stock: {motif}",
                utilisateur=request.user,
                client="Ajustement de stock"
            )
            
            # Mettre à jour le stock
            produit.quantite_stock = quantite
            produit.save()
            
            return Response({
                "detail": "Stock ajusté avec succès.",
                "type": "sortie",
                "mouvement_id": sortie.id,
                "nouveau_stock": produit.quantite_stock
            })
        
        # Si pas de différence, ne rien faire
        return Response({
            "detail": "Aucun ajustement nécessaire. La quantité est identique au stock actuel.",
            "stock_actuel": produit.quantite_stock
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques sur les mouvements de stock"""
        # Période par défaut : 30 derniers jours
        date_fin = timezone.now()
        date_debut = date_fin - timedelta(days=30)
        
        # Récupérer les paramètres de filtre
        date_debut_param = request.query_params.get('date_debut')
        date_fin_param = request.query_params.get('date_fin')
        
        if date_debut_param:
            try:
                date_debut = timezone.datetime.strptime(date_debut_param, '%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        
        if date_fin_param:
            try:
                date_fin = timezone.datetime.strptime(date_fin_param + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                pass
        
        # Statistiques des entrées
        entrees = EntreeStock.objects.filter(
            date__range=[date_debut, date_fin],
            annulee=False
        ).aggregate(
            total_quantite=Coalesce(Sum('quantite'), 0),
            total_montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0),
            nb_mouvements=Count('id')
        )
        
        # Statistiques des sorties
        sorties = SortieStock.objects.filter(
            date__range=[date_debut, date_fin]
        ).aggregate(
            total_quantite=Coalesce(Sum('quantite'), 0),
            total_montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0),
            nb_mouvements=Count('id')
        )
        
        # Produits les plus vendus
        produits_vendus = SortieStock.objects.filter(
            date__range=[date_debut, date_fin]
        ).values(
            'produit__id', 'produit__designation', 'produit__code'
        ).annotate(
            quantite=Coalesce(Sum('quantite'), 0),
            montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0)
        ).order_by('-quantite')[:5]
        
        # Fournisseurs les plus utilisés
        fournisseurs = EntreeStock.objects.filter(
            date__range=[date_debut, date_fin],
            annulee=False,
            fournisseur__isnull=False
        ).values(
            'fournisseur__id', 'fournisseur__nom'
        ).annotate(
            nb_entrees=Count('id'),
            quantite=Coalesce(Sum('quantite'), 0),
            montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0)
        ).order_by('-montant')[:5]
        
        # Évolution des mouvements par jour
        mouvements_par_jour = []
        current_date = date_debut.date()
        
        while current_date <= date_fin.date():
            # Entrées du jour
            entrees_jour = EntreeStock.objects.filter(
                date__date=current_date,
                annulee=False
            ).aggregate(
                quantite=Coalesce(Sum('quantite'), 0),
                montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0)
            )
            
            # Sorties du jour
            sorties_jour = SortieStock.objects.filter(
                date__date=current_date
            ).aggregate(
                quantite=Coalesce(Sum('quantite'), 0),
                montant=Coalesce(Sum(F('quantite') * F('prix_unitaire')), 0)
            )
            
            mouvements_par_jour.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'entrees': {
                    'quantite': float(entrees_jour['quantite']),
                    'montant': float(entrees_jour['montant'])
                },
                'sorties': {
                    'quantite': float(sorties_jour['quantite']),
                    'montant': float(sorties_jour['montant'])
                }
            })
            
            current_date += timedelta(days=1)
        
        return Response({
            'periode': {
                'debut': date_debut.date().isoformat(),
                'fin': date_fin.date().isoformat()
            },
            'entrees': {
                'quantite': float(entrees['total_quantite']),
                'montant': float(entrees['total_montant']),
                'nb_mouvements': entrees['nb_mouvements']
            },
            'sorties': {
                'quantite': float(sorties['total_quantite']),
                'montant': float(sorties['total_montant']),
                'nb_mouvements': sorties['nb_mouvements']
            },
            'produits_vendus': [
                {
                    'id': p['produit__id'],
                    'designation': p['produit__designation'],
                    'code': p['produit__code'],
                    'quantite': float(p['quantite']),
                    'montant': float(p['montant'])
                }
                for p in produits_vendus
            ],
            'fournisseurs': [
                {
                    'id': f['fournisseur__id'],
                    'nom': f['fournisseur__nom'],
                    'nb_entrees': f['nb_entrees'],
                    'quantite': float(f['quantite']),
                    'montant': float(f['montant'])
                }
                for f in fournisseurs
            ],
            'evolution': mouvements_par_jour
        })
