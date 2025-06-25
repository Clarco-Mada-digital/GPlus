from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Q, F, Sum, Count, Case, When, Value, IntegerField
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

from ..models import EntreeStock, SortieStock, Produit


class HistoriqueMouvementsView(LoginRequiredMixin, ListView):
    """Vue pour afficher l'historique des mouvements de stock"""
    template_name = 'stock/historique/mouvements.html'
    context_object_name = 'mouvements'
    paginate_by = 50
    
    def get_queryset(self):
        # Récupérer les entrées et sorties
        entrees = EntreeStock.objects.select_related('produit', 'fournisseur', 'utilisateur').filter(
            annulee=False
        ).annotate(
            type_mouvement=Value('entree', output_field=models.CharField()),
            reference_mouvement=F('reference'),
            quantite_mouvement=F('quantite'),
            prix_unitaire_mouvement=F('prix_unitaire'),
            montant_total_mouvement=F('montant_total'),
            tiers=F('fournisseur__nom'),
        )
        
        sorties = SortieStock.objects.select_related('produit', 'utilisateur').annotate(
            type_mouvement=Value('sortie', output_field=models.CharField()),
            reference_mouvement=F('reference'),
            quantite_mouvement=F('quantite'),
            prix_unitaire_mouvement=F('prix_unitaire'),
            montant_total_mouvement=F('montant_total'),
            tiers=F('client'),
            fournisseur_id=None,
            fournisseur=None
        )
        
        # Combiner les deux querysets
        mouvements = entrees.union(sorties, all=True).order_by('-date')
        
        # Appliquer les filtres
        # Filtre par type de mouvement
        type_mouvement = self.request.GET.get('type')
        if type_mouvement == 'entree':
            mouvements = entrees.order_by('-date')
        elif type_mouvement == 'sortie':
            mouvements = sorties.order_by('-date')
        
        # Filtre par produit
        produit_id = self.request.GET.get('produit')
        if produit_id:
            mouvements = mouvements.filter(produit_id=produit_id)
        
        # Filtre par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if date_debut:
            mouvements = mouvements.filter(date__date__gte=date_debut)
        if date_fin:
            mouvements = mouvements.filter(date__date__lte=date_fin)
        
        return mouvements
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les filtres
        type_mouvement = self.request.GET.get('type', '')
        produit_id = self.request.GET.get('produit')
        date_debut = self.request.GET.get('date_debut', '')
        date_fin = self.request.GET.get('date_fin', '')
        
        # Ajouter les filtres au contexte
        context['type_mouvement'] = type_mouvement
        context['produit'] = Produit.objects.filter(id=produit_id).first() if produit_id else None
        context['date_debut'] = date_debut
        context['date_fin'] = date_fin
        
        # Calculer les totaux
        mouvements = self.get_queryset()
        
        total_entrees = mouvements.filter(type_mouvement='entree').aggregate(
            total=Sum('montant_total_mouvement')
        )['total'] or 0
        
        total_sorties = mouvements.filter(type_mouvement='sortie').aggregate(
            total=Sum('montant_total_mouvement')
        )['total'] or 0
        
        context['total_entrees'] = total_entrees
        context['total_sorties'] = total_sorties
        context['solde'] = total_entrees - total_sorties
        
        # Produits disponibles pour le filtre
        context['produits'] = Produit.objects.all().order_by('designation')
        
        return context


class HistoriqueProduitView(LoginRequiredMixin, TemplateView):
    """Vue pour afficher l'historique détaillé d'un produit"""
    template_name = 'stock/historique/historique_produit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produit_id = self.kwargs.get('pk')
        
        # Récupérer le produit
        produit = get_object_or_404(Produit, id=produit_id)
        context['produit'] = produit
        
        # Récupérer les mouvements du produit
        date_limite = timezone.now() - timedelta(days=90)  # 3 mois d'historique
        
        # Dernières entrées
        entrees = EntreeStock.objects.filter(
            produit=produit,
            date__gte=date_limite,
            annulee=False
        ).select_related('fournisseur', 'utilisateur').order_by('-date')[:10]
        
        # Dernières sorties
        sorties = SortieStock.objects.filter(
            produit=produit,
            date__gte=date_limite
        ).select_related('utilisateur').order_by('-date')[:10]
        
        # Statistiques des mouvements par mois
        mouvements_mensuels = EntreeStock.objects.filter(
            produit=produit,
            date__gte=date_limite,
            annulee=False
        ).annotate(
            mois=TruncMonth('date')
        ).values('mois').annotate(
            entrees=Sum('quantite'),
            cout_total=Sum(F('quantite') * F('prix_unitaire'))
        ).order_by('mois')
        
        # Préparer les données pour le graphique
        mois = []
        quantites_entrees = []
        quantites_sorties = []
        
        for mouvement in mouvements_mensuels:
            mois.append(mouvement['mois'].strftime('%b %Y'))
            quantites_entrees.append(float(mouvement['entrees'] or 0))
            
            # Récupérer les sorties pour le même mois
            sorties_mois = SortieStock.objects.filter(
                produit=produit,
                date__year=mouvement['mois'].year,
                date__month=mouvement['mois'].month
            ).aggregate(total=Sum('quantite'))['total'] or 0
            
            quantites_sorties.append(float(sorties_mois))
        
        context['entrees'] = entrees
        context['sorties'] = sorties
        context['mois'] = mois
        context['quantites_entrees'] = quantites_entrees
        context['quantites_sorties'] = quantites_sorties
        
        # Calculer la consommation moyenne mensuelle
        if quantites_sorties:
            moyenne_sorties = sum(quantites_sorties) / len(quantites_sorties)
            context['moyenne_sorties'] = round(moyenne_sorties, 2)
            
            # Estimer la durée de stock restante (en mois)
            if moyenne_sorties > 0:
                duree_restante = produit.quantite_stock / moyenne_sorties
                context['duree_stock_restant'] = round(duree_restante, 1)
        
        return context
