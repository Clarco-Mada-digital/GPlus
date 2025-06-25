from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from django.db import connection
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.generic import TemplateView
from datetime import datetime, timedelta
from ..models import Produit, EntreeStock, SortieStock, Categorie, Fournisseur


class TableauBordView(LoginRequiredMixin, TemplateView):
    template_name = 'stock/tableau_bord.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les statistiques principales avec une seule requête
        stats_produits = Produit.objects.aggregate(
            total=Count('id'),
            en_alerte=Count('id', filter=Q(quantite_stock__lte=F('seuil_alerte'))),
            valeur_totale=Sum(F('quantite_stock') * F('prix_vente'))
        )
        
        # Calcul des mouvements des 7 derniers jours
        date_limite = timezone.now() - timedelta(days=7)
        stats_mouvements = {
            'entrees': EntreeStock.objects.filter(date__gte=date_limite).count(),
            'sorties': SortieStock.objects.filter(date__gte=date_limite).count(),
        }
        
        # Derniers mouvements optimisés avec une seule requête
        from itertools import chain
        # Récupérer les entrées et sorties
        entrees = list(EntreeStock.objects.select_related('produit', 'utilisateur')
                              .order_by('-date')[:10])
        sorties = list(SortieStock.objects.select_related('produit', 'utilisateur')
                               .order_by('-date')[:10])
        
        # Ajouter le type de mouvement à chaque entrée/sortie
        for entree in entrees:
            entree.type_mouvement = 'entree'
        for sortie in sorties:
            sortie.type_mouvement = 'sortie'
            
        # Combiner et trier les mouvements
        derniers_mouvements = sorted(
            entrees + sorties,
            key=lambda x: x.date,
            reverse=True
        )[:10]  # Limiter à 10 mouvements
        
        # Trier par date les mouvements combinés
        context['derniers_mouvements'] = sorted(
            derniers_mouvements,
            key=lambda x: x.date,
            reverse=True
        )[:10]  # Limiter à 10 mouvements au total
        
        # Générer les données pour le graphique (7 derniers jours)
        today = timezone.now().date()
        context['dates'] = [
            (today - timedelta(days=i)).strftime('%d/%m') 
            for i in range(6, -1, -1)  # 7 derniers jours
        ]
        
        # Récupérer les données des 7 derniers jours
        date_limite = today - timedelta(days=7)
        
        # Récupérer les entrées
        entrees = EntreeStock.objects.filter(date__gte=date_limite)
        sorties = SortieStock.objects.filter(date__gte=date_limite)
        
        # Initialiser les séries avec des zéros
        context['serie_entrees'] = [0] * 7
        context['serie_sorties'] = [0] * 7
        
        # Remplir les séries avec les données réelles
        for i in range(7):
            date_cible = today - timedelta(days=6-i)
            
            # Compter les entrées pour ce jour
            entree_jour = sum(
                e.quantite for e in entrees 
                if e.date.date() == date_cible
            )
            
            # Compter les sorties pour ce jour
            sortie_jour = sum(
                s.quantite for s in sorties
                if s.date.date() == date_cible
            )
            
            context['serie_entrees'][i] = entree_jour
            context['serie_sorties'][i] = sortie_jour
        
        # Produits les plus vendus (30 derniers jours)
        if SortieStock.objects.exists():
            date_limite = timezone.now() - timedelta(days=30)
            produits_vendus = SortieStock.objects.filter(date__gte=date_limite) \
                .values('produit__designation') \
                .annotate(total=Sum('quantite')) \
                .order_by('-total')[:5]
            
            context['produits_vendus'] = [
                {
                    'produit': p['produit__designation'],
                    'quantite': p['total']
                } for p in produits_vendus
            ]
        else:
            context['produits_vendus'] = []
        
        return context


from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def get_chart_data(request):
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': 'Authentification requise'}, 
                status=401
            )
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    try:
        # Récupérer le nombre de jours depuis le paramètre de requête
        nb_jours = int(request.GET.get('days', 7))
        if nb_jours not in [7, 30, 90]:
            nb_jours = 7
            
        date_limite = timezone.now() - timedelta(days=nb_jours)
        
        # Générer les dates pour la période sélectionnée
        dates = [(timezone.now().date() - timedelta(days=i)).strftime('%d/%m') for i in range(nb_jours-1, -1, -1)]
        
        # Récupérer les données pour le graphique
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                date(date) as jour, 
                COALESCE(SUM(CASE WHEN type_mouvement = 'entree' THEN quantite ELSE 0 END), 0) as entrees,
                COALESCE(SUM(CASE WHEN type_mouvement = 'sortie' THEN quantite ELSE 0 END), 0) as sorties
            FROM (
                SELECT date, quantite, 'entree' as type_mouvement FROM stock_entreestock
                WHERE date >= %s
                UNION ALL
                SELECT date, quantite, 'sortie' as type_mouvement FROM stock_sortiestock
                WHERE date >= %s
            ) as mouvements
            GROUP BY date(date)
            ORDER BY jour
        """, [date_limite, date_limite])
        
        # Traiter les résultats
        mouvements_par_jour = {}
        for date, entrees, sorties in cursor.fetchall():
            if isinstance(date, str):
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    date_str = date_obj.strftime('%d/%m')
                except (ValueError, TypeError):
                    continue
            else:
                date_str = date.strftime('%d/%m')
            mouvements_par_jour[date_str] = {'entrees': int(entrees or 0), 'sorties': int(sorties or 0)}
        
        # Préparer les séries pour le graphique
        serie_entrees = []
        serie_sorties = []
        
        for date in dates:
            data = mouvements_par_jour.get(date, {'entrees': 0, 'sorties': 0})
            serie_entrees.append(data['entrees'])
            serie_sorties.append(data['sorties'])
        
        return JsonResponse({
            'status': 'success',
            'dates': dates,
            'entrees': serie_entrees,
            'sorties': serie_sorties,
            'periode': nb_jours
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
