from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required  # Ajout du décorateur pour restreindre l'accès
def index(request):
    return render(request, "caisse/dashboard.html")

@login_required
def listes(request):
    return render(request, "caisse/listes/listes_operations.html")  # Créez ce fichier HTML

@login_required
def depenses(request):
    return render(request, "caisse/depenses/depense.html")  # Créez ce fichier HTML

@login_required
def acteurs(request):
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

@login_required
def ajouter_categorie(request):
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect('acteurs')
    return redirect('acteurs')

@login_required
def modifier_categorie(request, pk):
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
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        categorie.delete()
        messages.success(request, "Catégorie supprimée avec succès.")
    return redirect('acteurs')

@login_required
def ajouts_entree(request):
    categories = Categorie.objects.all()  # Récupérer toutes les catégories
    
    if request.method == 'POST':
        if 'date' in request.POST:  # Vérifier si c'est une opération d'entrée
            lignes_entrees = []
            for i in range(len(request.POST.getlist('date'))):  # Itérer sur les lignes d'entrée
                date_operation = request.POST.getlist('date')[i]
                designation = request.POST.getlist('désignation')[i]
                montant = request.POST.getlist('montant')[i]
                categorie_id = request.POST.getlist('categorie')[i]

                try:
                    montant = float(montant)
                    categorie = Categorie.objects.get(id=categorie_id) # Récupérer l'objet Categorie

                    operation_entree = OperationEntrer(
                        date_transaction=date_operation,
                        description=designation,
                        montant=montant,
                        categorie=categorie # Assigner l'objet Categorie
                    )
                    operation_entree.save()
                    lignes_entrees.append(operation_entree)  # Ajouter l'objet à la liste pour un traitement ultérieur si nécessaire
                except (ValueError, Categorie.DoesNotExist):
                    # Gérer les erreurs de conversion de montant ou si la catégorie n'existe pas
                    return render(request, 'caisse/operations/entre-sortie.html', {'error': 'Données invalides', 'categories': categories})
                
            # Rediriger ou afficher un message de succès
            return redirect('listes')

        # Gestion des sorties (à implémenter de manière similaire aux entrées)
        # ...


    return render(request, 'caisse/operations/entre-sortie.html', {'categories': categories})  # Passer les catégories au contexte du template