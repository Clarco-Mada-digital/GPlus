import re
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from .forms import ClientForm
from .models import Client
import json

# Create your views here.
def index(request):
  clients = Client.objects.all()
  count_prospect = Client.objects.filter(type_client='Prospect').count()
  count_client = Client.objects.filter(type_client='Client').count()
  count_fourniseur = Client.objects.filter(type_client='Fourniseur').count()
  print([client for client in clients])
  context = {
    "clients_list" : clients,
    "count_prospect": count_prospect,
    "count_client": count_client,
    "count_fourniseur": count_fourniseur,
  }
  return render(request, "client_pages/index.html", context)

# @login_required
# defrelient(request):
  clients = Client.objects.all()
  context = {
    "clients_list" : clients
  }
  return render(request, "client_pages/client.html", context)


@require_POST
@csrf_exempt
def new_client(request):
    if request.method == 'POST':
      start_times = {}
      form = ClientForm(request.POST, request.FILES)
      for key, value in request.POST.items():
        if key.startswith('start-time-'):
          # Extraire l'identifiant du jour à partir de la clé
          day_id = key.split('start-time-')[1]  # Récupère la partie après 'start-time-'
          start_times[day_id] = value  # Ajoute au dictionnaire
      print("Form data:", request.POST)  # Affiche les données reçues
      print("Form errors:", form.errors)  # Affiche les erreurs de validation      
      
      if form.is_valid():
          try:
              client = form.save(commit=False)
              client.disponibilite = start_times
              client.save()
              messages.success(request, "Client ajouté avec succès.")
              return redirect('client:client')
          except Exception as e:
              print("Erreur lors de l'enregistrement:", str(e))
              messages.error(request, f"Erreur lors de l'enregistrement: {str(e)}")
      else:
          print("Erreurs de validation:", form.errors)
          error_messages = []
          for field, errors in form.errors.items():
              error_messages.append(f"{field}: {', '.join(errors)}")
          messages.error(request, "Erreurs dans le formulaire: " + " | ".join(error_messages))
            
    return redirect('client:client')

@login_required
@require_POST
@csrf_exempt
def edit_client(request, pk):
  try:
    client = get_object_or_404(Client, pk=pk)
    data = json.loads(request.body)
    
    # Valider les données avant la mise à jour
    form = ClientForm(data, instance=client)
    if form.is_valid():
      # Mise à jour des champs du client
      for key, value in data.items():
          if hasattr(client, key):
              setattr(client, key, value)
      
      client.save()
      messages.success(request, f"Le client '{client.name}' a été modifié avec succès.")
    else:
      error_messages = []
      for field, errors in form.errors.items():
          error_messages.append(f"{field}: {', '.join(errors)}")
      messages.error(request, "Erreurs dans le formulaire: " + " | ".join(error_messages))
          
  except json.JSONDecodeError:
    messages.error(request, "Données JSON invalides")
  except Exception as e:
    messages.error(request, f"Erreur lors de la modification: {str(e)}")
      
  return redirect('client:client')  

  
@login_required
@csrf_exempt
def supprimer_client(request, pk):
  try:
    client = get_object_or_404(Client, pk=pk)
    nom_client = client.name # Sauvegarde le nom avant suppression
    client.delete()
    messages.success(request, f"Le client '{nom_client}' a été supprimé avec succès.")
    return redirect('client:client')
  except Exception as e:
    messages.error(request, f"Erreur lors de la suppression du client: {str(e)}")
    return redirect('client:client')

@login_required
def client_list(request):
    # Récupérer le type de client et le terme de recherche depuis l'URL
    type_client = request.GET.get('type')
    search_query = request.GET.get('search', '')
    
    # Commencer avec tous les clients
    clients = Client.objects.all()
    
    # Filtrer par type si spécifié
    if type_client:
        clients = clients.filter(type_client=type_client)
        
    # Filtrer par terme de recherche si présent
    if search_query:      
      clients = clients.filter(
          Q(name__icontains=search_query) |
          Q(commercial_name__icontains=search_query) |
          Q(email__icontains=search_query) |
          Q(tel__icontains=search_query)
      )
    # Statistiques pour la navigation
    types_clients = Client.objects.values_list('type_client', flat=True).distinct()
    stats_clients = {
        'total': Client.objects.count(),
        'types': {}
    }
    
    for type_client in types_clients:
        count = Client.objects.filter(type_client=type_client).count()
        stats_clients['types'][type_client] = count

    context = {
        'clients_list': clients,
        'stats_clients': stats_clients,
        'search_query': search_query,  # Pour conserver la valeur dans le formulaire
    }
    return render(request, 'client_pages/client.html', context)