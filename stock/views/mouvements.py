from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, DetailView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import F, Sum, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction

from ..models import EntreeStock, SortieStock, Produit, Fournisseur
from ..forms import EntreeStockForm, SortieStockForm, AnnulerEntreeForm


class ListeEntreesView(LoginRequiredMixin, ListView):
    model = EntreeStock
    template_name = 'stock/mouvements/entree_liste.html'
    context_object_name = 'entrees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EntreeStock.objects.select_related(
            'produit', 'fournisseur', 'utilisateur'
        ).order_by('-date')
        
        # Filtre par produit
        produit_id = self.request.GET.get('produit', '').strip()
        if produit_id and produit_id.isdigit():
            queryset = queryset.filter(produit_id=int(produit_id))
        
        # Filtre par fournisseur
        fournisseur_id = self.request.GET.get('fournisseur', '').strip()
        if fournisseur_id and fournisseur_id.isdigit():
            queryset = queryset.filter(fournisseur_id=int(fournisseur_id))
        
        # Filtre par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(date__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__date__lte=date_fin)
        
        # Filtre par statut (annulé ou non)
        statut = self.request.GET.get('statut')
        if statut == 'annulees':
            queryset = queryset.filter(annulee=True)
        elif statut == 'validees':
            queryset = queryset.filter(annulee=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les filtres
        produit_id = self.request.GET.get('produit')
        fournisseur_id = self.request.GET.get('fournisseur')
        date_debut = self.request.GET.get('date_debut', '')
        date_fin = self.request.GET.get('date_fin', '')
        statut = self.request.GET.get('statut', '')
        
        # Ajouter les filtres au contexte
        context['produit'] = Produit.objects.filter(id=produit_id).first()
        context['fournisseur'] = Fournisseur.objects.filter(id=fournisseur_id).first()
        context['date_debut'] = date_debut
        context['date_fin'] = date_fin
        context['statut'] = statut
        
        # Calculer les totaux
        total_quantite = sum(e.quantite for e in context['entrees'])
        total_montant = sum(e.montant_total for e in context['entrees'])
        
        context['total_quantite'] = total_quantite
        context['total_montant'] = total_montant
        
        return context


class DetailEntreeView(LoginRequiredMixin, DetailView):
    model = EntreeStock
    template_name = 'stock/mouvements/entree_detail.html'
    context_object_name = 'entree'
    permission_required = 'stock.view_entree_stock'

    def get_queryset(self):
        return EntreeStock.objects.select_related('produit', 'fournisseur', 'utilisateur')


class ModifierEntreeView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = EntreeStock
    form_class = EntreeStockForm
    template_name = 'stock/mouvements/entree_form.html'
    context_object_name = 'entree'
    permission_required = 'stock.change_entree_stock'

    def get_queryset(self):
        return EntreeStock.objects.select_related('produit', 'fournisseur', 'utilisateur')

    def get_success_url(self):
        return reverse('stock:detail_entree', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Modifier une entrée de stock"
        return context


class AjouterEntreeView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EntreeStock
    form_class = EntreeStockForm
    template_name = 'stock/mouvements/entree_form.html'
    permission_required = 'stock.add_entree_stock'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['utilisateur'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _("L'entrée en stock a été enregistrée avec succès."))
        return response
    
    def get_success_url(self):
        if 'enregistrer_ajouter' in self.request.POST:
            return reverse('stock:ajouter_entree')
        return reverse('stock:liste_entrees')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Nouvelle entrée en stock")
        context['submit_text'] = _("Enregistrer")
        context['submit_and_add'] = True
        return context


class AnnulerEntreeView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = EntreeStock
    form_class = AnnulerEntreeForm
    template_name = 'stock/mouvements/annuler_entree.html'
    permission_required = 'stock.change_entree_stock'
    
    def form_valid(self, form):
        with transaction.atomic():
            entree = self.get_object()
            entree.annulee = True
            entree.motif_annulation = form.cleaned_data['motif_annulation']
            entree.utilisateur_annulation = self.request.user
            entree.date_annulation = timezone.now()
            
            # Mettre à jour le stock
            Produit.objects.filter(id=entree.produit_id).update(
                quantite_stock=F('quantite_stock') - entree.quantite
            )
            
            entree.save()
            
            messages.success(self.request, _("L'entrée en stock a été annulée avec succès."))
            return redirect('stock:liste_entrees')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entree'] = self.get_object()
        return context


class ListeSortiesView(LoginRequiredMixin, ListView):
    model = SortieStock
    template_name = 'stock/mouvements/sortie_liste.html'
    context_object_name = 'sorties'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SortieStock.objects.select_related(
            'produit', 'utilisateur'
        ).order_by('-date')
        
        # Filtre par produit
        produit_id = self.request.GET.get('produit')
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
        
        # Filtre par client
        client = self.request.GET.get('client')
        if client:
            queryset = queryset.filter(client__icontains=client)
        
        # Filtre par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(date__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__date__lte=date_fin)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les filtres
        produit_id = self.request.GET.get('produit')
        client = self.request.GET.get('client', '')
        date_debut = self.request.GET.get('date_debut', '')
        date_fin = self.request.GET.get('date_fin', '')
        
        # Ajouter les filtres au contexte
        context['produit'] = Produit.objects.filter(id=produit_id).first()
        context['client'] = client
        context['date_debut'] = date_debut
        context['date_fin'] = date_fin
        
        # Calculer les totaux
        total_quantite = sum(s.quantite for s in context['sorties'])
        total_montant = sum(s.montant_total for s in context['sorties'])
        
        context['total_quantite'] = total_quantite
        context['total_montant'] = total_montant
        
        return context


class AjouterSortieView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SortieStock
    form_class = SortieStockForm
    template_name = 'stock/mouvements/sortie_form.html'
    permission_required = 'stock.add_sortiestock'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['utilisateur'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        
        # Vérifier le stock disponible
        produit = form.cleaned_data['produit']
        quantite = form.cleaned_data['quantite']
        
        if produit.quantite_stock < quantite:
            form.add_error('quantite', _("Stock insuffisant. Quantité disponible : %(quantite)d") % {
                'quantite': produit.quantite_stock
            })
            return self.form_invalid(form)
        
        response = super().form_valid(form)
        messages.success(self.request, _("La sortie de stock a été enregistrée avec succès."))
        return response
    
    def get_success_url(self):
        if 'enregistrer_ajouter' in self.request.POST:
            return reverse('stock:ajouter_sortie')
        return reverse('stock:liste_sorties')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Nouvelle sortie de stock")
        context['submit_text'] = _("Enregistrer")
        context['submit_and_add'] = True
        return context


class AnnulerSortieView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stock.delete_sortiestock'
    
    def post(self, request, *args, **kwargs):
        sortie = get_object_or_404(SortieStock, pk=kwargs['pk'])
        
        with transaction.atomic():
            # Restaurer le stock
            Produit.objects.filter(id=sortie.produit_id).update(
                quantite_stock=F('quantite_stock') + sortie.quantite
            )
            
            # Supprimer la sortie
            sortie.delete()
            
            messages.success(request, _("La sortie de stock a été annulée avec succès."))
            return redirect('stock:liste_sorties')


@method_decorator(csrf_exempt, name='dispatch')
class GetPrixProduitView(LoginRequiredMixin, View):
    """Vue pour récupérer le prix d'un produit en AJAX"""
    
    def get(self, request, *args, **kwargs):
        produit_id = request.GET.get('produit_id')
        type_prix = request.GET.get('type_prix', 'vente')  # 'vente' ou 'achat'
        
        try:
            produit = Produit.objects.get(id=produit_id)
            prix = produit.prix_vente if type_prix == 'vente' else produit.prix_achat
            return JsonResponse({'success': True, 'prix': float(prix)})
        except (Produit.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': 'Produit non trouvé'}, status=404)
