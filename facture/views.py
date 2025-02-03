from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from clients.models import Client
from .models import Service, Facture
from .forms import FactureForm, ServiceForm
from xhtml2pdf import pisa
import json
import uuid

# Create your views here.
@login_required(login_url="accounts:login_user")
def index(request):
  today = timezone.now()
  mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

  # Récupération du filtre depuis le front
  fact_annee_filtre = request.GET.get('fact_annee', 0)
  fact_mois_filtre = request.GET.get('fact_mois', 0)
  fact_search = request.GET.get('fact_search', "")
  dev_annee_filtre = request.GET.get('dev_annee', 0)
  dev_mois_filtre = request.GET.get('dev_mois', 0)
  dev_search = request.GET.get('dev_search', "")

  # Filtrage des factures en fonction du filtre sélectionné
  all_facture = Facture.objects.all()

  factures = all_facture.filter(type="Facture")
  devis = all_facture.filter(type="Devis")  

  mois_uniques = {facture.date_facture.month for facture in factures}
  mois_uniques = sorted(mois_uniques, reverse=True)
  mois_filtrable = [{"id": i, "nom": mois[i-1]} for i in mois_uniques]

  # Pour devis
  dev_mois_uniques = {dev.date_facture.month for dev in devis}
  dev_mois_uniques = sorted(dev_mois_uniques, reverse=True)
  dev_mois_filtrable = [{"id": i, "nom": mois[i-1]} for i in dev_mois_uniques]

  annee_uniques = {facture.date_facture.year for facture in factures}
  annee_uniques = sorted(annee_uniques, reverse=True)
  annee_filtrable = [{"id": i, "nom": i} for i in annee_uniques]

  # Pour devis
  dev_annee_uniques = {dev.date_facture.year for dev in devis}
  dev_annee_uniques = sorted(dev_annee_uniques, reverse=True)
  dev_annee_filtrable = [{"id": i, "nom": i} for i in dev_annee_uniques]

  # Facture filter
  if fact_annee_filtre:
    factures = factures.filter(date_facture__year=fact_annee_filtre, type="Facture")
  if fact_mois_filtre:
    factures = factures.filter(date_facture__month=int(fact_mois_filtre), type="Facture")
  if fact_search:
    factures = factures.filter(intitule__contains=fact_search, type="Facture")
  # Devis filter
  if dev_annee_filtre:
    devis = devis.filter(date_facture__year=dev_annee_filtre, type="Devis")
  if dev_mois_filtre:
    devis = devis.filter(date_facture__month=int(dev_mois_filtre), type="Devis")
  if dev_search:
    devis = devis.filter(intitule__contains=dev_search, type="Devis")
    
  
  paginator_fact = Paginator(factures, 10) # Afficher les resultat par 10
  paginator_dev = Paginator(devis, 10) # Afficher les resultat par 10
  page_facture = request.GET.get('page_facture')
  factures = paginator_fact.get_page(page_facture)
  page_dev = request.GET.get('page_dev')
  devis = paginator_dev.get_page(page_dev)

  context = {
    'factures' : factures,
    'devis' : devis,
    'fact_mois_filtrable': mois_filtrable,
    'dev_mois_filtrable': dev_mois_filtrable,
    'fact_annee_filtrable': annee_filtrable,
    'dev_annee_filtrable': dev_annee_filtrable,
    'annee_filtre': int(fact_annee_filtre),
    'mois_filtre': int(fact_mois_filtre),
    # Pour affichage dans le filtre
    'dev_mois_filtre': int(dev_mois_filtre),
    "dev_annee_filtre": int(dev_annee_filtre),
    "fact_search":fact_search,
    "dev_search":dev_search
  }
  return render(request, "facture_pages/index.html", context)

