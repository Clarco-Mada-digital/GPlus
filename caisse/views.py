from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.serializers import serialize
from django.db import models  # Ajoutez cette ligne
import json
from decimal import Decimal
from .models import Categorie, Personnel, Fournisseur, OperationEntrer, OperationSortir, Beneficiaire
from .forms import FournisseurForm, PersonnelForm, CategorieForm, OperationEntrerForm, OperationSortirForm
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from django.db.models.functions import TruncYear, TruncMonth
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import update_session_auth_hash
from django.template import loader
import openpyxl
from openpyxl import Workbook
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

User = get_user_model()

def is_admin(user):
    return user.is_staff

# Vues principales

@login_required
def index(request):
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calcul des totaux
    solde_actuel = OperationEntrer.objects.aggregate(Sum('montant'))['montant__sum'] or 0
    solde_actuel -= OperationSortir.objects.aggregate(Sum('montant'))['montant__sum'] or 0
    
    total_entrees = OperationEntrer.objects.aggregate(Sum('montant'))['montant__sum'] or 0
    total_sorties = OperationSortir.objects.aggregate(Sum('montant'))['montant__sum'] or 0

    # Données pour le graphique Résumé du mois (12 derniers mois)
    douze_mois_ago = today - timedelta(days=365)
    
    # Récupérer les entrées et sorties par mois
    entrees_par_mois = OperationEntrer.objects.filter(date_transaction__gte=douze_mois_ago) \
        .annotate(mois=TruncMonth('date_transaction')) \
        .values('mois') \
        .annotate(total=Sum('montant')) \
        .order_by('mois')
    
    sorties_par_mois = OperationSortir.objects.filter(date_de_sortie__gte=douze_mois_ago) \
        .annotate(mois=TruncMonth('date_de_sortie')) \
        .values('mois') \
        .annotate(total=Sum('montant')) \
        .order_by('mois')

    # Calculer le solde cumulatif pour chaque mois
    soldes_par_mois = []
    solde_cumule = 0
    
    # Créer un dictionnaire des entrées et sorties par mois
    mois_data = {}
    
    for entry in entrees_par_mois:
        mois = entry['mois'].strftime("%b")
        if mois not in mois_data:
            mois_data[mois] = {'entrees': 0, 'sorties': 0}
        mois_data[mois]['entrees'] = float(entry['total'])

    for entry in sorties_par_mois:
        mois = entry['mois'].strftime("%b")
        if mois not in mois_data:
            mois_data[mois] = {'entrees': 0, 'sorties': 0}
        mois_data[mois]['sorties'] = float(entry['total'])

    # Calculer le solde cumulatif
    for mois in mois_data:
        solde_cumule += mois_data[mois]['entrees'] - mois_data[mois]['sorties']
        soldes_par_mois.append({
            'mois': mois,
            'solde': solde_cumule
        })

    # Données pour le graphique circulaire des catégories
    sorties_categories = OperationSortir.objects.values('categorie__name') \
        .annotate(total=Sum('montant')) \
        .order_by('-total')

    # Données pour les 4 derniers mois
    quatre_mois_ago = today - timedelta(days=120)
    entrees_4_mois = OperationEntrer.objects.filter(date_transaction__gte=quatre_mois_ago) \
        .values('date_transaction', 'montant') \
        .order_by('-date_transaction')[:4]

    context = {
        'solde_actuel': float(solde_actuel),
        'total_entrees': float(total_entrees),
        'total_sorties': float(total_sorties),
        'entrees_par_mois': json.dumps([{
            'mois': entry['mois'].strftime("%b"),
            'total': float(entry['total'])
        } for entry in entrees_par_mois], default=str),
        'sorties_par_mois': json.dumps([{
            'mois': entry['mois'].strftime("%b"),
            'total': float(entry['total'])
        } for entry in sorties_par_mois], default=str),
        'soldes_par_mois': json.dumps(soldes_par_mois, default=str),
        'sorties_categories': json.dumps([{
            'categorie': entry['categorie__name'],
            'total': float(entry['total'])
        } for entry in sorties_categories], default=str),
        'entrees_4_mois': json.dumps([{
            'date': entry['date_transaction'].strftime("%d/%m/%Y"),
            'montant': float(entry['montant'])
        } for entry in entrees_4_mois], default=str),
    }

    return render(request, "caisse/dashboard.html", context)

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
    """
    Affiche la liste des opérations.
    """
    # Récupérer les filtres de recherche et de triage
    query = request.GET.get('q')
    categorie_id = request.GET.get('categorie')
    beneficiaire_id = request.GET.get('beneficiaire')
    fournisseur_id = request.GET.get('fournisseur')
    montant_min = request.GET.get('montant_min')
    montant_max = request.GET.get('montant_max')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    quantite_min = request.GET.get('quantite_min')
    quantite_max = request.GET.get('quantite_max')
    sort_by = request.GET.get('sort', 'date')  # Par défaut, tri par date
    ordre = request.GET.get('order', 'asc')  # Ordre croissant ou décroissant

    # Filtrer les opérations d'entrée et de sortie
    entree = OperationEntrer.objects.all()
    sortie = OperationSortir.objects.all()

    # Appliquer les filtres
    if query:
        entree = entree.filter(
            Q(description__icontains=query) |
            Q(categorie__name__icontains=query) |
            Q(montant__icontains=query) |
            Q(date_transaction__icontains=query)
        )
        sortie = sortie.filter(
            Q(description__icontains=query) |
            Q(categorie__name__icontains=query) |
            Q(montant__icontains=query) |
            Q(date_de_sortie__icontains=query)
        )
    if categorie_id:
        entree = entree.filter(categorie_id=categorie_id)
        sortie = sortie.filter(categorie_id=categorie_id)

    if beneficiaire_id:
        sortie = sortie.filter(beneficiaire_id=beneficiaire_id)

    if fournisseur_id:
        sortie = sortie.filter(fournisseur_id=fournisseur_id)

    if date_min:
        entree = entree.filter(date_transaction__gte=date_min)
        sortie = sortie.filter(date_de_sortie__gte=date_min)

    if date_max:
        entree = entree.filter(date_transaction__lte=date_max)
        sortie = sortie.filter(date_de_sortie__lte=date_max)

    # Définir le triage pour chaque type d'opération
    sort_order = '' if ordre == 'asc' else '-'
    if sort_by == 'date':
        entree = entree.order_by(f"{sort_order}date_transaction")
        sortie = sortie.order_by(f"{sort_order}date_de_sortie")
    elif sort_by == 'montant':
        entree = entree.order_by(f"{sort_order}montant")
        sortie = sortie.order_by(f"{sort_order}montant")
    elif sort_by == 'categorie':
        entree = entree.order_by(f"{sort_order}categorie__name")
        sortie = sortie.order_by(f"{sort_order}categorie__name")
    elif sort_by == 'beneficiaire':
        sortie = sortie.order_by(f"{sort_order}beneficiaire__name")

    # Récupérer les catégories, bénéficiaires et fournisseurs pour les options de filtrage
    categories = Categorie.objects.all()
    beneficiaires = Beneficiaire.objects.all()
    fournisseurs = Fournisseur.objects.all()

    # Contexte et rendu du template
    template = loader.get_template('caisse/listes/listes_operations.html')
    context = {
        'entree': entree,
        'sortie': sortie,
        'categories': categories,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        'prix': "Ar",
        'sort_by': sort_by,
        'ordre': ordre,
    }
    return HttpResponse(template.render(context, request))

