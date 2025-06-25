from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, F, Sum
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.detail import DetailView

from ..models import Produit, Categorie, EntreeStock, SortieStock
from ..forms import ProduitForm


class ListeProduitsView(LoginRequiredMixin, ListView):
    model = Produit
    template_name = 'stock/produits/liste.html'
    context_object_name = 'produits'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Produit.objects.select_related('categorie', 'fournisseur')
        
        # Filtre par recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(designation__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        
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
        
        # Tri
        order_by = self.request.GET.get('order_by', 'designation')
        if order_by in ['designation', 'code', 'quantite_stock', 'prix_vente']:
            direction = self.request.GET.get('direction', 'asc')
            if direction == 'desc':
                order_by = f'-{order_by}'
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Categorie.objects.all()
        context['statut'] = self.request.GET.get('statut', '')
        context['order_by'] = self.request.GET.get('order_by', 'designation')
        context['direction'] = self.request.GET.get('direction', 'asc')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AjouterProduitView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'stock/produits/form.html'
    success_url = reverse_lazy('stock:liste_produits')
    permission_required = 'stock.add_produit'
    
    def form_valid(self, form):
        form.instance.utilisateur_creation = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _("Le produit a été ajouté avec succès."))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Ajouter un produit")
        context['submit_text'] = _("Ajouter")
        return context


class ModifierProduitView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'stock/produits/form.html'
    success_url = reverse_lazy('stock:liste_produits')
    permission_required = 'stock.change_produit'
    
    def form_valid(self, form):
        form.instance.utilisateur_modification = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _("Le produit a été modifié avec succès."))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Modifier le produit")
        context['submit_text'] = _("Enregistrer les modifications")
        return context


class SupprimerProduitView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Produit
    template_name = 'stock/produits/supprimer.html'
    success_url = reverse_lazy('stock:liste_produits')
    permission_required = 'stock.delete_produit'
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("Le produit a été supprimé avec succès."))
        return response


class DetailProduitView(LoginRequiredMixin, DetailView):
    model = Produit
    template_name = 'stock/produits/detail.html'
    context_object_name = 'produit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produit = self.get_object()
        
        # Dernières entrées
        context['dernieres_entrees'] = EntreeStock.objects.filter(produit=produit) \
            .select_related('fournisseur', 'utilisateur') \
            .order_by('-date')[:5]
        
        # Dernières sorties
        context['dernieres_sorties'] = SortieStock.objects.filter(produit=produit) \
            .select_related('utilisateur') \
            .order_by('-date')[:5]
        
        # Statistiques des mouvements (30 derniers jours)
        date_limite = timezone.now() - timedelta(days=30)
        
        # Total des entrées et sorties
        total_entrees = EntreeStock.objects.filter(
            produit=produit,
            date__gte=date_limite
        ).aggregate(total=Sum('quantite'))['total'] or 0
        
        total_sorties = SortieStock.objects.filter(
            produit=produit,
            date__gte=date_limite
        ).aggregate(total=Sum('quantite'))['total'] or 0
        
        context['total_entrees'] = total_entrees
        context['total_sorties'] = total_sorties
        context['variation_stock'] = total_entrees - total_sorties
        
        return context


class StockFaibleView(LoginRequiredMixin, ListView):
    model = Produit
    template_name = 'stock/produits/stock_faible.html'
    context_object_name = 'produits'
    
    def get_queryset(self):
        return Produit.objects.filter(
            quantite_stock__lte=F('seuil_alerte')
        ).order_by('quantite_stock')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Produits en alerte de stock")
        return context
