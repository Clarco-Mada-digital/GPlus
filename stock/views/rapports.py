from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, F, Q, Value, DecimalField, Case, When, IntegerField
from django.db.models.functions import TruncMonth, TruncDay, TruncYear, Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from datetime import timedelta

from ..models import Produit, EntreeStock, SortieStock, Categorie, Fournisseur


class EtatStockView(LoginRequiredMixin, ListView):
    """Rapport d'état des stocks"""
    template_name = 'stock/rapports/etat_stock.html'
    context_object_name = 'produits'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Produit.objects.select_related('categorie', 'fournisseur')
        
        # Filtre par catégorie
        categorie_id = self.request.GET.get('categorie')
        if categorie_id:
            queryset = queryset.filter(categorie_id=categorie_id)
        
        # Filtre par statut de stock
        statut = self.request.GET.get('statut')
        if statut == 'alerte':
            queryset = queryset.filter(quantite_stock__lte=F('seuil_alerte'))
        elif statut == 'epuise':
            queryset = queryset.filter(quantite_stock=0)
        
        # Filtre par fournisseur
        fournisseur_id = self.request.GET.get('fournisseur')
        if fournisseur_id:
            queryset = queryset.filter(fournisseur_id=fournisseur_id)
        
        # Tri
        order_by = self.request.GET.get('order_by', 'designation')
        if order_by in ['designation', 'code', 'quantite_stock', 'prix_vente', 'prix_achat']:
            direction = self.request.GET.get('direction', 'asc')
            if direction == 'desc':
                order_by = f'-{order_by}'
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les filtres
        categorie_id = self.request.GET.get('categorie')
        fournisseur_id = self.request.GET.get('fournisseur')
        statut = self.request.GET.get('statut', '')
        order_by = self.request.GET.get('order_by', 'designation')
        direction = self.request.GET.get('direction', 'asc')
        
        # Calculer les totaux
        produits = self.get_queryset()
        
        total_quantite = sum(p.quantite_stock for p in produits)
        total_valeur_achat = sum(p.quantite_stock * p.prix_achat for p in produits)
        total_valeur_vente = sum(p.quantite_stock * p.prix_vente for p in produits)
        
        # Préparer les données pour les graphiques
        categories = Categorie.objects.annotate(
            nb_produits=Count('produit'),
            valeur_stock=Sum(F('produit__quantite_stock') * F('produit__prix_vente'))
        ).filter(nb_produits__gt=0).order_by('-valeur_stock')
        
        noms_categories = [c.nom for c in categories]
        valeurs_stock = [float(c.valeur_stock or 0) for c in categories]
        
        # Produits en alerte
        produits_alerte = Produit.objects.filter(
            quantite_stock__lte=F('seuil_alerte'),
            quantite_stock__gt=0
        ).count()
        
        produits_epuises = Produit.objects.filter(
            quantite_stock=0
        ).count()
        
        produits_disponibles = Produit.objects.filter(
            quantite_stock__gt=F('seuil_alerte')
        ).count()
        
        # Ajouter les données au contexte
        context.update({
            'categories': Categorie.objects.all(),
            'fournisseurs': Fournisseur.objects.all(),
            'categorie_selected': int(categorie_id) if categorie_id else None,
            'fournisseur_selected': int(fournisseur_id) if fournisseur_id else None,
            'statut': statut,
            'order_by': order_by,
            'direction': direction,
            'total_quantite': total_quantite,
            'total_valeur_achat': total_valeur_achat,
            'total_valeur_vente': total_valeur_vente,
            'noms_categories': noms_categories,
            'valeurs_stock': valeurs_stock,
            'produits_alerte': produits_alerte,
            'produits_epuises': produits_epuises,
            'produits_disponibles': produits_disponibles,
        })
        
        return context


