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
from django.urls import reverse
from itertools import chain
from operator import attrgetter
from django.core.paginator import Paginator
from .models import UserActivity
from functools import wraps
from babel.dates import format_date

User = get_user_model()

def is_admin(user):
    return user.is_staff

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('caisse:index')  # Remplacez 'index' par le nom de votre URL d'index
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Vues principales

@login_required
def index(request):
    """Vue du tableau de bord"""
    # Calcul des totaux globaux
    total_entrees = OperationEntrer.objects.aggregate(Sum('montant'))['montant__sum'] or 0
    total_sorties = OperationSortir.objects.aggregate(Sum('montant'))['montant__sum'] or 0
    solde_actuel = total_entrees - total_sorties

    # Obtenir les 6 derniers mois
    today = timezone.now()
    six_months_ago = today - timedelta(days=180)

    # Données des entrées par mois
    entrees_par_mois = list(OperationEntrer.objects.filter(
        date_transaction__gte=six_months_ago
    ).annotate(
        mois=TruncMonth('date_transaction')
    ).values('mois').annotate(
        total=Sum('montant')
    ).order_by('mois'))

    # Données des sorties par mois 
    sorties_par_mois = list(OperationSortir.objects.filter(
        date_de_sortie__gte=six_months_ago
    ).annotate(
        mois=TruncMonth('date_de_sortie')
    ).values('mois').annotate(
        total=Sum('montant')
    ).order_by('mois'))

    # Données pour le graphique des catégories de sorties
    sorties_categories = list(OperationSortir.objects.values(
        'categorie__name'
    ).annotate(
        total=Sum('montant')
    ).order_by('-total')[:5])

    # Créer un dictionnaire pour faciliter l'accès aux totaux par mois
    entrees_dict = {item['mois'].strftime('%Y-%m'): item['total'] for item in entrees_par_mois}
    sorties_dict = {item['mois'].strftime('%Y-%m'): item['total'] for item in sorties_par_mois}

    # Obtenir tous les mois uniques
    all_months = sorted(set(entrees_dict.keys()) | set(sorties_dict.keys()))

    # Calculer les soldes cumulatifs
    solde_cumule = 0
    soldes_par_mois = []
    formatted_entrees = []
    formatted_sorties = []
    
    for mois_str in all_months:
        entree_mois = float(entrees_dict.get(mois_str, 0) or 0)
        sortie_mois = float(sorties_dict.get(mois_str, 0) or 0)
        solde_mois = entree_mois - sortie_mois
        solde_cumule += solde_mois
        
        # Convertir la chaîne de date en objet datetime pour le formatage
        mois_date = datetime.strptime(mois_str, '%Y-%m')
        mois_format = format_date(mois_date, format='MMMM yyyy', locale='fr_FR')
        
        soldes_par_mois.append({
            'mois': mois_format,
            'solde': solde_cumule
        })
        formatted_entrees.append({
            'mois': mois_format,
            'total': entree_mois
        })
        formatted_sorties.append({
            'mois': mois_format,
            'total': sortie_mois
        })

    # Formater les données des catégories
    formatted_categories = [{
        'categorie': item['categorie__name'],
        'total': float(item['total'])
    } for item in sorties_categories]

    # Formater les données pour le template
    context = {
        'solde_actuel': float(solde_actuel),
        'total_entrees': float(total_entrees),
        'total_sorties': float(total_sorties),
        'entrees_par_mois': json.dumps(formatted_entrees),
        'sorties_par_mois': json.dumps(formatted_sorties),
        'soldes_par_mois': json.dumps(soldes_par_mois),
        'sorties_categories': json.dumps(formatted_categories),
        'entrees_4_mois': json.dumps(formatted_entrees[-4:]) if formatted_entrees else json.dumps([]),
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
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
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

    # Récupérer le nombre de lignes par page depuis les paramètres GET
    lignes_par_page = request.GET.get('lignes', 5)  # Valeur par défaut : 10

    # Combiner et trier par date
    if sort_by == 'date':
        key_func = lambda op: getattr(op, 'date_transaction', None) or getattr(op, 'date_de_sortie', None)
    elif sort_by == 'categorie':
        key_func = lambda op: op.categorie.name
    elif sort_by == 'description':
        key_func = lambda op: op.description
    elif sort_by == 'beneficiaire':
        key_func = lambda op: op.beneficiaire.name if op.beneficiaire else ''
    elif sort_by == 'fournisseur':
        key_func = lambda op: op.fournisseur.name if op.fournisseur else ''
    else:
        key_func = lambda op: getattr(op, 'date_transaction', None) or getattr(op, 'date_de_sortie', None)

    # Trier les opérations
    operations = sorted(
        chain(entree, sortie),
        key=key_func,
        reverse=(ordre == 'desc')
    )
    # Pagination
    paginator = Paginator(operations, lignes_par_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Récupérer les catégories, bénéficiaires et fournisseurs pour les options de filtrage
    categories = Categorie.objects.all()
    beneficiaires = Beneficiaire.objects.all()
    fournisseurs = Fournisseur.objects.all()

    # Contexte et rendu du template
    template = loader.get_template('caisse/listes/listes_operations.html')
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        'prix': "Ar",
        'sort_by': sort_by,
        'ordre': ordre,
        'lignes_par_page': lignes_par_page,
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
            'label': format_date(date, format='MMMM yyyy', locale='fr_FR')
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
            return redirect('caisse:acteurs')

        if form.is_valid():
            form.save()
            # Enregistrement de l'activité
            UserActivity.objects.create(user=request.user, action='Création', description=f'a ajouté un {type_acteur[:-1]}')
            messages.success(request, f"{type_acteur[:-1].capitalize()} ajouté avec succès.")
            return redirect('caisse:acteurs')
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez vérifier les données.")
    return redirect('caisse:acteurs')

@login_required
def ajouter_fournisseur(request):
    """
    Ajoute un nouveau fournisseur.
    """
    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            form.save()
            # Enregistrement de l'activité
            UserActivity.objects.create(user=request.user, action='Création', description='a ajouté un fournisseur')
            messages.success(request, "Fournisseur ajouté avec succès.")
            return redirect('caisse:acteurs')
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez vérifier les données.")
    return redirect('caisse:acteurs')

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
    # Enregistrement de l'activité
    UserActivity.objects.create(user=request.user, action='Modification', description='a modifier un acteur')
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
    UserActivity.objects.create(user=request.user, action='Suppression', description='a supprimé un acteur')
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
            # Enregistrement de l'activité
            UserActivity.objects.create(user=request.user, action='Création', description='a ajouté une catégorie')
            messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect('caisse:acteurs')
    return redirect('caisse:acteurs')

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
    # Enregistrement de l'activité
    UserActivity.objects.create(user=request.user, action='Modification', description='a modifier une catégorie')
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
    UserActivity.objects.create(user=request.user, action='Suppression', description='a supprimé une catégorie')
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
                # Enregistrement de l'activité
                UserActivity.objects.create(user=request.user, action='Création', description='a ajouté une opération entrée')
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
                prix_total_ligne = float(prix_total[i])


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
                    quantite=quantite,
                    montant=montant_total, # Utiliser le montant total calculé
                    categorie=categorie
                )
                operation_sortie.save()
                # Enregistrement de l'activité
                UserActivity.objects.create(user=request.user, action='Création', description='a créé une opération de sortie')
                

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
def modifier_entree(request, pk):
    # Récupérer l'entrée existante
    entree = get_object_or_404(OperationEntrer, id=pk)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        date_transaction = request.POST.get('date')
        description = request.POST.get('description')
        montant = request.POST.get('montant')
        categorie_id = request.POST.get('categorie')

        # Mettre à jour l'objet entrée
        entree.date_transaction = date_transaction
        entree.description = description
        entree.montant = montant
        entree.categorie_id = categorie_id

        # Sauvegarder les modifications
        entree.save()
        
        # Enregistrement de l'activité
        UserActivity.objects.create(user=request.user, action='Modification', description='a modifier une opération entrée')
        # Ajouter un message de succès
        messages.success(request, "L'opération d'entrée a été modifiée avec succès.")

        # Rediriger vers la liste des entrées
        return redirect(reverse('caisse:liste_entrees'))

    # Préparer le contexte pour le template
    context = {
        'entree': entree,
        'categories_entree': Categorie.objects.filter(type='entree'),
    }

    # Rendre le template avec le contexte
    return render(request, 'caisse/listes/modifier_entree.html', context)


@login_required
def modifier_sortie(request, pk):
    # Récupérer l'opération de sortie spécifique
    operation = get_object_or_404(OperationSortir, id=pk)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        date_de_sortie = request.POST.get('date')
        designation = request.POST.get('designation')
        quantite = request.POST.get('quantite')
        prix_unitaire = request.POST.get('prixUnitaire')
        beneficiaire_id = request.POST.get('beneficiaire')
        fournisseur_id = request.POST.get('fournisseur')
        categorie_id = request.POST.get('categorie')

        # Mettre à jour les champs de l'opération
        operation.date_de_sortie = date_de_sortie
        operation.description = designation
        operation.quantite = quantite
        operation.montant = prix_unitaire  # En supposant que 'montant' correspond au prix unitaire
        operation.beneficiaire_id = beneficiaire_id
        operation.fournisseur_id = fournisseur_id
        operation.categorie_id = categorie_id

        # Sauvegarder les modifications
        operation.save()
        # Enregistrement de l'activité
        UserActivity.objects.create(user=request.user, action='Modification', description='a modifier une opération sortie')
        # Ajouter un message de succès
        messages.success(request, "L'opération a été modifiée avec succès.")
        # Rediriger vers la liste des sorties
        return redirect(reverse('caisse:liste_sorties'))

    # Préparer le contexte pour le template avec les options de sélection
    context = {
        'operation': operation,
        'beneficiaires': Beneficiaire.objects.all(),
        'fournisseurs': Fournisseur.objects.all(),
        'categories_sortie': Categorie.objects.filter(type='sortie'),
    }

    # Rendre le template avec le contexte
    return render(request, 'caisse/listes/modifier_sortie.html', context)

#Suppression des entrées
@login_required
def supprimer_entree(request, pk):
    """
    Supprime une opération d'entrée ou de sortie en fonction de son ID.
    """

    operation = OperationEntrer.objects.get(pk=pk)
    
    operation.delete()
    UserActivity.objects.create(user=request.user, action='Suppression', description='a supprimé une opération entrée')
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
    UserActivity.objects.create(user=request.user, action='Suprression', description='a supprimé une opération sortie')
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
    try:
        UserActivity.objects.create(user=request.user, action='Création', description='a créé une nouvelle catégorie')
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
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
            UserActivity.objects.create(user=request.user, action='Modification', description=f'a modifié un {type_acteur}')
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
        # Enregistrement de l'activité
        UserActivity.objects.create(user=request.user, action='Modification', description='a modifier un utilisateur')
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
        UserActivity.objects.create(user=request.user, action='Suppression', description='a supprimé un utilisateur')
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
            UserActivity.objects.create(user=request.user, action='Modification', description='a modifié son profil')
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
            UserActivity.objects.create(user=request.user, action='Modification', description='a modifié son mot de passe')
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
    ordre = request.GET.get('order', 'asc')  # Ordre croissant ou décroissant

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
    if ordre == 'desc':
        sort_by = f'-{sort_by}'
    entrees = entrees.order_by(sort_by)

    # Récupérer uniquement les catégories de type "entrée" pour les options de filtrage
    categories = Categorie.objects.filter(type="entree")

    # Charger le template
    template = loader.get_template('caisse/listes/entrees.html')
    
    lignes_par_page = request.GET.get('lignes', 5)  # Valeur par défaut : 5
    paginator = Paginator(entrees, lignes_par_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contexte à passer au template
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'prix': "Ar",
        'sort_by': sort_by.lstrip('-'),  # Retirer le '-' pour le contexte
        'ordre': ordre,
        'lignes_par_page': lignes_par_page,
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
    ordre = request.GET.get('order', 'asc')  # Ordre croissant ou décroissant

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
    if ordre == 'desc':
        sort_by = f'-{sort_by}'
    sorties = sorties.order_by(sort_by)

    # Récupérer uniquement les catégories de type "sortie" pour les options de filtrage
    categories = Categorie.objects.filter(type="sortie")
    beneficiaires = Beneficiaire.objects.all()
    fournisseurs = Fournisseur.objects.all()

    # Charger le template
    template = loader.get_template('caisse/listes/sorties.html')

    # Pagination
    lignes_par_page = request.GET.get('lignes', 5)  # Valeur par défaut : 5
    paginator = Paginator(sorties, lignes_par_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Contexte à passer au template
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        'prix': "Ar",
        'sort_by': sort_by.lstrip('-'),  # Retirer le '-' pour le contexte
        'ordre': ordre,
        'lignes_par_page': lignes_par_page,
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
    # Enregistrer l'activité de l'utilisateur
    UserActivity.objects.create(
        user=request.user,
        activity_type="EXPORT",
        description=f"Export Excel des opérations d'entrée"
    )

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
    # Enregistrer l'activité de l'utilisateur
    UserActivity.objects.create(
        user=request.user,
        activity_type="EXPORT",
        description=f"Export Excel des opérations de sortie"
    )

    return response

@login_required
def historique(request):
    # Si l'utilisateur est un administrateur, afficher toutes les activités
    if request.user.is_staff:
        historique = UserActivity.objects.all().order_by('-timestamp')
    else:
        # Sinon, afficher uniquement les activités de l'utilisateur connecté
        historique = UserActivity.objects.filter(user=request.user).order_by('-timestamp')
    
    return render(request, 'caisse/historique/historique.html', {'historique': historique})