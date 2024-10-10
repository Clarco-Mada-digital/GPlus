# Register your models here.
from django.contrib import admin
from .models import Employee, Poste, Departement, Conge, Competence, Paie


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'date_naissance', 'type_salarie', 'statut_matrimonial')
    search_fields = ('nom', 'prenom', 'email')
    list_filter = ('ville', 'poste', 'type_salarie', 'statut')
    ordering = ['nom']

@admin.register(Paie)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'employee', 'mois', 'salaire_net',  'statut')
    search_fields = ('employee__nom', 'employee__prenom')

class PosteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'departement')  # Affiche les champs dans la liste
    search_fields = ('nom',)  # Ajoute une barre de recherche pour le champ 'nom'
    list_filter = ('departement',)  # Ajoute un filtre pour le champ 'departement'
    ordering = ('nom', )  # Trie les objets par le champ 'nom' par défaut
admin.site.register(Poste, PosteAdmin)

class DepartementAdmin(admin.ModelAdmin):
    search_fields = ('departement',)  # Ajoute une barre de recherche pour le champ 'nom'
admin.site.register(Departement, DepartementAdmin)

class CongeAdmin(admin.ModelAdmin):
    list_display = ('employee', 'type_conge', 'date_debut', 'date_fin', 'statut')  # Affiche les champs dans la liste
    search_fields = ('type_conge', 'statut')  # Ajoute une barre de recherche pour le champ 'nom'
    list_filter = ('type_conge',) # Ajoute un filtre pour le champ departement
    ordering = ('statut',)  # Trie les objets par le champ 'nom' par défaut
admin.site.register(Conge, CongeAdmin)

class CompetenceAdmin(admin.ModelAdmin):
    search_fields = ('nom',)  # Ajoute une barre de recherche pour le champ 'nom'
admin.site.register(Competence, CompetenceAdmin)