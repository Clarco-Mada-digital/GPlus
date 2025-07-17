from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View, ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.conf import settings
from django.db.models import Q, Count, Value, CharField, Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Concat, TruncDate, TruncMonth, ExtractMonth, ExtractYear
from django.db import transaction, models
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.urls import reverse
from stock.models import Produit, Categorie, SortieStock, EntreeStock
from facture.models import Service, Facture
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
import json
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProduitSuggestionsView(View):
    """Vue API pour les suggestions de recherche de produits"""
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            query = request.GET.get('q', '').strip()
            
            if not query or len(query) < 2:
                return JsonResponse([], safe=False)
                
            # Recherche dans la désignation et le code
            produits = Produit.objects.filter(
                Q(designation__icontains=query) |
                Q(code__icontains=query),
                quantite_stock__gt=0
            ).annotate(
                full_info=Concat(
                    'designation',
                    Value(' ('),
                    'code',
                    Value(')'),
                    output_field=CharField()
                )
            ).values('id', 'designation', 'code', 'prix_vente')[:10]  # Limiter à 10 résultats
            
            # Formater les résultats pour le frontend
            suggestions = [{
                'id': p['id'],
                'designation': p['designation'],
                'code': p['code'],
                'prix_vente': float(p['prix_vente'])  # S'assurer que c'est un float pour le JSON
            } for p in produits]
            
            return JsonResponse(suggestions, safe=False)
            
        except Exception as e:
            logger.error(f"Erreur dans la vue ProduitSuggestionsView: {str(e)}", exc_info=True)
            return JsonResponse([], status=500, safe=False)

class VenteView(View):
    """Vue pour le point de vente"""
    template_name = 'vente/index.html'
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            # Récupérer les paramètres de filtre
            categorie_id = request.GET.get('categorie', '')
            recherche = request.GET.get('recherche', '').strip()
            prix_min = request.GET.get('prix_min', '')
            prix_max = request.GET.get('prix_max', '')
            
            # Initialiser la requête avec les produits en stock
            produits = Produit.objects.filter(quantite_stock__gt=0).select_related('categorie')
            
            # Récupérer toutes les catégories pour le filtre avec le nombre de produits
            categories = Categorie.objects.annotate(
                produit_count=Count('produit', filter=Q(produit__quantite_stock__gt=0))
            ).order_by('nom')
            
            # Récupérer tous les services
            services = Service.objects.all().order_by('nom_service')
            
            # Log des paramètres de requête pour le débogage
            logger.debug(f"Paramètres de requête - categorie: {categorie_id}, recherche: {recherche}, prix_min: {prix_min}, prix_max: {prix_max}")
            
            # Appliquer le filtre par catégorie
            if categorie_id and categorie_id.isdigit():
                produits = produits.filter(categorie_id=int(categorie_id))
                logger.debug(f"Filtrage par catégorie ID: {categorie_id}")
            
            # Appliquer le filtre de recherche sur plusieurs champs
            if recherche:
                produits = produits.filter(
                    Q(designation__icontains=recherche) |
                    Q(code__icontains=recherche) |
                    Q(description__icontains=recherche)
                )
                logger.debug(f"Filtrage par recherche: {recherche}")
            
            # Appliquer le filtre par prix minimum
            if prix_min and prix_min.isdigit():
                produits = produits.filter(prix_vente__gte=float(prix_min))
                logger.debug(f"Filtrage par prix minimum: {prix_min}")
            
            # Appliquer le filtre par prix maximum
            if prix_max and prix_max.isdigit():
                produits = produits.filter(prix_vente__lte=float(prix_max))
                logger.debug(f"Filtrage par prix maximum: {prix_max}")
            
            # Trier les produits par désignation
            produits = produits.order_by('designation')
            
            # Préparer le contexte avec les paramètres de filtre actuels
            # Définir les seuils de stock (peuvent être déplacés dans les paramètres plus tard)
            stock_seuils = {
                'stock_faible': 5,
                'stock_moyen': 10,
                'stock_eleve': 20
            }
            
            context = {
                'produits': produits,
                'services': services,
                'categories': categories,
                'categorie_active': categorie_id if categorie_id and categorie_id.isdigit() else None,
                'recherche': recherche,
                'prix_min': prix_min,
                'prix_max': prix_max,
                'debug': settings.DEBUG,
                'stock_seuils': stock_seuils,
                'filters': {
                    'categorie': categorie_id,
                    'recherche': recherche,
                    'prix_min': prix_min,
                    'prix_max': prix_max,
                    'type': request.GET.get('type', 'produit')  # Ajout du type de filtre
                },
                'stock_seuils': {
                    'stock_eleve': 10,  # Seuil pour stock élevé
                    'stock_faible': 3,   # Seuil pour stock faible
                }
            }
            
            # Log du nombre de produits trouvés
            logger.info(f"{produits.count()} produits chargés pour la vue de vente")
            
            # Si aucun produit trouvé, afficher un message d'information
            if not produits.exists():
                if recherche or categorie_id:
                    messages.info(request, "Aucun produit ne correspond à vos critères de recherche.")
                else:
                    messages.warning(request, "Aucun produit disponible en stock. Veuillez réapprovisionner le stock.")
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Erreur dans la vue VenteView: {str(e)}", exc_info=True)
            # En cas d'erreur, on propage l'exception pour que Django gère l'affichage de l'erreur 500
            messages.error(request, "Une erreur est survenue lors du chargement de la page de vente.")
            raise  # Propage l'exception pour la gestion d'erreur standard de Django

