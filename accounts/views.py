from django.conf import settings
from accounts.models import User
from django.shortcuts import redirect, render
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required

# Create your views here.
def signup(request):
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


@login_required(login_url="login_user")
def index(request):
  # auth_user = authenticate()
  return render(request, "index.html")

def logout_user(request):
  logout(request)
  return redirect("login_user")