@login_required(login_url="accounts:login_user")
def get_on_facture(request):  # sourcery skip: avoid-builtin-shadow
  """
  Récupère une facture spécifique.

  Cette fonction récupère une facture en fonction de son ID.

  :param request: La requête HTTP.
  :param id: L'ID de la facture à récupérer.
  :return: Le rendu de la page avec le contexte de la facture.
  """
  # Récupérer l'ID de la facture depuis les paramètres GET
  id = request.GET.get('id')

  # Vérifier si l'ID est fourni et est un entier
  if id is None or not id.isdigit():
      return JsonResponse({'error': 'ID de facture invalide.'}, status=400)

  # Récupérer la facture ou renvoyer une erreur 404 si elle n'existe pas
  facture = get_object_or_404(Facture, pk=id)

  # Retourner les détails de la facture sous forme de JSON
  return JsonResponse({
      'id': facture.id,
      'client_comercial_name': facture.client.commercial_name,
      'client_address': facture.client.adresse,
      'client_code_postal': '2343',
      'client_ville': 'Paris',
      'client_name': facture.client.name,
      'client_email': facture.client.email,
      'client_desc_facture': facture.client.description_facture,
      'facture_ref': facture.ref,
      'facture_intitule': facture.intitule,
      'facture_emission_date': facture.date_facture,
      'facture_reglement': facture.reglement,
      'facture_etat': facture.etat_facture,
      'facture_montant': facture.montant,
      'facture_condition': facture.condition,
      'facture_with_tva': facture.with_tva,
      'facture_services': json.dumps(list(facture.services.values())),
      # Ajoutez d'autres champs nécessaires ici
    })
  
@login_required(login_url="accounts:login_user")
def facture(request):
  client_id = request.GET.get('client_id')
  client = Client.objects.get(id=client_id) if client_id else None
  clients = Client.objects.all()
  services = Service.objects.all()
  services_list = list(services.values('id', 'nom_service', 'prix_unitaire', 'description'))
  for service in services_list:
      service['prix_unitaire'] = float(service['prix_unitaire'])  # Conversion
  context = {
    "clients_list" : clients,
    "services_list" : services,
    "services_json" : json.dumps(services_list),
    "client_selected" : client
  }
  return render(request, "facture_pages/facture.html", context)

@login_required(login_url="accounts:login_user")
def ajouter_facture(request):
  """
  Vue pour l'ajout d'une nouvelle facture.
  
  Si la méthode de requête est POST, on valide le formulaire et on l'enregistre en base de données.
  Sinon, on affiche le formulaire vide.
  
  :param request: La requête HTTP
  :return: La page de création de facture avec le formulaire et un message de succès ou d'erreur si applicable
  """
  if request.method != 'POST':
    return redirect('facture:facture')
  form = FactureForm(request.POST) 

  services_data = {}
  for key, value in request.POST.items():
      if key.startswith('description-'):
          service_id = key.split('description-')[1]
          services_data[service_id] = {'description': value, 'quantite': 0, 'prix': 0.0}
      elif key.startswith('quantite-'):
          service_id = key.split('quantite-')[1]
          if service_id in services_data:
              services_data[service_id]['quantite'] = int(value)
      elif key.startswith('prix-'):
          service_id = key.split('prix-')[1]
          if service_id in services_data:
              services_data[service_id]['prix'] = float(value)

  if form.is_valid():
    try:
      facture = form.save(commit=False)
      facture.services = services_data
      facture.created_by = request.user
      dernier_id = Facture.objects.latest('id').id if Facture.objects.exists() else 0
      if facture.etat_facture == 'Brouillon' and facture.type == 'Facture':
        facture.ref = (f'(FPROV{str(timezone.now().year)}-' +
                       str(dernier_id + 1).zfill(6) + ')')
      elif facture.etat_facture == 'Brouillon' and facture.type == 'Devis':
        facture.ref = (
            f'(DPROV{str(timezone.now().year)}-{str(dernier_id + 1).zfill(6)})'
        )
      elif facture.type == 'Facture':
        facture.ref = f'F{str(timezone.now().year)}-{str(dernier_id + 1).zfill(6)}'
      else:
        facture.ref = f'D{str(timezone.now().year)}-{str(dernier_id + 1).zfill(6)}'
      facture.save()
      messages.success(request, "Facture ajoutée avec succès.")
      return redirect('facture:facture')
    except Exception as e:
      print("Erreur lors de l'enregistrement:", e)
      messages.error(request, f"Erreur lors de l'enregistrement: {str(e)}")
      return redirect('facture:facture')
  else:
    print("Erreurs de validation:", form.errors)
    messages.error(request, "Erreur lors de l'ajout de la facture. Veuillez vérifier les informations entrées.")
    return redirect('facture:facture')

