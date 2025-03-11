import json
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


"""
Bascule la préférence de thème de l'utilisateur entre les modes sombre et clair.

Cette fonction vérifie la session de l'utilisateur pour la clé 'is_dark_theme' et inverse sa valeur. Si la clé n'existe pas, elle définit le thème en mode sombre par défaut, puis redirige l'utilisateur vers l'URL de référence.

Args:
    request: L'objet de requête HTTP contenant les données de session.

Returns:
    HttpResponseRedirect: Une réponse de redirection vers l'URL de référence ou un chemin par défaut.

Raises:
    None: Cette fonction ne lève aucune exception.
"""
@csrf_exempt
def change_theme(request, **kwargs):
  if request.method == 'POST':
    data = json.loads(request.body)
    is_dark_theme = data.get('is_dark_theme', None)
    if is_dark_theme is not None:
      request.session['is_dark_theme'] = is_dark_theme
    else:
      request.session['is_dark_theme'] = not request.session.get('is_dark_theme', True)
    return JsonResponse({'status': 'success'})
  return JsonResponse({'status': 'failed'}, status=400)