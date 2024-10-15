from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required  # Ajout du décorateur pour restreindre l'accès
def index(request):
    return render(request, "caisse/dashboard.html")

@login_required
def operations(request):
    return render(request, "caisse/operations/entre-sortie.html")  # Créez ce fichier HTML

@login_required
def listes(request):
    return render(request, "caisse/listes/listes_operations.html")  # Créez ce fichier HTML

@login_required
def depenses(request):
    return render(request, "caisse/depenses/depense.html")  # Créez ce fichier HTML

@login_required
def acteurs(request):
    return render(request, "caisse/acteurs/acteurs.html")  # Créez ce fichier HTML