# Alias pour la compatibilité avec les URLs existants
index = VenteView.as_view()

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class ValiderVenteView(View):
    """Vue pour valider une vente"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({'status': 'error', 'message': 'Aucun article dans la vente'}, status=400)
            
            # Créer une référence de vente unique pour le groupe d'articles
            timestamp = int(time.time())
            vente_reference = f"VNT-{request.user.id}-{timestamp}"
            client = data.get('client', 'Client non spécifié')
            
            # Liste pour stocker les sorties de stock créées
            sorties_crees = []
            services_factures = []
            
            # Vérifier d'abord tous les stocks avant de procéder aux modifications
            for item in items:
                item_id = item.get('id')
                quantite = int(item.get('quantite', 1))  # Par défaut 1 pour les services
                item_type = item.get('type', 'produit')  # 'produit' par défaut pour la rétrocompatibilité
                
                if quantite <= 0:
                    continue
                
                # Gestion des produits (vérification des stocks)
                if item_type == 'produit':
                    try:
                        produit = Produit.objects.get(id=item_id)
                        
                        # Vérifier si le stock est suffisant avec une marge de sécurité
                        if quantite <= 0:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Quantité invalide pour {produit.designation}.'
                            }, status=400)
                            
                        if produit.quantite_stock < quantite:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Stock insuffisant pour {produit.designation}. Stock disponible: {produit.quantite_stock}'
                            }, status=400)
                        
                    except Produit.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Produit avec ID {item_id} non trouvé'
                        }, status=404)
                # Gestion des services
                elif item_type == 'service':
                    try:
                        service = Service.objects.get(id=item_id)
                        services_factures.append({
                            'service': service,
                            'quantite': quantite,
                            'prix_unitaire': float(service.prix_unitaire)
                        })
                    except Service.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Service avec ID {item_id} non trouvé'
                        }, status=404)
            
            # Si on arrive ici, tous les stocks sont disponibles, on peut procéder à la vente
            try:
                with transaction.atomic():
                    # Traitement des produits
                    for item in items:
                        item_id = item.get('id')
                        quantite = int(item.get('quantite', 1))
                        item_type = item.get('type', 'produit')
                        
                        if quantite <= 0 or item_type != 'produit':
                            continue
                            
                        produit = Produit.objects.get(id=item_id)
                        
                        # Créer la sortie de stock avec la référence de vente commune
                        sortie = SortieStock.objects.create(
                            produit=produit,
                            quantite=quantite,
                            prix_unitaire=produit.prix_vente,
                            utilisateur=request.user,
                            client=client,
                            reference=vente_reference,
                            date=datetime.now()
                        )
                        sorties_crees.append(sortie)
                        
                        # Mettre à jour le stock du produit de manière atomique
                        updated = Produit.objects.filter(
                            id=produit.id, 
                            quantite_stock__gte=quantite
                        ).update(
                            quantite_stock=models.F('quantite_stock') - quantite
                        )
                        
                        # Vérifier que la mise à jour a bien eu lieu
                        if not updated:
                            raise ValueError(f"Échec de la mise à jour du stock pour {produit.designation}. Stock insuffisant ou produit introuvable.")
                            
                        # Rafraîchir l'objet produit pour avoir la valeur mise à jour
                        produit.refresh_from_db()
                    
                    # Traitement des services (création de facture)
                    if services_factures:
                        # Calculer le montant total des services
                        montant_total = sum(s['prix_unitaire'] * s['quantite'] for s in services_factures)
                        
                        # Préparer les données des services pour la facture
                        services_data = [{
                            'nom': s['service'].nom_service,
                            'quantite': s['quantite'],
                            'prix_unitaire': float(s['prix_unitaire']),
                            'total': float(s['prix_unitaire'] * s['quantite'])
                        } for s in services_factures]
                        
                        # Créer la facture pour les services
                        facture = Facture.objects.create(
                            ref=f"FAC-SERV-{int(time.time())}",
                            intitule=f"Facture pour services - {client}",
                            montant=montant_total,
                            client=client,
                            date_facture=datetime.now().date(),
                            etat_facture='Payé',
                            services=services_data,
                            created_by=request.user,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        # Créer une entrée dans SortieStock pour le suivi (sans produit)
                        SortieStock.objects.create(
                            reference=vente_reference,
                            description=f"Services: {', '.join([s['service'].nom_service for s in services_factures])}",
                            quantite=1,
                            prix_unitaire=montant_total,
                            utilisateur=request.user,
                            client=client,
                            date=datetime.now(),
                            est_service=True
                        )
                        
            except Exception as e:
                logger.error(f"Erreur lors de la validation de la vente: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Erreur lors de la mise à jour du stock: {str(e)}'
                }, status=500)
            
            # Récupérer toutes les sorties de cette vente
            sorties = SortieStock.objects.filter(reference=vente_reference)
            
            # Utiliser la première sortie comme référence pour la redirection
            if sorties.exists():
                from django.contrib import messages
                from django.shortcuts import redirect, reverse
                
                # Stocker le message de succès dans la session
                messages.success(request, 'Vente validée avec succès')
                
                # Rediriger vers la page de détail de la vente
                return JsonResponse({
                    'status': 'redirect',
                    'url': reverse('vente:detail_vente', kwargs={'vente_id': sorties.first().id})
                })
            
            return JsonResponse({
                'status': 'success',
                'message': 'Vente validée avec succès',
                'reference': vente_reference,
                'timestamp': int(time.time())
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Données invalides'}, status=400)
        except Exception as e:
            logger.error(f"Erreur lors de la validation de la vente: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Une erreur est survenue'}, status=500)

# Alias pour la vue de validation de vente
valider_vente = ValiderVenteView.as_view()

@login_required
@require_POST
@csrf_exempt
def annuler_vente(request, reference):
    """Vue pour annuler une vente et restaurer les quantités en stock"""
    try:
        with transaction.atomic():
            # Récupérer toutes les sorties liées à cette référence
            sorties = SortieStock.objects.filter(
                reference=reference,
                annulee=False  # Ne pas traiter les sorties déjà annulées
            ).select_related('produit')
            
            if not sorties.exists():
                return JsonResponse(
                    {'success': False, 'message': 'Aucune vente active trouvée avec cette référence'}, 
                    status=404
                )
            
            # Annuler chaque sortie de la vente
            for sortie in sorties:
                # Utiliser la méthode annuler() du modèle qui gère déjà la restauration du stock
                # et la création de l'entrée d'annulation
                sortie.annuler(utilisateur=request.user)
            
            messages.success(request, f'La vente {reference} a été annulée avec succès.')
            return JsonResponse({'success': True, 'message': 'Vente annulée avec succès'})
            
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de la vente {reference}: {str(e)}", exc_info=True)
        return JsonResponse(
            {'success': False, 'message': f'Une erreur est survenue: {str(e)}'}, 
            status=500
        )

class DetailVenteView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'une vente"""
    model = SortieStock
    template_name = 'vente/detail_vente.html'
    context_object_name = 'vente'
    pk_url_kwarg = 'vente_id'
    
    def get_queryset(self):
        return SortieStock.objects.select_related('produit', 'utilisateur')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupérer toutes les sorties de stock avec la même référence
        sorties = SortieStock.objects.filter(
            reference=self.object.reference
        ).select_related('produit')
        
        # Calculer le montant total et la quantité totale de la vente
        montant_total = 0
        quantite_totale = 0
        
        for sortie in sorties:
            montant_total += sortie.quantite * float(sortie.prix_unitaire)
            quantite_totale += sortie.quantite
        
        context.update({
            'sorties': sorties,
            'montant_total': montant_total,
            'quantite_totale': quantite_totale
        })
        return context

