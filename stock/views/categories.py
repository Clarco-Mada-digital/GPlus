from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

from ..models import Categorie
from ..forms import CategorieForm


class ListeCategoriesView(LoginRequiredMixin, ListView):
    model = Categorie
    template_name = 'stock/categories/liste.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        queryset = Categorie.objects.annotate(
            nombre_produits=Count('produit')
        ).order_by('nom')
        
        # Filtre par recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AjouterCategorieView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Categorie
    form_class = CategorieForm
    template_name = 'stock/categories/form.html'
    success_url = reverse_lazy('stock:liste_categories')
    permission_required = 'stock.add_categorie'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("La catégorie a été ajoutée avec succès."))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Ajouter une catégorie")
        context['submit_text'] = _("Ajouter")
        return context


class ModifierCategorieView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Categorie
    form_class = CategorieForm
    template_name = 'stock/categories/form.html'
    success_url = reverse_lazy('stock:liste_categories')
    permission_required = 'stock.change_categorie'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("La catégorie a été modifiée avec succès."))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Modifier la catégorie")
        context['submit_text'] = _("Enregistrer les modifications")
        return context


class SupprimerCategorieView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Categorie
    template_name = 'stock/categories/supprimer.html'
    success_url = reverse_lazy('stock:liste_categories')
    permission_required = 'stock.delete_categorie'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produits_associes'] = self.get_object().produit_set.count()
        return context
    
    def delete(self, request, *args, **kwargs):
        categorie = self.get_object()
        
        # Vérifier s'il y a des produits associés
        if categorie.produit_set.exists():
            messages.error(
                request,
                _("Impossible de supprimer cette catégorie car elle est utilisée par des produits.")
            )
            return self.get(request, *args, **kwargs)
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("La catégorie a été supprimée avec succès."))
        return response
