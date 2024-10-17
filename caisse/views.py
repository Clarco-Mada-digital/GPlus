from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Categorie, Fournisseur, Beneficiaire, OperationEntrer, OperationSortir
from datetime import datetime
#from django.contrib.messages import Message

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
    return render(request, "caisse/acteurs/acteurs.html")  # Créez ce fichier HTML

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