class HistoriqueVenteView(LoginRequiredMixin, ListView):
    """Vue pour afficher l'historique des ventes groupées par référence"""
    model = SortieStock
    template_name = 'vente/historique_vente.html'
    context_object_name = 'ventes_groupes'
    paginate_by = 15  # Nombre d'éléments par page
    
    def get_queryset(self):
        # Récupérer les références uniques avec les informations de la première sortie
        queryset = super().get_queryset().select_related('produit', 'utilisateur')
        
        # Filtrer par date si fourni
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if date_debut:
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
            queryset = queryset.filter(date__date__gte=date_debut)
            
        if date_fin:
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d')
            # Ajouter un jour pour inclure toute la journée de fin
            date_fin = date_fin + timedelta(days=1)
            queryset = queryset.filter(date__date__lte=date_fin)
        
        # Utiliser annotate pour regrouper par référence et calculer les totaux
        from django.db.models import Sum, Count, Min
        
        # Récupérer les références uniques avec les informations agrégées
        references = queryset.values('reference').annotate(
            date_min=Min('date'),
            montant_total=Sum('prix_unitaire'),
            nombre_articles=Count('id'),
            first_sortie_id=Min('id')  # Pour récupérer les informations de la première sortie
        ).order_by('-date_min')
        
        # Récupérer les informations détaillées des premières sorties
        sorties_ids = [ref['first_sortie_id'] for ref in references]
        sorties_map = {s.id: s for s in SortieStock.objects.filter(id__in=sorties_ids).select_related('utilisateur')}
        
        # Construire la liste des ventes groupées
        ventes_groupes = []
        for ref in references:
            sortie = sorties_map.get(ref['first_sortie_id'])
            if sortie:
                ventes_groupes.append({
                    'reference': ref['reference'],
                    'date': sortie.date,
                    'utilisateur': sortie.utilisateur,
                    'client': sortie.client,
                    'nombre_articles': ref['nombre_articles'],
                    'montant_total': ref['montant_total'],
                    'sorties': queryset.filter(reference=ref['reference'])  # Pour la compatibilité
                })
        
        return ventes_groupes
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer la liste complète non paginée pour les totaux
        queryset = self.get_queryset()
        
        # Calculer les totaux sur l'ensemble des résultats
        context['total_ventes'] = len(queryset)
        context['montant_total'] = sum(v['montant_total'] for v in queryset)
        context['total_articles'] = sum(v['nombre_articles'] for v in queryset)
        
        # Ajouter les paramètres de filtre pour les garder dans la pagination
        context['date_debut'] = self.request.GET.get('date_debut', '')
        context['date_fin'] = self.request.GET.get('date_fin', '')
        
        # Ajouter la pagination personnalisée
        page_obj = context.get('page_obj')
        if page_obj:
            paginator = page_obj.paginator
            context['pagination'] = {
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else 1,
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else paginator.num_pages,
                'current_page': page_obj.number,
                'num_pages': paginator.num_pages,
                'page_range': range(1, paginator.num_pages + 1),
                'count': paginator.count,
                'start_index': page_obj.start_index(),
                'end_index': page_obj.end_index(),
            }
        
        return context

