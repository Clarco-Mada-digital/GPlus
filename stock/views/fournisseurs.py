from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404

from ..models import Fournisseur, EntreeStock, Produit
from ..forms import FournisseurForm


class ListeFournisseursView(LoginRequiredMixin, ListView):
    model = Fournisseur
    template_name = 'stock/fournisseurs/liste.html'
    context_object_name = 'fournisseurs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Fournisseur.objects.annotate(
            nombre_produits=Count('produit', distinct=True),
            nombre_entrees=Count('entreestock', distinct=True),
            total_achats=Sum(
                ExpressionWrapper(
                    F('entreestock__quantite') * F('entreestock__prix_unitaire'),
                    output_field=DecimalField()
                )
            )
        ).order_by('nom')
        
        # Filtre par recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(email__icontains=search) |
                Q(telephone__icontains=search) |
                Q(contact__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AjouterFournisseurView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'stock/fournisseurs/form.html'
    success_url = reverse_lazy('stock:liste_fournisseurs')
    permission_required = 'stock.add_fournisseur'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Le fournisseur a été ajouté avec succès."))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Ajouter un fournisseur")
        context['submit_text'] = _("Ajouter")
        return context


class ModifierFournisseurView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'stock/fournisseurs/form.html'
    success_url = reverse_lazy('stock:liste_fournisseurs')
    permission_required = 'stock.change_fournisseur'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Le fournisseur a été modifié avec succès."))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = _("Modifier le fournisseur")
        context['submit_text'] = _("Enregistrer les modifications")
        return context


class SupprimerFournisseurView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Fournisseur
    template_name = 'stock/fournisseurs/supprimer.html'
    success_url = reverse_lazy('stock:liste_fournisseurs')
    permission_required = 'stock.delete_fournisseur'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Supprimer le fournisseur")
        context['message'] = _("Êtes-vous sûr de vouloir supprimer ce fournisseur ?")
        context['cancel_url'] = reverse_lazy('stock:liste_fournisseurs')
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Vérifier si le fournisseur a des produits associés
        if self.object.produit_set.exists():
            messages.error(
                self.request,
                _("Impossible de supprimer ce fournisseur car il est associé à des produits.")
            )
            return self.render_to_response(self.get_context_data())
            
        # Vérifier si le fournisseur a des entrées en stock
        if self.object.entree_stock.exists():
            messages.error(
                self.request,
                _("Impossible de supprimer ce fournisseur car il a des entrées en stock associées.")
            )
            return self.render_to_response(self.get_context_data())
            
        messages.success(self.request, _("Le fournisseur a été supprimé avec succès."))
        return super().delete(request, *args, **kwargs)


class DetailFournisseurView(LoginRequiredMixin, DetailView):
    model = Fournisseur
    template_name = 'stock/fournisseurs/detail.html'
    context_object_name = 'fournisseur'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fournisseur = self.get_object()
        
        # Récupérer les produits du fournisseur avec les informations nécessaires
        produits = fournisseur.produit_set.all().select_related('categorie').annotate(
            quantite=Sum('entreestock__quantite', distinct=True)
        )
        
        # Récupérer les entrées de stock récentes
        entrees = fournisseur.entreestock_set.select_related('produit').order_by('-date')[:10]
        
        # Statistiques des achats (30 derniers jours)
        date_limite = timezone.now() - timedelta(days=30)
        
        total_achats = fournisseur.entreestock_set.filter(date__gte=date_limite) \
            .aggregate(total=Sum(F('quantite') * F('prix_unitaire')))['total'] or 0
        
        nombre_entrees = fournisseur.entreestock_set.filter(date__gte=date_limite).count()
        
        # Ajouter les données au contexte
        context['produits'] = produits
        context['entrees_recentes'] = entrees
        context['total_achats'] = total_achats
        context['nombre_entrees'] = nombre_entrees
        
        # Évolution des achats par mois (6 derniers mois)
        maintenant = timezone.now()
        six_mois = maintenant - timedelta(days=180)
        
        achats_par_mois = fournisseur.entreestock_set.filter(date__gte=six_mois) \
            .annotate(mois=TruncMonth('date')) \
            .values('mois') \
            .annotate(total=Sum(F('quantite') * F('prix_unitaire'))) \
            .order_by('mois')
        
        # Préparer les données pour le graphique
        mois = []
        montants = []
        
        for achat in achats_par_mois:
            mois.append(achat['mois'].strftime('%b %Y'))
            montants.append(float(achat['total'] or 0))
        
        context['mois_achats'] = mois
        context['montants_achats'] = montants
        
        return context
