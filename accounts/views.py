from django.conf import settings
from django.http import HttpResponseRedirect
from accounts.models import User
from django.shortcuts import redirect, render
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required

"""
Gère le processus d'inscription de l'utilisateur en authentifiant l'utilisateur en fonction de l'email et du mot de passe fournis. 
Si l'authentification réussit, l'utilisateur est connecté et redirigé vers la page d'accueil ; sinon, un message d'erreur est affiché.

Args:
    request: L'objet de requête HTTP contenant les données saisies par l'utilisateur.

Returns:
    None: Rendu de la page de connexion avec un message indiquant le succès ou l'échec du processus d'inscription.

Raises:
    None: Cette fonction ne lève pas explicitement d'exceptions, mais gère les erreurs en interne.

Examples:
    Pour inscrire un utilisateur, envoyez une requête POST avec les champs 'email' et 'password'.
"""
def signup(request)->None:
  message = ""
  auth_user = None
  
  if request.method == "POST":
    email = request.POST.get('email', None)
    password = request.POST.get('password', None)
    if user := User.objects.filter(email=email).first():
      if auth_user := authenticate(username=user.username, password=password):       
        login(request, auth_user)
        return redirect("accounts:index")
      else:
        message="Email ou Mot de passe inccorect"
    else:
      message = "Utilisateur introuvable !"

  context = {
    "message" : message,
    "user": auth_user,
  }
  
  return render(request, "registration/login.html", context)

"""
Rend la page d'accueil de l'application. 
Cette fonction gère la requête HTTP et retourne le modèle HTML approprié pour la vue d'accueil.

Args:
    request: L'objet de requête HTTP.

Returns:
    None: Rendu de la page index.html.

Raises:
    None: Cette fonction ne lève pas explicitement d'exceptions.

"""
@login_required(login_url="accounts:login_user")
def index(request)->None:
  # auth_user = authenticate()
  return render(request, "index.html")


"""
Déconnecte l'utilisateur authentifié et redirige vers la page appropriée. 
Cette fonction gère le processus de déconnexion de la session utilisateur.

Args:
    request: L'objet de requête HTTP.

Returns:
    None: Effectue une redirection après la déconnexion.

Raises:
    None: Cette fonction ne lève pas explicitement d'exceptions.
"""
def logout_user(request)->None:
  logout(request)
  return redirect("login_user")



"""
Affiche le tableau de bord de l'utilisateur.

Cette fonction gère la requête HTTP pour afficher le tableau de bord de l'utilisateur connecté.
Elle peut inclure des informations personnalisées, des statistiques ou des actions spécifiques à l'utilisateur.

Args:
    request: L'objet de requête HTTP.

Returns:
    HttpResponse: Rendu de la page dashboard.html avec le contexte approprié.

Raises:
    None: Cette fonction ne lève pas explicitement d'exceptions.

Note:
    Cette vue nécessite que l'utilisateur soit authentifié. Assurez-vous d'ajouter le décorateur @login_required si nécessaire.
"""
@login_required(login_url="accounts:login_user")
def dashboard(request):
  return render(request, "dashboard.html")

@login_required(login_url="accounts:login_user")
def pricing(request):
  return render(request, "pricing.html")


@login_required(login_url="accounts:login_user")
def settings(request):
  return render(request, "settings.html")