class RapportsView(LoginRequiredMixin, TemplateView):
    """Vue pour afficher les rapports et statistiques"""
    template_name = 'vente/rapports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Période par défaut : 30 derniers jours
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)
        
        context.update({
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
        })
        
        return context


@login_required
def ventes_par_jour(request):
    """API pour les données de ventes par jour"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filtrer les ventes par date si fourni
    sorties = SortieStock.objects.all()
    
    if start_date and end_date:
        sorties = sorties.filter(date__date__range=[start_date, end_date])
    
    # Calculer le total pour chaque jour
    ventes_par_jour = sorties.annotate(
        jour=TruncDate('date'),
        total_vente=ExpressionWrapper(
            F('prix_unitaire') * F('quantite'),
            output_field=DecimalField()
        )
    ).values('jour').annotate(
        total=Sum('total_vente', output_field=DecimalField())
    ).order_by('jour')
    
    # Formater les données pour Chart.js
    labels = [vente['jour'].strftime('%d/%m/%Y') for vente in ventes_par_jour]
    data = [float(vente['total'] or 0) for vente in ventes_par_jour]
    
    return JsonResponse({
        'labels': labels,
        'datasets': [{
            'label': 'Ventes (Ar)',
            'data': data,
            'backgroundColor': 'rgba(59, 130, 246, 0.5)',
            'borderColor': 'rgba(59, 130, 246, 1)',
            'borderWidth': 1
        }]
    })


@login_required
def ventes_par_categorie(request):
    """API pour les ventes par catégorie"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filtrer les ventes par date si fourni
    sorties = SortieStock.objects.select_related('produit__categorie')
    
    if start_date and end_date:
        sorties = sorties.filter(date__date__range=[start_date, end_date])
    
    # Grouper par catégorie
    ventes_par_cat = sorties.annotate(
        total_vente=ExpressionWrapper(
            F('prix_unitaire') * F('quantite'),
            output_field=DecimalField()
        )
    ).values(
        'produit__categorie__nom'
    ).annotate(
        total=Sum('total_vente', output_field=DecimalField())
    ).order_by('-total')
    
    # Formater les données pour Chart.js
    labels = [v['produit__categorie__nom'] or 'Sans catégorie' for v in ventes_par_cat]
    data = [float(v['total'] or 0) for v in ventes_par_cat]
    
    # Couleurs pour les catégories
    background_colors = [
        'rgba(59, 130, 246, 0.7)',  # Bleu
        'rgba(16, 185, 129, 0.7)',  # Vert
        'rgba(245, 158, 11, 0.7)',  # Jaune
        'rgba(239, 68, 68, 0.7)',   # Rouge
        'rgba(139, 92, 246, 0.7)',  # Violet
        'rgba(20, 184, 166, 0.7)',  # Turquoise
        'rgba(249, 115, 22, 0.7)',  # Orange
        'rgba(236, 72, 153, 0.7)',  # Rose
    ]
    
    return JsonResponse({
        'labels': labels,
        'datasets': [{
            'data': data,
            'backgroundColor': background_colors[:len(labels)],
            'borderWidth': 1
        }]
    })


@login_required
def meilleurs_produits(request):
    """API pour les meilleurs produits par quantité vendue"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    limit = int(request.GET.get('limit', 10))
    
    # Filtrer les ventes par date si fourni
    sorties = SortieStock.objects.select_related('produit')
    
    if start_date and end_date:
        sorties = sorties.filter(date__date__range=[start_date, end_date])
    
    # Grouper par produit et calculer les totaux
    meilleurs = sorties.annotate(
        total_vente=ExpressionWrapper(
            F('prix_unitaire') * F('quantite'),
            output_field=DecimalField()
        )
    ).values(
        'produit__designation'
    ).annotate(
        quantite=Sum('quantite'),
        total=Sum('total_vente', output_field=DecimalField())
    ).order_by('-quantite')[:limit]
    
    # Formater les données
    produits = [{
        'produit': m['produit__designation'],
        'quantite': m['quantite'],
        'total': float(m['total'] or 0)
    } for m in meilleurs]
    
    return JsonResponse({'produits': produits})