@login_required(login_url="accounts:login_user")
def ajouter_Devis(request):
  """
  Vue pour l'ajout d'une nouvelle facture.
  
  Si la méthode de requête est POST, on valide le formulaire et on l'enregistre en base de données.
  Sinon, on affiche le formulaire vide.
  
  :param request: La requête HTTP
  :return: La page de création de facture avec le formulaire et un message de succès ou d'erreur si applicable
  """
  if request.method != 'POST':
    return redirect('facture:facture')
  form = FactureForm(request.POST)
  services_data = {}
  for key, value in request.POST.items():
      if key.startswith('description-'):
          service_id = key.split('description-')[1]
          services_data[service_id] = {'description': value, 'quantite': 0, 'prix': 0.0}
      elif key.startswith('quantite-'):
          service_id = key.split('quantite-')[1]
          if service_id in services_data:
              services_data[service_id]['quantite'] = int(value)
      elif key.startswith('prix-'):
          service_id = key.split('prix-')[1]
          if service_id in services_data:
              services_data[service_id]['prix'] = float(value)

  if form.is_valid():
    try:
      facture = form.save(commit=False)
      facture.services = services_data
      facture.type = "Devis"
      facture.ref = (
          f'(FPROV{str(timezone.now().year)}-{str(uuid.uuid4().int)[:6].zfill(6)})'
          if facture.etat_facture == 'Brouillon' else
          f'F{str(timezone.now().year)}-{str(uuid.uuid4().int)[:6].zfill(6)}')
      facture.save()
      messages.success(request, "Facture ajoutée avec succès.")
      return redirect(request.META.get('HTTP_REFERER'))
    except Exception as e:
      print("Erreur lors de l'enregistrement:", e)
      messages.error(request, f"Erreur lors de l'enregistrement: {str(e)}")
  else:
    print("Erreurs de validation:", form.errors)
    messages.error(request, "Erreur lors de l'ajout de la facture. Veuillez vérifier les informations entrées.")
    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url="accounts:login_user")
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
    services_data = {}
    for key, value in request.POST.items():
      if key.startswith('description-'):
        service_id = key.split('description-')[1]
        services_data[service_id] = {'description': value, 'quantite': 0, 'prix': 0.0}
      elif key.startswith('quantite-'):
        service_id = key.split('quantite-')[1]
        if service_id in services_data:
          services_data[service_id]['quantite'] = int(value)
      elif key.startswith('prix-'):
        service_id = key.split('prix-')[1]
        if service_id in services_data:
          services_data[service_id]['prix'] = float(value)
    if form.is_valid():
      try:
        # facture = form.save(commit=False)
        facture.services = services_data
        facture.updated_at = timezone.now()
        numFact = facture.ref.split('-')[-1]
        if (facture.ref.startswith('DPROV') or facture.ref.startswith('FPROV')) and facture.etat_facture != 'Brouillon':
          facture.ref = (
              f'F{str(timezone.now().year)}-{str(numFact).zfill(6)}'
              if facture.type == 'Facture' else
              f'D{str(timezone.now().year)}-{str(numFact).zfill(6)}')
        elif (not facture.ref.startswith('DPROV') or not facture.ref.startswith('FPROV')) and facture.etat_facture == 'Brouillon':
           facture.ref = (
              f'FPROV{str(timezone.now().year)}-{str(numFact).zfill(6)}'
              if facture.type == 'Facture' else
              f'DPROV{str(timezone.now().year)}-{str(numFact).zfill(6)}')
        form.save()
        messages.success(request, "Modification du facture avec succsse")
        return redirect(request.META.get('HTTP_REFERER'))
      except Exception as e:
        print("Erreur lors de l'enregistrement:", e)
        messages.error(request, f"Erreur lors de l'enregistrement: {str(e)}")
        return redirect(request.META.get('HTTP_REFERER'))
    else:
      print("Erreurs de validation:", form.errors)
      messages.error(request, "Erreur lors de l'ajout de la facture. Veuillez vérifier les informations entrées.")
      return redirect(request.META.get('HTTP_REFERER'))
  elif request.method == 'GET':
    user = request.user
    services = Service.objects.all() 
    services_list = list(services.values('id', 'nom_service', 'prix_unitaire', 'description'))
    for service in services_list:
      service['prix_unitaire'] = float(service['prix_unitaire'])  # Conversion
    context = {
      'facture': facture,
      'user': user,
      "services_json" : json.dumps(services_list)
    }
    return render(request, 'facture_pages/edit_facture.html', context)

