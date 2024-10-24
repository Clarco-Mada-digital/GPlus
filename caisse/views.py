from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers import serialize
from django.db import models  # Ajoutez cette ligne
import json
from .models import Categorie, Personnel, Fournisseur, OperationEntrer, OperationSortir, Beneficiaire
from .forms import FournisseurForm, PersonnelForm, CategorieForm
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from django.db.models.functions import TruncYear
from django.db.models import Q

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
    categories = Categorie.objects.all()
    categories_entree = Categorie.objects.filter(type='entree')
    categories_sortie = Categorie.objects.filter(type='sortie')
    beneficiaires = Beneficiaire.objects.all()
    fournisseurs = Fournisseur.objects.all()

    return render(request, "caisse/operations/entre-sortie.html", {
        'categories': categories,
        'categories_entree': categories_entree,
        'categories_sortie': categories_sortie,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        })

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
    """Affiche la liste des opérations."""

    entree = OperationEntrer.objects.all()
    sortie = OperationSortir.objects.select_related('beneficiaire', 'fournisseur', 'categorie').all()
    categories = Categorie.objects.all()
    beneficiaires = Beneficiaire.objects.all()
    fournisseurs = Fournisseur.objects.all()
    sort_by = request.GET.get('sort', 'date')

    # Dictionnaire pour stocker les filtres
    filters = {}

    # Gestion des filtres (simplifiée et plus robuste)
    for field in ['categorie', 'beneficiaire', 'fournisseur', 'sort']:
        value = request.GET.get(field)
        if value:
            filters[field] = value

    for field in ['montant_min', 'montant_max', 'quantite_min', 'quantite_max']:
        value = request.GET.get(field)
        if value:
            try:
                filters[field] = float(value)  # Conversion en nombre
            except ValueError:
                # Gérer l'erreur, par exemple afficher un message à l'utilisateur
                # ou simplement ignorer la valeur invalide.
                pass

    for field in ['date_min', 'date_max']:
         value = request.GET.get(field)
         if value:
             filters[field] = value


    query = request.GET.get('q')
    if query:
       filters['query'] = query


    # Application des filtres
    if filters:
        if 'query' in filters:
            entree = entree.filter(
                Q(description__icontains=filters['query']) |
                Q(categorie__name__icontains=filters['query']) |
                Q(montant__icontains=filters['query']) |
                Q(date__icontains=filters['query'])
            )
            sortie = sortie.filter(
                Q(description__icontains=filters['query']) |
                Q(categorie__name__icontains=filters['query']) |
                Q(montant__icontains=filters['query']) |
                Q(date__icontains=filters['query'])
            )

        if 'categorie' in filters:
            entree = entree.filter(categorie_id=filters['categorie'])
            sortie = sortie.filter(categorie_id=filters['categorie'])

        if 'beneficiaire' in filters:
            sortie = sortie.filter(beneficiaire_id=filters['beneficiaire'])

        if 'fournisseur' in filters:
            sortie = sortie.filter(fournisseur_id=filters['fournisseur'])
        
        if 'montant_min' in filters:
             entree = entree.filter(montant__gte=filters['montant_min'])
             sortie = sortie.filter(montant__gte=filters['montant_min'])

        if 'montant_max' in filters:
             entree = entree.filter(montant__lte=filters['montant_max'])
             sortie = sortie.filter(montant__lte=filters['montant_max'])

        if 'quantite_min' in filters:
             sortie = sortie.filter(quantité__gte=filters['quantite_min'])
        if 'quantite_max' in filters:
             sortie = sortie.filter(quantité__lte=filters['quantite_max'])


        if 'date_min' in filters:
             entree = entree.filter(date__gte=filters['date_min'])
             sortie = sortie.filter(date__gte=filters['date_min'])

        if 'date_max' in filters:
             entree = entree.filter(date__lte=filters['date_max'])
             sortie = sortie.filter(date__lte=filters['date_max'])
        

    # Filtrer les opérations de sortie qui ont des bénéficiaires valides
    sortie = sortie.filter(Q(beneficiaire__isnull=False) | Q(beneficiaire__personnel__isnull=False) | Q(beneficiaire__name__isnull=False))

    # Tri
    entree = entree.order_by(sort_by)
    sortie = sortie.order_by(sort_by)
    print(entree)
    print(sortie)

    context = {
        'entree': entree,
        'sortie': sortie,
        'categories': categories,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        'prix': "Ar",  # Vous pouvez gérer 'Ar' dans le template
        'sort_by': sort_by,
    }

    return render(request, "caisse/listes/listes_operations.html", context)

