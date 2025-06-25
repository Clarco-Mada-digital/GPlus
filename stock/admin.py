from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Categorie, Fournisseur, Produit, EntreeStock, SortieStock


class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'date_creation')
    search_fields = ('nom', 'description')
    list_filter = ('date_creation',)
    ordering = ('nom',)


class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone', 'contact', 'date_creation')
    search_fields = ('nom', 'email', 'contact')
    list_filter = ('date_creation',)
    ordering = ('nom',)


class ProduitAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation', 'categorie', 'quantite_stock', 'prix_achat', 'prix_vente', 'statut_stock')
    list_filter = ('categorie', 'fournisseur')
    search_fields = ('code', 'designation', 'description')
    list_editable = ('prix_achat', 'prix_vente', 'quantite_stock')
    readonly_fields = ('statut_stock', 'date_creation', 'date_mise_a_jour')
    fieldsets = (
        (None, {
            'fields': ('code', 'designation', 'description', 'categorie', 'fournisseur')
        }),
        (_('Prix et stock'), {
            'fields': ('prix_achat', 'prix_vente', 'quantite_stock', 'seuil_alerte')
        }),
        (_('Métadonnées'), {
            'fields': ('photo', 'date_creation', 'date_mise_a_jour', 'statut_stock')
        }),
    )


class EntreeStockAdmin(admin.ModelAdmin):
    list_display = ('produit', 'quantite', 'prix_unitaire', 'montant_total', 'date', 'utilisateur', 'fournisseur')
    list_filter = ('date', 'fournisseur', 'utilisateur')
    search_fields = ('produit__designation', 'reference', 'notes')
    readonly_fields = ('montant_total', 'date')
    raw_id_fields = ('produit', 'fournisseur', 'utilisateur')
    date_hierarchy = 'date'


class SortieStockAdmin(admin.ModelAdmin):
    list_display = ('produit', 'quantite', 'prix_unitaire', 'montant_total', 'date', 'utilisateur', 'client')
    list_filter = ('date', 'utilisateur')
    search_fields = ('produit__designation', 'reference', 'client', 'notes')
    readonly_fields = ('montant_total', 'date')
    raw_id_fields = ('produit', 'utilisateur')
    date_hierarchy = 'date'


# Enregistrement des modèles dans l'administration
admin.site.register(Categorie, CategorieAdmin)
admin.site.register(Fournisseur, FournisseurAdmin)
admin.site.register(Produit, ProduitAdmin)
admin.site.register(EntreeStock, EntreeStockAdmin)
admin.site.register(SortieStock, SortieStockAdmin)
