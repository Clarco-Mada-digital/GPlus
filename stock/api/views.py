"""
Vues API pour le module de gestion de stock.

Ce module contient les ViewSets et les vues personnalisées pour l'API REST
du module de gestion de stock, permettant d'accéder et de manipuler
les données via des requêtes HTTP standardisées.
"""

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from datetime import timedelta

from ..models import (
    Produit, Categorie, Fournisseur, EntreeStock, SortieStock
)
from .serializers import (
    ProduitSerializer, ProduitDetailSerializer,
    CategorieSerializer, FournisseurSerializer,
    EntreeStockSerializer, SortieStockSerializer,
    AjustementStockSerializer
)

class ProduitViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les produits via l'API.
    """
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Utilise un sérialiseur détaillé pour la récupération d'un seul objet."""
        if self.action == 'retrieve':
            return ProduitDetailSerializer
        return self.serializer_class
    
    @action(detail=True, methods=['get'])
    def mouvements(self, request, pk=None):
        """Récupère les mouvements d'un produit spécifique."""
        produit = self.get_object()
        entrees = EntreeStock.objects.filter(produit=produit)
        sorties = SortieStock.objects.filter(produit=produit)
        
        # Sérialisation des entrées et sorties
        entrees_data = EntreeStockSerializer(entrees, many=True).data
        sorties_data = SortieStockSerializer(sorties, many=True).data
        
        return Response({
            'entrees': entrees_data,
            'sorties': sorties_data
        })
    
    @action(detail=False, methods=['get'])
    def stock_faible(self, request):
        """Récupère les produits dont le stock est inférieur au seuil d'alerte."""
        produits = self.queryset.filter(quantite_stock__lte=F('seuil_alerte'))
        serializer = self.get_serializer(produits, many=True)
        return Response(serializer.data)


class CategorieViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les catégories via l'API.
    """
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def produits(self, request, pk=None):
        """Récupère les produits d'une catégorie spécifique."""
        categorie = self.get_object()
        produits = Produit.objects.filter(categorie=categorie)
        page = self.paginate_queryset(produits)
        
        if page is not None:
            serializer = ProduitSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = ProduitSerializer(produits, many=True)
        return Response(serializer.data)


class FournisseurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les fournisseurs via l'API.
    """
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def produits(self, request, pk=None):
        """Récupère les produits d'un fournisseur spécifique."""
        fournisseur = self.get_object()
        produits = Produit.objects.filter(fournisseur=fournisseur)
        page = self.paginate_queryset(produits)
        
        if page is not None:
            serializer = ProduitSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = ProduitSerializer(produits, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historique_achats(self, request, pk=None):
        """Récupère l'historique des achats d'un fournisseur."""
        fournisseur = self.get_object()
        entrees = EntreeStock.objects.filter(fournisseur=fournisseur)
        
        # Agrégation des données
        total_achats = entrees.aggregate(
            total=Sum(F('quantite') * F('prix_unitaire_ht'))
        )['total'] or 0
        
        # Dernières entrées
        dernieres_entrees = EntreeStockSerializer(
            entrees.order_by('-date')[:5], 
            many=True
        ).data
        
        return Response({
            'fournisseur': FournisseurSerializer(fournisseur).data,
            'total_achats': total_achats,
            'nombre_entrees': entrees.count(),
            'dernieres_entrees': dernieres_entrees
        })


class EntreeStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les entrées de stock via l'API.
    """
    queryset = EntreeStock.objects.all()
    serializer_class = EntreeStockSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Met à jour le stock lors de la création d'une entrée."""
        instance = serializer.save()
        # Mise à jour du stock du produit
        produit = instance.produit
        produit.quantite_stock += instance.quantite
        produit.save()
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annule une entrée de stock et met à jour le stock du produit."""
        entree = self.get_object()
        
        # Vérifier si l'entrée n'a pas déjà été annulée
        if entree.annulee:
            return Response(
                {'erreur': 'Cette entrée a déjà été annulée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier si le stock est suffisant pour annuler
        if entree.produit.quantite_stock < entree.quantite:
            return Response(
                {
                    'erreur': 'Stock insuffisant pour annuler cette entrée. '
                             'Stock actuel: {}, Quantité à annuler: {}'.format(
                                 entree.produit.quantite_stock, entree.quantite)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour le stock
        produit = entree.produit
        produit.quantite_stock -= entree.quantite
        produit.save()
        
        # Marquer l'entrée comme annulée
        entree.annulee = True
        entree.save()
        
        return Response({'message': 'Entrée annulée avec succès.'})


class SortieStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les sorties de stock via l'API.
    """
    queryset = SortieStock.objects.all()
    serializer_class = SortieStockSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Vérifie le stock et effectue la sortie."""
        instance = serializer.save()
        produit = instance.produit
        
        # Vérifier le stock disponible
        if produit.quantite_stock < instance.quantite:
            raise serializers.ValidationError(
                f'Stock insuffisant. Stock disponible: {produit.quantite_stock}'
            )
        
        # Mettre à jour le stock
        produit.quantite_stock -= instance.quantite
        produit.save()


class MouvementStockViewSet(viewsets.GenericViewSet):
    """
    ViewSet pour les opérations sur les mouvements de stock.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def ajustement(self, request):
        """
        Ajuste le stock d'un produit manuellement.
        Crée une entrée ou une sortie selon le besoin.
        """
        serializer = AjustementStockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        produit = serializer.validated_data['produit']
        quantite = serializer.validated_data['quantite']
        motif = serializer.validated_data['motif']
        
        if quantite > 0:
            # Créer une entrée de stock
            entree = EntreeStock.objects.create(
                produit=produit,
                quantite=quantite,
                prix_unitaire_ht=produit.prix_achat_ht or 0,
                motif=f"Ajustement: {motif}",
                utilisateur=request.user
            )
            return Response(
                EntreeStockSerializer(entree).data,
                status=status.HTTP_201_CREATED
            )
        else:
            # Créer une sortie de stock
            if produit.quantite_stock < abs(quantite):
                return Response(
                    {'erreur': 'Stock insuffisant pour cet ajustement'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            sortie = SortieStock.objects.create(
                produit=produit,
                quantite=abs(quantite),
                motif=f"Ajustement: {motif}",
                utilisateur=request.user
            )
            return Response(
                SortieStockSerializer(sortie).data,
                status=status.HTTP_201_CREATED
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Récupère les statistiques des mouvements de stock.
        """
        # Périodes pour les statistiques
        aujourdhui = timezone.now().date()
        debut_mois = aujourdhui.replace(day=1)
        debut_annee = aujourdhui.replace(month=1, day=1)
        
        # Agrégations pour les entrées
        entrees_mois = EntreeStock.objects.filter(
            date__gte=debut_mois
        ).aggregate(
            total_quantite=Sum('quantite'),
            total_montant=Sum(F('quantite') * F('prix_unitaire_ht'))
        )
        
        entrees_annee = EntreeStock.objects.filter(
            date__gte=debut_annee
        ).aggregate(
            total_quantite=Sum('quantite'),
            total_montant=Sum(F('quantite') * F('prix_unitaire_ht'))
        )
        
        # Agrégations pour les sorties
        sorties_mois = SortieStock.objects.filter(
            date__gte=debut_mois
        ).aggregate(
            total_quantite=Sum('quantite'),
        )
        
        sorties_annee = SortieStock.objects.filter(
            date__gte=debut_annee
        ).aggregate(
            total_quantite=Sum('quantite'),
        )
        
        # Produits en stock faible
        produits_faible_stock = Produit.objects.filter(
            quantite_stock__lte=F('seuil_alerte')
        ).count()
        
        return Response({
            'periode': {
                'mois': debut_mois.strftime('%B %Y'),
                'annee': debut_annee.year
            },
            'entrees': {
                'ce_mois': {
                    'quantite': entrees_mois['total_quantite'] or 0,
                    'montant': float(entrees_mois['total_montant'] or 0)
                },
                'cette_annee': {
                    'quantite': entrees_annee['total_quantite'] or 0,
                    'montant': float(entrees_annee['total_montant'] or 0)
                }
            },
            'sorties': {
                'ce_mois': {
                    'quantite': sorties_mois['total_quantite'] or 0
                },
                'cette_annee': {
                    'quantite': sorties_annee['total_quantite'] or 0
                }
            },
            'alertes': {
                'produits_faible_stock': produits_faible_stock
            }
        })
