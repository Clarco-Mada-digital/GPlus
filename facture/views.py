from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from clients.models import Client
from .models import Service, Facture
from .forms import FactureForm, ServiceForm
import json

# Create your views here.

def index(request):
  today = timezone.now()
  years = range(today.year - 5, today.year + 1)
  
  context = {
    'years' : years,
  }
  return render(request, "facture_pages/index.html", context)


def facture(request):
  clients = Client.objects.all()
  services = Service.objects.all()
  services_list = list(services.values('nom_service', 'prix_unitaire'))
  for service in services_list:
      service['prix_unitaire'] = float(service['prix_unitaire'])  # Conversion
  context = {
    "clients_list" : clients,
    "services_list" : services,
    "services_json" : json.dumps(services_list)
  }
  return render(request, "facture_pages/facture.html", context)

@login_required
def ajouter_facture(request):
  """
  Vue pour l'ajout d'une nouvelle facture.
  
  Si la méthode de requête est POST, on valide le formulaire et on l'enregistre en base de données.
  Sinon, on affiche le formulaire vide.
  
  :param request: La requête HTTP
  :return: La page de création de facture avec le formulaire et un message de succès ou d'erreur si applicable
  """
  if request.method == 'POST':
    form = FactureForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, "Facture ajoutée avec succès.")
      return render(request, "facture_pages/facture.html")
    else:
      messages.error(request, "Erreur lors de l'ajout de la facture. Veuillez vérifier les informations entrées.")
  else:
    # form = FactureForm()
    return redirect(request, 'facture:facture')

@login_required
def modifier_facture(request, pk):
  """
  Vue pour la modification d'une facture.
  
  Si la méthode de requête est POST, on valide le formulaire et on l'enregistre en base de données.
  Sinon, on affiche le formulaire pré-rempli.
  
  :param request: La requête HTTP
  :param pk: La clé primaire de la facture à modifier
  :return: La page de modification de facture avec le formulaire pré-rempli et un message de succès si applicable
  """
  facture = get_object_or_404(Facture, pk=pk)
  if request.method == 'POST':
    form = FactureForm(request.POST, instance=facture)
    if form.is_valid():
      form.save()
      return render(request, "facture_pages/modifier_facture.html", {"message": "Facture modifiée avec succès."})
  else:
    form = FactureForm(instance=facture)
  return render(request, "facture_pages/modifier_facture.html", {"form": form})

@login_required
def supprimer_facture(request, pk):
  """
  Vue pour la suppression d'une facture.
  
  Si la méthode de requête est POST, on supprime la facture de la base de données.
  Sinon, on affiche la page de confirmation de suppression.
  
  :param request: La requête HTTP
  :param pk: La clé primaire de la facture à supprimer
  :return: La page de confirmation de suppression ou un message de succès si applicable
  """
  facture = get_object_or_404(Facture, pk=pk)
  if request.method == 'POST':
    facture.delete()
    return render(request, "facture_pages/supprimer_facture.html", {"message": "Facture supprimée avec succès."})
  else:
    return render(request, "facture_pages/supprimer_facture.html", {"facture": facture})



def ajouter_service(request):
  """
  Vue pour l'ajout d'un nouvel article.
  
  Si la méthode de requête est POST, on valide le formulaire et on l'enregistre en base de données.
  Sinon, on affiche le formulaire vide.
  
  :param request: La requête HTTP
  :return: La page de création d'article avec le formulaire et un message de succès ou d'erreur si applicable
  """
  if request.method == 'POST':
    form = ServiceForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, "Service ajouté avec succès.")
      return redirect('facture:facture')
    else:
      messages.error(request, "Erreur lors de l'ajout de l'article. Veuillez vérifier les informations entrées.")
  else:
    return redirect('facture:facture')

@login_required
def modifier_article(request, pk):
  """
  Vue pour la modification d'un article.
  
  Si la méthode de requête est POST, on valide le formulaire et on l'enregistre en base de données.
  Sinon, on affiche le formulaire pré-rempli.
  
  :param request: La requête HTTP
  :param pk: La clé primaire de l'article à modifier
  :return: La page de modification d'article avec le formulaire pré-rempli et un message de succès si applicable
  """
  article = get_object_or_404(Service, pk=pk)
  if request.method == 'POST':
    form = ServiceForm(request.POST, instance=article)
    if form.is_valid():
      form.save()
      return render(request, "facture_pages/modifier_article.html", {"message": "Article modifié avec succès."})
  else:
    form = ServiceForm(instance=article)
  return render(request, "facture_pages/modifier_article.html", {"form": form})

@login_required
def supprimer_article(request, pk):
  """
  Vue pour la suppression d'un article.
  
  Si la méthode de requête est POST, on supprime l'article de la base de données.
  Sinon, on affiche la page de confirmation de suppression.
  
  :param request: La requête HTTP
  :param pk: La clé primaire de l'article à supprimer
  :return: La page de confirmation de suppression de l'article
  """
  article = get_object_or_404(Service, pk=pk)
  if request.method == 'POST':
    article.delete()
    return render(request, "facture_pages/supprimer_article.html", {"message": "Article supprimé avec succès."})
  return render(request, "facture_pages/supprimer_article.html", {"article": article})