@login_required(login_url="accounts:login_user")
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
  try:
    facture.delete()
    messages.success(request, "Facture supprimée avec succès.")
  except Exception as e:
    print("Erreur lors de la suppression:", str(e))
    messages.error(request, f"Erreur lors de la suppression: {str(e)}")
  return redirect('facture:index')

@login_required(login_url="accounts:login_user")
def generate_pdf(request):
  # html = render(request, 'facture_pages/index.html')
  facure_id = request.GET.get('facture_id')
  html = "<div>Hello word</div>"
  # Generate PDF using xhtml2pdf
  result = pisa.CreatePDF(html, dest=BytesIO())
  if result.err:
    return HttpResponse(f'Error generating PDF: {result.err}')
  response = HttpResponse(content_type='application/pdf')
  response.write(result.dest.getvalue())
  # return response
  context = {"facture_generate" : facure_id}
  return render(request, 'facture_pages/generate_pdf.html', context)

@login_required(login_url="accounts:login_user")
def service(request):
  if request.GET.get('search'):
    filter_search = request.GET.get('search')
    all_services = Service.objects.filter(nom_service__contains=filter_search)
  else:
    all_services = Service.objects.all()
  paginator = Paginator(all_services, 10) # Afficher les resultat par 10
  
  page = request.GET.get('page')
  services = paginator.get_page(page)
  serv_rang = range(1, services.paginator.num_pages +1)
  
  context={
    'services':services,
    'serv_rang':serv_rang,
  }
  return render(request, "facture_pages/service.html", context)

@login_required(login_url="accounts:login_user")
def ajouter_service(request):
  """
  Vue pour l'ajout d'un nouvel article.
  
  Si la méthode de requête est POST, on valide le formulaire et on l'enregistre en base de données.
  Sinon, on affiche le formulaire vide.
  
  :param request: La requête HTTP
  :return: La page de création d'article avec le formulaire et un message de succès ou d'erreur si applicable
  """
  if request.method != 'POST':
    return redirect(request.META.get('HTTP_REFERER'))
  form = ServiceForm(request.POST)
  if form.is_valid():
    form.save()
    messages.success(request, "Service ajouté avec succès.")
    return redirect(request.META.get('HTTP_REFERER'))
  else:
    messages.error(request, "Erreur lors de l'ajout de l'article. Veuillez vérifier les informations entrées.")

@login_required(login_url="accounts:login_user")
def modifier_service(request, pk):
  """
  Vue pour la modification d'une facture.
  
  Si la méthode de requête est POST, on valide le formulaire et on l'enregistre en base de données.
  Sinon, on affiche le formulaire pré-rempli.
  
  :param request: La requête HTTP
  :param pk: La clé primaire de la facture à modifier
  :return: La page de modification de facture avec le formulaire pré-rempli et un message de succès si applicable
  """
  service = get_object_or_404(Service, pk=pk)
  if request.method == 'POST':
    form = ServiceForm(request.POST, instance=service)
    if form.is_valid():
      form.save()
      messages.success(request, "Service modifié avec succès.")
      return redirect('facture:service')
  return redirect('facture:service')

@login_required(login_url="accounts:login_user")
def supprimer_service(request, pk):
  """
  Vue pour la suppression d'une service.
  
  Si la méthode de requête est POST, on supprime la facture de la base de données.
  Sinon, on affiche la page de confirmation de suppression.
  
  :param request: La requête HTTP
  :param pk: La clé primaire de la facture à supprimer
  :return: La page de confirmation de suppression ou un message de succès si applicable
  """
  service = get_object_or_404(Service, pk=pk)
  try:
    service.delete()
    messages.success(request, "Service supprimée avec succès.")
  except Exception as e:
    print("Erreur lors de la suppression:", e)
    messages.error(request, f"Erreur lors de la suppression: {str(e)}")
  return redirect('facture:service')

# @login_required
# def service(request):
#   services = Service.objects.all()
  
#   context={
#     'services':services,
#   }
#   return render(request, "facture_pages/service.html", context)

@login_required(login_url="accounts:login_user")
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

@login_required(login_url="accounts:login_user")
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
