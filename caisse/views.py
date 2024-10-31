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

User = get_user_model()

def is_admin(user):
    return user.is_staff

# Vues principales

@login_required
def index(request):
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calcul des totaux
    caisse_totale = OperationEntrer.objects.aggregate(Sum('montant'))['montant__sum'] or 0
    caisse_totale -= OperationSortir.objects.aggregate(Sum('montant'))['montant__sum'] or 0
    
    entrees_mois = OperationEntrer.objects.filter(date_transaction__gte=first_day_of_month).aggregate(Sum('montant'))['montant__sum'] or 0
    sorties_mois = OperationSortir.objects.filter(date_de_sortie__gte=first_day_of_month).aggregate(Sum('montant'))['montant__sum'] or 0

    # Données pour le graphique Résumé du mois
    six_months_ago = today - timedelta(days=180)
    entrees_par_mois = OperationEntrer.objects.filter(date_transaction__gte=six_months_ago) \
        .annotate(mois=TruncMonth('date')) \
        .values('mois') \
        .annotate(total=Sum('montant')) \
        .order_by('mois')
    sorties_par_mois = OperationSortir.objects.filter(date_de_sortie__gte=six_months_ago) \
        .annotate(mois=TruncMonth('date')) \
        .values('mois') \
        .annotate(total=Sum('montant')) \
        .order_by('mois')

    labels_mois = [entry['mois'].strftime("%b") for entry in entrees_par_mois]
    entrees_data = [entry['total'] for entry in entrees_par_mois]
    sorties_data = [entry['total'] for entry in sorties_par_mois]

    # Données pour le graphique Sorties par catégories
    sorties_categories = OperationSortir.objects.values('categorie__name') \
        .annotate(total=Sum('montant')) \
        .order_by('-total')[:5]  # Top 5 catégories

    labels_categories = [entry['categorie__name'] for entry in sorties_categories]
    sorties_categories_data = [entry['total'] for entry in sorties_categories]

    # Données pour les entrées des 4 derniers mois
    quatre_mois_ago = today - timedelta(days=120)
    entrees_4_mois = OperationEntrer.objects.filter(date_transaction__gte=quatre_mois_ago) \
        .annotate(mois=TruncMonth('date')) \
        .values('mois') \
        .annotate(montant=Sum('montant')) \
        .order_by('-mois')[:4]

    # Fonction pour convertir Decimal en float
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError

    context = {
        'caisse_totale': float(caisse_totale),
        'entrees_mois': float(entrees_mois),
        'sorties_mois': float(sorties_mois),
        'labels_mois': json.dumps(labels_mois),
        'entrees_data': json.dumps([float(x) for x in entrees_data], default=decimal_default),
        'sorties_data': json.dumps([float(x) for x in sorties_data], default=decimal_default),
        'labels_categories': json.dumps(labels_categories),
        'sorties_categories_data': json.dumps([float(x) for x in sorties_categories_data], default=decimal_default),
        'entrees_4_mois': [{'mois': e['mois'], 'montant': float(e['montant'])} for e in entrees_4_mois],
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
    
    entrees = OperationEntrer.objects.all()
    sorties = OperationSortir.objects.select_related('beneficiaire', 'fournisseur', 'categorie').all()
    categories = Categorie.objects.all()
    beneficiaires = Beneficiaire.objects.all()
    fournisseurs = Fournisseur.objects.all()
    sort_by = request.GET.get('sort', 'date')

    # Détecter le type d'opération choisi (par défaut, affichage des entrées)
    type_operation = request.GET.get('type', 'entrees')
    
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
            entrees = entrees.filter(
                Q(description__icontains=filters['query']) |
                Q(categorie__name__icontains=filters['query']) |
                Q(montant__icontains=filters['query']) |
                Q(date__icontains=filters['query'])
            )
            sorties = sorties.filter(
                Q(description__icontains=filters['query']) |
                Q(categorie__name__icontains=filters['query']) |
                Q(montant__icontains=filters['query']) |
                Q(date__icontains=filters['query'])
            )

        if 'categorie' in filters:
            entrees = entrees.filter(categorie_id=filters['categorie'])
            sorties = sorties.filter(categorie_id=filters['categorie'])

        if 'beneficiaire' in filters:
            sorties = sorties.filter(beneficiaire_id=filters['beneficiaire'])

        if 'fournisseur' in filters:
            sorties = sortie.filter(fournisseur_id=filters['fournisseur'])
        
        if 'montant_min' in filters:
            entrees = entrees.filter(montant__gte=filters['montant_min'])
            sorties = sorties.filter(montant__gte=filters['montant_min'])

        if 'montant_max' in filters:
            entrees = entrees.filter(montant__lte=filters['montant_max'])
            sorties = sorties.filter(montant__lte=filters['montant_max'])

        if 'quantite_min' in filters:
            sorties = sorties.filter(quantité__gte=filters['quantite_min'])
        if 'quantite_max' in filters:
            sorties = sorties.filter(quantité__lte=filters['quantite_max'])


        if 'date_min' in filters:
            entrees = entrees.filter(date__gte=filters['date_min'])
            sorties = sorties.filter(date__gte=filters['date_min'])

        if 'date_max' in filters:
            entrees = entrees.filter(date__lte=filters['date_max'])
            sorties = sorties.filter(date__lte=filters['date_max'])
    

    # Filtrer les opérations de sortie qui ont des bénéficiaires valides
    sorties = sorties.filter(Q(beneficiaire__isnull=False) | Q(beneficiaire__personnel__isnull=False) | Q(beneficiaire__name__isnull=False))

    # Tri
    entrees = entrees.order_by(sort_by)
    sorties = sorties.order_by(sort_by)

    context = {
        'entrees': entrees,
        'sorties': sorties,
        'categories': categories,
        'beneficiaires': beneficiaires,
        'fournisseurs': fournisseurs,
        'prix': "Ar",  # Vous pouvez gérer 'Ar' dans le template
        'sort_by': sort_by,
        'type_operation': type_operation
    }

    return render(request, "caisse/listes/listes_operations.html", context)

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

@login_required
@user_passes_test(is_admin)
def historique(request):
    """
    Affiche l'historique des activités de tous les utilisateurs (admin ou non)
    """
    historique = OperationSortir.history.all()
    return render(request, 'caisse/historique/historique.html', {'historique': historique})
    
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


