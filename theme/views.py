from django.http import HttpResponseRedirect


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
def change_theme(request, **kwargs):
  if 'is_dark_theme' in request.session:
    request.session['is_dark_theme'] = not request.session['is_dark_theme']
    # request.session['is_dark_theme'] = not request.session.get('is_dark_theme')
  else:
    request.session['is_dark_theme'] = True
  return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))