@login_required
def depenses(request):
    """
    Affiche la page des dépenses avec les opérations par employé et par catégorie.
    """
    # Récupérer le mois sélectionné
    mois_selectionne = request.GET.get('mois', timezone.now().strftime('%Y-%m'))
    
    try:
        date_debut = timezone.datetime.strptime(f"{mois_selectionne}-01", '%Y-%m-%d')
        date_fin = (date_debut + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
    except ValueError:
        date_debut = timezone.now().replace(day=1)
        date_fin = (date_debut + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

    # Filtrer les opérations par mois
    operations = OperationSortir.objects.filter(
        date_de_sortie__gte=date_debut,
        date_de_sortie__lte=date_fin
    )

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

    # Couleurs pour les catégories
    colors = [
        '#3B82F6', '#EF4444', '#F59E0B', '#10B981', '#6366F1',
        '#EC4899', '#8B5CF6', '#14B8A6', '#F97316', '#06B6D4'
    ]
    
    for i, depense in enumerate(depenses_par_categorie):
        depense['color'] = colors[i % len(colors)]

    # Dépenses par année
    depenses_par_annee = OperationSortir.objects.annotate(
        year=TruncYear('date_de_sortie')
    ).values('year').annotate(
        total_depenses=Sum('montant')
    ).order_by('year')

    # Générer la liste des mois
    mois_liste = []
    date_courante = timezone.now()
    for i in range(12):
        date = date_courante - timezone.timedelta(days=30*i)
        mois_liste.append({
            'value': date.strftime('%Y-%m'),
            'label': date.strftime('%B %Y')
        })

    context = {
        'depenses_par_employe': depenses_par_employe,
        'depenses_par_categorie': depenses_par_categorie,
        'depenses_par_annee': depenses_par_annee,
        'mois_selectionne': mois_selectionne,
        'mois_liste': mois_liste,
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
@require_POST
@csrf_exempt
def modifier_acteur(request, type_acteur, pk):
    if type_acteur == 'personnel':
        acteur = get_object_or_404(Personnel, pk=pk)
    elif type_acteur == 'fournisseur':
        acteur = get_object_or_404(Fournisseur, pk=pk)
    else:
        return JsonResponse({'success': False, 'error': 'Type d\'acteur invalide'}, status=400)

    data = json.loads(request.body)
    
    for key, value in data.items():
        setattr(acteur, key, value)
    
    acteur.save()
    
    return JsonResponse({
        'success': True,
        'acteur': {
            'id': acteur.id,
            'name': acteur.name if hasattr(acteur, 'name') else f"{acteur.first_name} {acteur.last_name}",
            'contact': acteur.contact if hasattr(acteur, 'contact') else acteur.email,
        }
    })

@login_required
@require_POST
@csrf_exempt
def supprimer_acteur(request, type_acteur, pk):
    if type_acteur == 'personnel':
        acteur = get_object_or_404(Personnel, pk=pk)
    elif type_acteur == 'fournisseur':
        acteur = get_object_or_404(Fournisseur, pk=pk)
    else:
        return JsonResponse({'success': False, 'error': 'Type d\'acteur invalide'}, status=400)

    acteur.delete()
    
    return JsonResponse({'success': True})

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
@require_POST
@csrf_exempt
def modifier_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    data = json.loads(request.body)
    
    categorie.name = data.get('name', categorie.name)
    categorie.description = data.get('description', categorie.description)
    categorie.type = data.get('type', categorie.type)
    
    categorie.save()
    
    return JsonResponse({
        'success': True,
        'categorie': {
            'id': categorie.id,
            'name': categorie.name,
            'description': categorie.description,
            'type': categorie.type
        }
    })

@login_required
@require_POST
@csrf_exempt
def supprimer_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    categorie.delete()
    return JsonResponse({'success': True})

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
            
        return redirect('caisse:listes')

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
        return redirect('caisse:listes') # Rediriger après un traitement réussi

    return render(request, 'caisse/operations/entre-sortie.html', {
        'categories_sortie': categories_sortie,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        'operation': 'sortie',
    })

@login_required
@require_http_methods(["GET", "POST"])
def modifier_entree(request, pk):
    """
    Modifie une opération d'entrée.
    """
    operation = get_object_or_404(OperationEntrer, pk=pk)

    try:
        if request.method == 'POST':
            # Si les données sont envoyées en multipart/form-data
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = request.POST.dict()
            else:
                # Si les données sont envoyées en JSON
                data = json.loads(request.body)

            # Mise à jour des champs
            operation.description = data.get('description', operation.description)
            operation.montant = float(data.get('montant', operation.montant))
            operation.date = data.get('date', operation.date)
            operation.categorie_id = data.get('categorie', operation.categorie_id)

            operation.save()

            return JsonResponse({
                'success': True,
                'operation': {
                    'id': operation.id,
                    'description': operation.description,
                    'montant': operation.montant,
                    'date': operation.date,
                    'categorie': operation.categorie.name if operation.categorie else None,
                }
            })
        else:
            # Préparation des données pour affichage
            form = OperationEntrerForm(instance=operation)
            form_data = {field_name: form[field_name].value() for field_name in form.fields}
            return JsonResponse({'form': form_data, 'type_operation': 'entrees'})

    except KeyError as e:
        return JsonResponse({
            'success': False, 
            'error': f"Champ requis manquant: {str(e)}"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET", "POST"])
def modifier_sortie(request, pk):
    """
    Modifie une opération de sortie.
    """
    operation = get_object_or_404(OperationSortir, pk=pk)

    try:
        if request.method == 'POST':
            # Si les données sont envoyées en multipart/form-data
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = request.POST.dict()
            else:
                # Si les données sont envoyées en JSON
                data = json.loads(request.body)

            # Mise à jour des champs
            operation.description = data.get('description', operation.description)
            operation.montant = float(data.get('montant', operation.montant))
            operation.quantite = int(data.get('quantite', operation.quantite))
            operation.date = data.get('date', operation.date)
            operation.categorie_id = data.get('categorie', operation.categorie_id)
            operation.beneficiaire_id = data.get('beneficiaire', operation.beneficiaire_id)
            operation.fournisseur_id = data.get('fournisseur', operation.fournisseur_id)

            operation.save()

            return JsonResponse({
                'success': True,
                'operation': {
                    'id': operation.id,
                    'description': operation.description,
                    'montant': operation.montant,
                    'quantite': operation.quantite,
                    'date': operation.date,
                    'categorie': operation.categorie.name if operation.categorie else None,
                    'beneficiaire': operation.beneficiaire.name if operation.beneficiaire else None,
                    'fournisseur': operation.fournisseur.name if operation.fournisseur else None,
                }
            })
        else:
            # Préparation des données pour affichage
            form = OperationSortirForm(instance=operation)
            form_data = {field_name: form[field_name].value() for field_name in form.fields}
            return JsonResponse({'form': form_data, 'type_operation': 'sorties'})

    except KeyError as e:
        return JsonResponse({
            'success': False, 
            'error': f"Champ requis manquant: {str(e)}"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)

#Suppression des entrées
@login_required
def supprimer_entree(request, pk):
    """
    Supprime une opération d'entrée ou de sortie en fonction de son ID.
    """

    operation = OperationEntrer.objects.get(pk=pk)
    
    operation.delete()
    messages.success(request, "L'opération a été supprimée avec succès.")
    
    return redirect('caisse:listes')

#Suppression des sorties
@login_required
def supprimer_sortie(request, pk):
    """
    Supprime une opération d'entrée ou de sortie en fonction de son ID.
    """

    operation = OperationSortir.objects.get(pk=pk)
    
    operation.delete()
    messages.success(request, "L'opération a été supprimée avec succès.")
    
    return redirect('caisse:listes')

# Add this new view
@login_required
def parametres(request):
    """
    Affiche la page des paramètres.
    """
    context = {
        # You can add any necessary context data here
    }
    return render(request, "caisse/parametres/parametres.html", context)

@login_required
@require_POST
@csrf_exempt
def creer_categorie(request):
    data = json.loads(request.body)
    name = data.get('name')
    description = data.get('description')
    type = data.get('type')
    
    if not name or not type:
        return JsonResponse({'success': False, 'error': 'Nom et type sont requis'}, status=400)
    
    categorie = Categorie.objects.create(name=name, description=description, type=type)
    
    return JsonResponse({
        'success': True,
        'categorie': {
            'id': categorie.id,
            'name': categorie.name,
            'description': categorie.description,
            'type': categorie.type
        }
    })

@login_required
def editer_acteur(request, type_acteur, pk):
    if type_acteur == 'personnel':
        acteur = get_object_or_404(Personnel, pk=pk)
        form_class = PersonnelForm
    elif type_acteur == 'fournisseur':
        acteur = get_object_or_404(Fournisseur, pk=pk)
        form_class = FournisseurForm
    else:
        messages.error(request, "Type d'acteur non valide.")
        return redirect('caisse:acteurs')

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=acteur)
        if form.is_valid():
            form.save()
            messages.success(request, f"{type_acteur.capitalize()} modifié avec succès.")
            return redirect('caisse:acteurs')
    else:
        form = form_class(instance=acteur)

    context = {
        'form': form,
        'type_acteur': type_acteur,
        'acteur': acteur,
    }
    return render(request, 'caisse/acteurs/editer_acteur.html', context)

@login_required
def editer_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie modifiée avec succès.")
            return redirect('caisse:acteurs')
    else:
        form = CategorieForm(instance=categorie)
    
    context = {
        'form': form,
        'categorie': categorie,
    }
    return render(request, 'caisse/acteurs/editer_categorie.html', context)

@login_required
@user_passes_test(is_admin)
def utilisateurs(request):
    """
    Affiche la liste des utilisateurs.
    """
    users = User.objects.all()
    return render(request, 'caisse/utilisateurs/utilisateurs.html', {'users': users})

@login_required
@user_passes_test(is_admin)
@csrf_exempt
def creer_utilisateur(request):
    """
    Crée un nouvel utilisateur.
    """
    if request.method != 'POST':
        return redirect('caisse:utilisateurs')
    
    try:
        # Récupérer les données du formulaire
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'true'
        is_active = request.POST.get('is_active') == 'true'
        
        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            messages.error(request, "Un utilisateur avec ce nom d'utilisateur existe déjà")
            return redirect('caisse:utilisateurs')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Un utilisateur avec cet email existe déjà")
            return redirect('caisse:utilisateurs')
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_active=is_active
        )

        # Gérer l'upload de la photo
        if 'photo' in request.FILES:
            user.photo = request.FILES['photo']
            user.save()
        
        messages.success(request, "Utilisateur créé avec succès")
        return redirect('caisse:utilisateurs')
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la création de l'utilisateur: {str(e)}")
        return redirect('caisse:utilisateurs')

@login_required
@user_passes_test(is_admin)
@require_POST
@csrf_exempt
def modifier_utilisateur(request, pk):
    """
    Modifie un utilisateur existant.
    """
    user = get_object_or_404(User, pk=pk)
    
    try:
        # Si les données sont envoyées en multipart/form-data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.POST.dict()
            # Convertir les chaînes 'true'/'false' en booléens
            data['is_staff'] = data.get('is_staff', 'false').lower() == 'true'
            data['is_active'] = data.get('is_active', 'true').lower() == 'true'
        else:
            # Si les données sont envoyées en JSON
            data = json.loads(request.body)
        
        # Vérifier si le nom d'utilisateur existe déjà pour un autre utilisateur
        if User.objects.exclude(pk=pk).filter(username=data['username']).exists():
            return JsonResponse({
                'success': False, 
                'error': "Un utilisateur avec ce nom d'utilisateur existe déjà"
            }, status=400)
            
        if User.objects.exclude(pk=pk).filter(email=data['email']).exists():
            return JsonResponse({
                'success': False, 
                'error': "Un utilisateur avec cet email existe déjà"
            }, status=400)
        
        user.username = data['username']
        user.email = data['email']
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.is_staff = data.get('is_staff', False)
        user.is_active = data.get('is_active', True)
        
        if data.get('password'):
            user.set_password(data['password'])
            
        # Gérer l'upload de la photo
        if 'photo' in request.FILES:
            user.photo = request.FILES['photo']
            
        user.save()
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'photo_url': user.photo.url if user.photo else None
            }
        })
    except KeyError as e:
        return JsonResponse({
            'success': False, 
            'error': f"Champ requis manquant: {str(e)}"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)

@login_required
@user_passes_test(is_admin)
@require_POST
@csrf_exempt
def supprimer_utilisateur(request, pk):
    """
    Supprime un utilisateur.
    """
    user = get_object_or_404(User, pk=pk)
    
    try:
        user.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
def editer_utilisateur(request, pk):
    """
    Affiche le formulaire de modification d'un utilisateur.
    """
    user = get_object_or_404(User, pk=pk)
    if request.method == 'GET':
        return render(request, 'caisse/utilisateurs/modifier_utilisateur.html', {'user': user})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@superuser_required
def historique(request):
    """
    Affiche l'historique des activités de tous les utilisateurs (admin ou non)
    """
    if request.user.is_superuser:
        historique = OperationSortir.history.all()
        return render(request, 'caisse/historique/historique.html', {'historique': historique})
    else:
        return redirect('caisse:index')

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        
        # Mise à jour des informations de base
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')

        # Gestion de la photo de profil
        if 'photo' in request.FILES:
            user.photo = request.FILES['photo']
        
        try:
            user.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour du profil: {str(e)}')
        
        return redirect('caisse:parametres')
    
    return redirect('caisse:parametres')

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user
        
        # Vérification du mot de passe actuel
        if not user.check_password(current_password):
            messages.error(request, 'Le mot de passe actuel est incorrect.')
            return redirect('caisse:parametres')
        
        # Vérification de la correspondance des nouveaux mots de passe
        if new_password != confirm_password:
            messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
            return redirect('caisse:parametres')
        
        # Mise à jour du mot de passe
        try:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Garde l'utilisateur connecté
            messages.success(request, 'Votre mot de passe a été modifié avec succès.')
        except Exception as e:
            messages.error(request, f'Erreur lors du changement de mot de passe: {str(e)}')
        
        return redirect('caisse:parametres')
    
    return redirect('caisse:parametres')

@login_required
def liste_entrees(request):
    """
    Affiche la liste des opérations d'entrée.
    """
    # Récupérer les filtres de recherche et de triage
    query = request.GET.get('q')
    categorie_id = request.GET.get('categorie')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    sort_by = request.GET.get('sort', 'date')  # Trier par date par défaut

    # Filtrer les opérations d'entrée
    entrees = OperationEntrer.objects.all()

    if query:
        entrees = entrees.filter(
            Q(description__icontains=query) | 
            Q(categorie__name__icontains=query) |
            Q(montant__icontains=query) | 
            Q(date_transaction__icontains=query)
        )
    if categorie_id:
        entrees = entrees.filter(categorie_id=categorie_id)
    if date_min:
        entrees = entrees.filter(date_transaction__gte=date_min)
    if date_max:
        entrees = entrees.filter(date_transaction__lte=date_max)

    # Appliquer le triage
    entrees = entrees.order_by(sort_by)

    # Récupérer uniquement les catégories de type "entrée" pour les options de filtrage
    categories = Categorie.objects.filter(type="entrée")

    # Charger le template
    template = loader.get_template('caisse/listes/entrees.html')

    # Contexte à passer au template
    context = {
        'entrees': entrees,
        'categories': categories,
        'prix': "Ar",
        'sort_by': sort_by,
    }
    return HttpResponse(template.render(context, request))

@login_required
def liste_sorties(request):
    """
    Affiche la liste des opérations de sortie.
    """
    # Récupérer les filtres de recherche et de triage
    query = request.GET.get('q')
    categorie_id = request.GET.get('categorie')
    beneficiaire_id = request.GET.get('beneficiaire')
    fournisseur_id = request.GET.get('fournisseur')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    sort_by = request.GET.get('sort', 'date')  # Trier par date par défaut

    # Filtrer les opérations de sortie
    sorties = OperationSortir.objects.all()

    if query:
        sorties = sorties.filter(
            Q(description__icontains=query) | 
            Q(categorie__name__icontains=query) |
            Q(montant__icontains=query) | 
            Q(date_de_sortie__icontains=query)
            )
    if categorie_id:
        sorties = sorties.filter(categorie_id=categorie_id)
    if beneficiaire_id:
        sorties = sorties.filter(beneficiaire_id=beneficiaire_id)
    if fournisseur_id:
        sorties = sorties.filter(fournisseur_id=fournisseur_id)
    if date_min:
        sorties = sorties.filter(date_de_sortie__gte=date_min)
    if date_max:
        sorties = sorties.filter(date_de_sortie__lte=date_max)

    # Appliquer le triage
    sorties = sorties.order_by(sort_by)

    # Récupérer uniquement les catégories de type "sortie" pour les options de filtrage
    categories = Categorie.objects.filter(type="sortie")
    beneficiaires = Beneficiaire.objects.all()
    fournisseurs = Fournisseur.objects.all()

    # Charger le template
    template = loader.get_template('caisse/listes/sorties.html')

    # Contexte à passer au template
    context = {
        'sorties': sorties,
        'categories': categories,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        'prix': "Ar",
        'sort_by': sort_by,
    }
    return HttpResponse(template.render(context, request))


#Pour générer un rapport en EXCEL (.xlsx)
def generer_excel_operations(request):
    # Vérifie si l'utilisateur souhaite exporter toutes les opérations ou seulement celles sélectionnées
    if request.POST.get("export_all"):
        operations_entrer = OperationEntrer.objects.all()
        operations_sortir = OperationSortir.objects.all()
    else:
        selected_ids = request.POST.getlist("selected_operations")
        operations_entrer = OperationEntrer.objects.filter(id__in=selected_ids)
        operations_sortir = OperationSortir.objects.filter(id__in=selected_ids)

    # Création d'un nouveau classeur Excel
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Liste des Opérations"

    # En-têtes
    headers = ["Type", "Description", "Catégorie", "Bénéficiaire", "Fournisseur", "Date", "Quantité", "Montant"]
    sheet.append(headers)

    # Style des en-têtes
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    for col_num, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Définir la largeur des colonnes
    column_widths = [10, 30, 15, 25, 20, 20, 15, 15]
    for i, width in enumerate(column_widths, 1):
        sheet.column_dimensions[get_column_letter(i)].width = width

    # Fonction pour ajouter des opérations au fichier Excel
    def ajouter_operations(operations, type_operation, avec_beneficiaire=False):
        for operation in operations:
            beneficiaire = operation.beneficiaire.name if avec_beneficiaire else "N/A"
            fournisseur = operation.fournisseur.name if avec_beneficiaire else "N/A"
            quantite = operation.quantite if avec_beneficiaire else "N/A"
            date_str = operation.date.strftime('%d-%m-%Y')
            row = [type_operation, operation.description, operation.categorie.name, beneficiaire, fournisseur, date_str, quantite, operation.montant]
            sheet.append(row)

    # Ajouter les opérations d'entrée et de sortie
    ajouter_operations(operations_entrer, "Entrée")
    ajouter_operations(operations_sortir, "Sortie", avec_beneficiaire=True)

    # Nom du fichier avec la date et l'heure actuelles
    now = datetime.now().strftime('%d-%m-%Y_%H-%M')
    filename = f"rapport_operations_{now}.xlsx"

    # Préparer la réponse HTTP
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)

    return response

def generer_excel_operations_entrees(request):
    if request.POST.get("export_all"):
        operations_entrer = OperationEntrer.objects.all()
    else:
        selected_ids = request.POST.getlist("selected_operations")
        operations_entrer = OperationEntrer.objects.filter(id__in=selected_ids)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Entrées"

    headers = ["Description", "Catégorie", "Date", "Montant"]
    sheet.append(headers)

    for col_num, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_num)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    # Définir la largeur des colonnes
    column_widths = [10, 30, 15, 25, 20, 20, 15, 15]
    for i, width in enumerate(column_widths, 1):
        sheet.column_dimensions[get_column_letter(i)].width = width


    for operation in operations_entrer:
        row = [operation.description, operation.categorie.name, operation.date_transaction, operation.montant]
        sheet.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"entrees_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)

    return response