class RapportMouvementsView(LoginRequiredMixin, TemplateView):
    """Rapport des mouvements de stock"""
    template_name = 'stock/rapports/mouvements.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les paramètres de filtre
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        type_mouvement = self.request.GET.get('type')
        produit_id = self.request.GET.get('produit')
        
        # Définir les dates par défaut (30 derniers jours)
        if not date_debut or not date_fin:
            date_fin = timezone.now().date()
            date_debut = date_fin - timedelta(days=30)
            date_debut = date_debut.strftime('%Y-%m-%d')
            date_fin = date_fin.strftime('%Y-%m-%d')
        
        # Construire les filtres de base
        filtres_entrees = Q(annulee=False)
        filtres_sorties = Q()
        
        if date_debut:
            filtres_entrees &= Q(date__date__gte=date_debut)
            filtres_sorties &= Q(date__date__gte=date_debut)
        
        if date_fin:
            filtres_entrees &= Q(date__date__lte=date_fin)
            filtres_sorties &= Q(date__date__lte=date_fin)
        
        if produit_id:
            filtres_entrees &= Q(produit_id=produit_id)
            filtres_sorties &= Q(produit_id=produit_id)
        
        # Récupérer les mouvements
        entrees = EntreeStock.objects.filter(filtres_entrees)
        sorties = SortieStock.objects.filter(filtres_sorties)
        
        # Préparer les données pour le graphique des mouvements par jour
        mouvements_par_jour = []
        
        if date_debut and date_fin:
            # Générer une plage de dates
            from datetime import datetime
            
            start_date = datetime.strptime(date_debut, '%Y-%m-%d').date()
            end_date = datetime.strptime(date_fin, '%Y-%m-%d').date()
            
            current_date = start_date
            
            while current_date <= end_date:
                # Compter les entrées et sorties pour ce jour
                nb_entrees = entrees.filter(date__date=current_date).count()
                nb_sorties = sorties.filter(date__date=current_date).count()
                
                if nb_entrees > 0 or nb_sorties > 0:
                    mouvements_par_jour.append({
                        'date': current_date.strftime('%d/%m'),
                        'entrees': nb_entrees,
                        'sorties': nb_sorties
                    })
                
                current_date += timedelta(days=1)
        
        # Calculer les totaux
        total_entrees_agg = entrees.aggregate(
            total_quantite=Sum('quantite'),
            total_montant=Sum(F('quantite') * F('prix_unitaire'))
        )
        total_entrees = total_entrees_agg['total_montant'] or 0
        
        total_sorties_agg = sorties.aggregate(
            total_quantite=Sum('quantite'),
            total_montant=Sum(F('quantite') * F('prix_unitaire'))
        )
        total_sorties = total_sorties_agg['total_montant'] or 0
        
        # Calculer le solde total
        total_general = total_entrees - total_sorties
        
        # Produits les plus vendus
        produits_vendus = sorties.values(
            'produit__designation', 'produit__code'
        ).annotate(
            quantite_vendue=Sum('quantite'),
            montant_total=Sum(F('quantite') * F('prix_unitaire'))
        ).order_by('-quantite_vendue')[:10]
        
        # Fournisseurs les plus utilisés
        fournisseurs = entrees.values(
            'fournisseur__nom', 'fournisseur_id'
        ).annotate(
            nb_entrees=Count('id'),
            quantite_totale=Sum('quantite'),
            montant_total=Sum(F('quantite') * F('prix_unitaire'))
        ).filter(fournisseur__isnull=False).order_by('-montant_total')[:10]
        
        # Préparer la liste des mouvements combinés
        mouvements = []
        
        # Ajouter les entrées
        for entree in entrees.select_related('produit', 'utilisateur', 'fournisseur'):
            mouvements.append({
                'date': entree.date,
                'type': 'Entrée',
                'produit': entree.produit,
                'quantite': entree.quantite,
                'prix_unitaire': entree.prix_unitaire,
                'montant_total': entree.quantite * entree.prix_unitaire,
                'reference': entree.reference,
                'utilisateur': entree.utilisateur,
                'objet': entree
            })
        
        # Ajouter les sorties
        for sortie in sorties.select_related('produit', 'utilisateur'):
            mouvements.append({
                'date': sortie.date,
                'type': 'Sortie',
                'produit': sortie.produit,
                'quantite': sortie.quantite,
                'prix_unitaire': sortie.prix_unitaire,
                'montant_total': sortie.quantite * sortie.prix_unitaire,
                'reference': sortie.reference,
                'utilisateur': sortie.utilisateur,
                'objet': sortie
            })
        
        # Trier les mouvements par date (du plus récent au plus ancien)
        mouvements.sort(key=lambda x: x['date'], reverse=True)
        
        # Ajouter les données au contexte
        context.update({
            'date_debut': date_debut,
            'date_fin': date_fin,
            'type_mouvement': type_mouvement,
            'produit_selected': Produit.objects.filter(id=produit_id).first() if produit_id else None,
            'mouvements_par_jour': mouvements_par_jour,
            'total_entrees': total_entrees,
            'total_sorties': total_sorties,
            'total_general': total_general,
            'produits_vendus': produits_vendus,
            'fournisseurs': fournisseurs,
            'produits': Produit.objects.all().order_by('designation'),
            'mouvements': mouvements,  # Ajout des mouvements combinés
        })
        
        return context


