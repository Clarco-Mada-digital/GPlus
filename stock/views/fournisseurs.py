from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, F
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
            nombre_entrees=Count('entrees', distinct=True),
            total_achats=Sum('entrees__quantite' * F('entrees__prix_unitaire'))
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
        fournisseur = self.get_object()
        
        # Compter les produits associés
        context['produits_associes'] = fournisseur.produit_set.count()
        
        # Compter les entrées de stock associées
        context['entrees_associees'] = fournisseur.entrees.count()
        
        return context
    
    def delete(self, request, *args, **kwargs):
        fournisseur = self.get_object()
        
        # Vérifier s'il y a des produits ou des entrées associés
        if fournisseur.produit_set.exists() or fournisseur.entrees.exists():
            messages.error(
                request,
                _("Impossible de supprimer ce fournisseur car il est utilisé par des produits ou des entrées de stock.")
            )
            return self.get(request, *args, **kwargs)
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("Le fournisseur a été supprimé avec succès."))
        return response


class DetailFournisseurView(LoginRequiredMixin, DetailView):
    model = Fournisseur
    template_name = 'stock/fournisseurs/detail.html'
    context_object_name = 'fournisseur'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fournisseur = self.get_object()
        
        # Dernières entrées de stock
        context['dernieres_entrees'] = fournisseur.entrees.select_related('produit', 'utilisateur') \
            .order_by('-date')[:5]
        
        # Produits fournis
        context['produits'] = fournisseur.produit_set.all()
        
        # Statistiques des achats (30 derniers jours)
        date_limite = timezone.now() - timedelta(days=30)
        
        total_achats = fournisseur.entrees.filter(date__gte=date_limite) \
            .aggregate(total=Sum(F('quantite') * F('prix_unitaire')))['total'] or 0
        
        nombre_entrees = fournisseur.entrees.filter(date__gte=date_limite).count()
        
        context['total_achats'] = total_achats
        context['nombre_entrees'] = nombre_entrees
        
        # Évolution des achats par mois (6 derniers mois)
        maintenant = timezone.now()
        six_mois = maintenant - timedelta(days=180)
        
        achats_par_mois = fournisseur.entrees.filter(date__gte=six_mois) \
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
