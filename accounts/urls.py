from django.urls import path
from .views import signIn, home, logout_user

urlpatterns = [
    path('signIn/', signIn, name='signIn'),  # Page de connexion
    path('home/', home, name='home'),  # Page d'accueil après connexion
    path('logout/', logout_user, name='logout'), #déconnexion
]