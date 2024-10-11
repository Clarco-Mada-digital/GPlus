from django.conf import settings
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
        return redirect("index")
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
@login_required(login_url="login_user")
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