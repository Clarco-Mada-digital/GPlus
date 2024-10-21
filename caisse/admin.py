from django.contrib import admin
from .models import Beneficiaire, Personnel, Fournisseur, OperationSortir, Categorie

# Register your models here.


admin.site.register(Personnel)
admin.site.register(Fournisseur)
admin.site.register(Beneficiaire)
admin.site.register(OperationSortir)
admin.site.register(Categorie)