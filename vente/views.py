from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    """Vue temporaire pour la section vente"""
    return render(request, 'vente/index.html', {
        'title': 'Module Vente',
        'description': 'Module de gestion des ventes en cours de développement'
    })