def generer_excel_operations_sorties(request):
    # Vérifier si l'utilisateur souhaite exporter toutes les opérations ou seulement celles sélectionnées
    if request.POST.get("export_all"):
        operations_sortie = OperationSortir.objects.all()
    else:
        selected_ids = request.POST.getlist("selected_operations")
        operations_sortie = OperationSortir.objects.filter(id__in=selected_ids)

    # Créer un nouveau classeur Excel
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sorties"

    # Définir les en-têtes
    headers = ["Description", "Catégorie", "Bénéficiaire", "Fournisseur", "Date", "Quantité", "Montant"]
    sheet.append(headers)

    # Style des en-têtes
    for col_num, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_num)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Remplir les données des opérations de sortie
    for operation in operations_sortie:
        row = [
            operation.description,
            operation.categorie.name,
            f"{operation.beneficiaire.personnel} {operation.beneficiaire.name}",
            operation.fournisseur.name,
            operation.date_de_sortie.strftime('%d-%m-%Y'),
            operation.quantite,
            operation.montant,
        ]
        sheet.append(row)

    # Ajuster la largeur des colonnes
    column_widths = [30, 20, 25, 25, 20, 10, 15]  # Largeurs ajustées
    for i, width in enumerate(column_widths, 1):
        sheet.column_dimensions[get_column_letter(i)].width = width

    # Créer la réponse HTTP pour le fichier Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"sorties_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)

    return response