class RapportVentesView(LoginRequiredMixin, TemplateView):
    """Rapport des ventes"""
    template_name = 'stock/rapports/ventes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les paramètres de filtre
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        # Définir les dates par défaut (30 derniers jours)
        if not date_debut or not date_fin:
            date_fin = timezone.now().date()
            date_debut = date_fin - timedelta(days=30)
            date_debut = date_debut.strftime('%Y-%m-%d')
            date_fin = date_fin.strftime('%Y-%m-%d')
        
        # Récupérer les ventes dans la période
        ventes = SortieStock.objects.filter(
            date__date__range=[date_debut, date_fin]
        ).select_related('produit', 'utilisateur')
        
        # Calculer les totaux
        total_ventes = ventes.count()
        total_quantite = ventes.aggregate(total=Sum('quantite'))['total'] or 0
        total_montant = ventes.aggregate(total=Sum(F('quantite') * F('prix_unitaire')))['total'] or 0
        
        # Ventes par jour
        ventes_par_jour = ventes.annotate(
            jour=TruncDay('date')
        ).values('jour').annotate(
            nb_ventes=Count('id'),
            quantite=Sum('quantite'),
            montant=Sum(F('quantite') * F('prix_unitaire'))
        ).order_by('jour')
        
        # Préparer les données pour le graphique
        jours = [v['jour'].strftime('%d/%m') for v in ventes_par_jour]
        montants = [float(v['montant'] or 0) for v in ventes_par_jour]
        
        # Produits les plus vendus
        produits_vendus = ventes.values(
            'produit__designation', 'produit__code'
        ).annotate(
            quantite=Sum('quantite'),
            montant=Sum(F('quantite') * F('prix_unitaire'))
        ).order_by('-quantite')[:10]
        
        # Ventes par utilisateur
        ventes_par_utilisateur = ventes.values(
            'utilisateur__first_name', 'utilisateur__last_name', 'utilisateur_id'
        ).annotate(
            nb_ventes=Count('id'),
            quantite=Sum('quantite'),
            montant=Sum(F('quantite') * F('prix_unitaire'))
        ).order_by('-montant')
        
        # Ajouter les données au contexte
        context.update({
            'date_debut': date_debut,
            'date_fin': date_fin,
            'total_ventes': total_ventes,
            'total_quantite': total_quantite,
            'total_montant': total_montant,
            'jours': jours,
            'montants': montants,
            'produits_vendus': produits_vendus,
            'ventes_par_utilisateur': ventes_par_utilisateur,
        })
        
        return context