@login_required
def depenses(request):
    """
    Affiche la page des dépenses avec les opérations par employé et par catégorie.
    """
    # Filtrage par date
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    mois_selectionne = request.GET.get('mois', 'Août 2024')  # Valeur par défaut

    operations = OperationSortir.objects.all()
    if date_debut:
        operations = operations.filter(date_de_sortie__gte=date_debut)
    if date_fin:
        operations = operations.filter(date_de_sortie__lte=date_fin)

    # Dépenses par employé
    depenses_par_employe = operations.values(
        'beneficiaire__personnel__first_name', 
        'beneficiaire__personnel__last_name'
    ).annotate(
        total_depenses=Sum('montant'),
        nombre_depenses=Count('id'),
        categorie_plus_depensee=models.F('categorie__name')
    ).order_by('-total_depenses')

    # Dépenses par catégorie
    depenses_par_categorie = operations.values(
        'categorie__name'
    ).annotate(
        total_depenses=Sum('montant'),
        nombre_depenses=Count('id')
    ).order_by('-total_depenses')

    # Dépenses par année
    depenses_par_annee = operations.annotate(
        year=TruncYear('date_de_sortie')
    ).values('year').annotate(
        total_depenses=Sum('montant')
    ).order_by('year')

    context = {
        'depenses_par_employe': depenses_par_employe,
        'depenses_par_categorie': depenses_par_categorie,
        'depenses_par_annee': depenses_par_annee,
        'mois_selectionne': mois_selectionne,
    }
    return render(request, "caisse/depenses/depense.html", context)

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
            return redirect('acteurs')
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
            return redirect('acteurs')
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
        messages.success(request, "Cat��gorie supprimée avec succès.")
    return redirect('acteurs')

# Gestion des opérations

@login_required
def ajouts_entree(request):
    """
    Gère l'ajout d'opérations d'entrée.
    """
    categories_entree = Categorie.objects.filter(type='entree')
    
    if request.method == 'POST' and 'date' in request.POST:
        lignes_entrees = []
        for i in range(len(request.POST.getlist('date'))):
            date_operation = request.POST.getlist('date')[i]
            designation = request.POST.getlist('designation')[i]
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
                return render(request, 'caisse/operations/entre-sortie.html', {'error': 'Données invalides', 'categories_entree': categories_entree})
            
        return redirect('listes')

    return render(request, 'caisse/operations/entre-sortie.html', {'categories_entree': categories_entree, 'operation': 'entree',})

@login_required
def ajouts_sortie(request):
    """
    Gère l'ajout d'opérations de sortie.
    """
    categories_sortie = Categorie.objects.filter(type='sortie') 
    beneficiaires = Beneficiaire.objects.all()
    fournisseurs = Fournisseur.objects.all()

    if request.method == 'POST':
        # Récupérer les données envoyées depuis le formulaire.
        # Utiliser getlist pour gérer les listes de valeurs.
        dates = request.POST.getlist('date')
        designations = request.POST.getlist('designation')
        beneficiaires_ids = request.POST.getlist('beneficiaire')
        fournisseurs_ids = request.POST.getlist('fournisseur')
        quantites = request.POST.getlist('quantite')
        prix_unitaires = request.POST.getlist('prixUnitaire')
        categories_ids = request.POST.getlist('categorie')
        prix_total = request.POST.getlist('prixTotal')
        for i in range(len(dates)):
            try:
                # Conversion explicite en types appropriés
                date_operation = dates[i]
                designation = designations[i]
                beneficiaire_id = int(beneficiaires_ids[i])  # Conversion en entier
                fournisseur_id = int(fournisseurs_ids[i])  # Conversion en entier
                quantite = int(quantites[i])
                prix_unitaire = float(prix_unitaires[i])
                categorie_id = int(categories_ids[i])      # Conversion en entier
                prix_total = float(prix_total[i])


                # Récupérer les objets ForeignKey en utilisant .get() et gérer les exceptions
                categorie = Categorie.objects.get(pk=categorie_id)
                beneficiaire = Beneficiaire.objects.get(pk=beneficiaire_id)
                fournisseur = Fournisseur.objects.get(pk=fournisseur_id)

                # Calculer le montant total
                montant_total = quantite * prix_unitaire

                # Créer une nouvelle opération de sortie
                operation_sortie = OperationSortir(
                    date_de_sortie=date_operation,
                    description=designation,
                    beneficiaire=beneficiaire,
                    fournisseur=fournisseur,
                    quantité=quantite,
                    montant=montant_total, # Utiliser le montant total calculé
                    categorie=categorie
                )
                operation_sortie.save()

            except (ValueError, Categorie.DoesNotExist, Beneficiaire.DoesNotExist, Fournisseur.DoesNotExist) as e:
                # Gérer les erreurs plus précisément : afficher le type d'erreur et l'index de la ligne problématique
                return render(request, 'caisse/operations/entre-sortie.html', {
                    'error': f"Erreur à la ligne {i+1} : {type(e).__name__} - {e}",
                    'categories_sortie': categories_sortie,
                    'beneficiaires': beneficiaires,
                    'fournisseurs': fournisseurs,
                })
        return redirect('listes') # Rediriger après un traitement réussi

    return render(request, 'caisse/operations/entre-sortie.html', {
        'categories_sortie': categories_sortie,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        'operation': 'sortie',
    })

@login_required
def modifier_operation(request, pk):
    operation = get_object_or_404(OperationSortir, pk=pk)
    if request.method == 'POST':
        # Logique de modification de l'opération
        # Utilisez un formulaire approprié ici
        messages.success(request, "Opération modifiée avec succès.")
        return redirect('depenses')
    # Afficher le formulaire de modification
    return render(request, 'caisse/operations/modifier_operation.html', {'operation': operation})

@login_required
def supprimer_operation(request, pk):
    operation = get_object_or_404(OperationSortir, pk=pk)
    if request.method == 'POST':
        operation.delete()
        messages.success(request, "Opération supprimée avec succès.")
    return redirect('depenses')

