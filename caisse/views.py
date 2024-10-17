from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers import serialize
import json
from .models import Categorie, Personnel, Fournisseur, OperationEntrer
from .forms import FournisseurForm, PersonnelForm, CategorieForm

# Vues principales

@login_required
def index(request):
    """
    Affiche le tableau de bord principal.
    """
    return render(request, "caisse/dashboard.html")

@login_required
def operations(request):
    """
    Affiche la page des opérations.
    """
    return render(request, "caisse/operations/entre-sortie.html")

@login_required
def categories(request):
    """
    Affiche la liste des catégories.
    """
    categories = Categorie.objects.all()
    categories_json = json.loads(serialize('json', categories))
    
    context = {
        'categories': json.dumps([{**item['fields'], 'id': item['pk']} for item in categories_json]),
    }
    return render(request, "caisse/categories/categories.html", context)

@login_required
def listes(request):
    """
    Affiche la liste des opérations.
    """
    return render(request, "caisse/listes/listes_operations.html")

@login_required
def depenses(request):
    """
    Affiche la page des dépenses.
    """
    return render(request, "caisse/depenses/depense.html")

# Gestion des acteurs

@login_required
def acteurs(request):
    """
    Affiche la page des acteurs (personnels, fournisseurs, catégories).
    """
    personnels = Personnel.objects.all()
    fournisseurs = Fournisseur.objects.all()
    categories = Categorie.objects.all()
    
    personnels_json = json.loads(serialize('json', personnels))
    fournisseurs_json = json.loads(serialize('json', fournisseurs))
    categories_entrees = json.loads(serialize('json', categories.filter(type='entree')))
    categories_sorties = json.loads(serialize('json', categories.filter(type='sortie')))
    
    context = {
        'personnels': json.dumps([{**item['fields'], 'id': item['pk']} for item in personnels_json]),
        'fournisseurs': json.dumps([{**item['fields'], 'id': item['pk']} for item in fournisseurs_json]),
        'categories_entrees': json.dumps([{**item['fields'], 'id': item['pk']} for item in categories_entrees]),
        'categories_sorties': json.dumps([{**item['fields'], 'id': item['pk']} for item in categories_sorties]),
    }
    return render(request, "caisse/acteurs/acteurs.html", context)

@login_required
def ajouter_acteur(request):
    """
    Ajoute un nouvel acteur (fournisseur, employé ou catégorie).
    """
    if request.method == 'POST':
        type_acteur = request.POST.get('type_acteur')
        if type_acteur == 'fournisseurs':
            form = FournisseurForm(request.POST)
        elif type_acteur == 'employes':
            form = PersonnelForm(request.POST, request.FILES)
        elif type_acteur == 'categories':
            form = CategorieForm(request.POST)
        else:
            messages.error(request, "Type d'acteur non valide.")
            return redirect('acteurs')

        if form.is_valid():
            form.save()
            messages.success(request, f"{type_acteur[:-1].capitalize()} ajouté avec succès.")
            return render(request, 'caisse/acteurs/acteurs.html')
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez vérifier les données.")
    return redirect('acteurs')

@login_required
def ajouter_fournisseur(request):
    """
    Ajoute un nouveau fournisseur.
    """
    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fournisseur ajouté avec succès.")
            return render(request, 'caisse/acteurs/acteurs.html')
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez vérifier les données.")
    return redirect('acteurs')

@login_required
def modifier_acteur(request, type_acteur, pk):
    """
    Modifie un acteur existant (fournisseur, personnel ou catégorie).
    """
    if type_acteur == 'fournisseurs':
        acteur = get_object_or_404(Fournisseur, pk=pk)
        form_class = FournisseurForm
    elif type_acteur == 'personnels':
        acteur = get_object_or_404(Personnel, pk=pk)
        form_class = PersonnelForm
    elif type_acteur == 'categories':
        acteur = get_object_or_404(Categorie, pk=pk)
        form_class = CategorieForm
    else:
        messages.error(request, "Type d'acteur non valide.")
        return redirect('acteurs')

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=acteur)
        if form.is_valid():
            form.save()
            messages.success(request, f"{type_acteur[:-1].capitalize()} modifié avec succès.")
            return redirect('acteurs')
    else:
        form = form_class(instance=acteur)
    
    context = {
        'form': form,
        'type_acteur': type_acteur,
        'acteur': acteur,
    }
    return render(request, 'caisse/acteurs/modifier_acteur.html', context)

@login_required
def supprimer_acteur(request, type_acteur, pk):
    """
    Supprime un acteur existant (fournisseur, personnel ou catégorie).
    """
    if type_acteur == 'fournisseurs':
        acteur = get_object_or_404(Fournisseur, pk=pk)
    elif type_acteur == 'personnels':
        acteur = get_object_or_404(Personnel, pk=pk)
    elif type_acteur == 'categories':
        acteur = get_object_or_404(Categorie, pk=pk)
    else:
        messages.error(request, "Type d'acteur non valide.")
        return redirect('acteurs')

    if request.method == 'POST':
        acteur.delete()
        messages.success(request, f"{type_acteur[:-1].capitalize()} supprimé avec succès.")
    return redirect('acteurs')

# Gestion des catégories

@login_required
def ajouter_categorie(request):
    """
    Ajoute une nouvelle catégorie.
    """
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect('acteurs')
    return redirect('acteurs')

@login_required
def modifier_categorie(request, pk):
    """
    Modifie une catégorie existante.
    """
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie modifiée avec succès.")
            return redirect('acteurs')
    else:
        form = CategorieForm(instance=categorie)
    return render(request, 'caisse/acteurs/modifier_categorie.html', {'form': form})

@login_required
def supprimer_categorie(request, pk):
    """
    Supprime une catégorie existante.
    """
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        categorie.delete()
        messages.success(request, "Catégorie supprimée avec succès.")
    return redirect('acteurs')

# Gestion des opérations

@login_required
def ajouts_entree(request):
    """
    Gère l'ajout d'opérations d'entrée.
    """
    categories = Categorie.objects.all()
    
    if request.method == 'POST':
        if 'date' in request.POST:
            lignes_entrees = []
            for i in range(len(request.POST.getlist('date'))):
                date_operation = request.POST.getlist('date')[i]
                designation = request.POST.getlist('désignation')[i]
                montant = request.POST.getlist('montant')[i]
                categorie_id = request.POST.getlist('categorie')[i]

                try:
                    montant = float(montant)
                    categorie = Categorie.objects.get(id=categorie_id)

                    operation_entree = OperationEntrer(
                        date_transaction=date_operation,
                        description=designation,
                        montant=montant,
                        categorie=categorie
                    )
                    operation_entree.save()
                    lignes_entrees.append(operation_entree)
                except (ValueError, Categorie.DoesNotExist):
                    return render(request, 'caisse/operations/entre-sortie.html', {'error': 'Données invalides', 'categories': categories})
                
            return redirect('listes')

    return render(request, 'caisse/operations/entre-sortie.html', {'categories': categories})