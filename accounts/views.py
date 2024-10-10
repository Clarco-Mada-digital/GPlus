from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser


# Create your views here.
def signIn(request):
  if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        # Récupérer l'utilisateur avec l'email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "L'email ou le mot de passe est incorrect.")
            return redirect('signIn')

        # Authentifier l'utilisateur avec l'email et le mot de passe
        user = authenticate(request, email=user.username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Rediriger vers la page d'accueil après la connexion
        else:
            messages.error(request, "L'email ou le mot de passe est incorrect.")

  return render(request, 'index.html')


def logout_user(request):
  logout(request)  # Déconnexion de l'utilisateur
  return redirect('signIn')  # Redirection vers la page de connexion après déconnexion

@login_required(login_url='signIn')
def home(request):
    return render(request, 'home.html')