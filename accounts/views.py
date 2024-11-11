from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.contrib.auth.forms import SetPasswordForm
from django.utils import timezone

from .models import CustomUser



# Create your views here.
def signIn(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        remember_me = request.POST.get('remember_me')  # Récupérer la case à cocher

        # Récupérer l'utilisateur avec l'email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "L'email ou le mot de passe est incorrect.")
            return redirect('accounts:signIn')

        # Authentifier l'utilisateur avec l'email et le mot de passe
        user = authenticate(request, username=user.username, password=password)
        if user is not None:
            login(request, user)

            # Gestion du 'Se souvenir de moi'
            if remember_me:  # Si la case est cochée
                request.session.set_expiry(1209600)  # 2 semaines

            return redirect('accounts:home')  # Rediriger vers la page d'accueil après la connexion
        else:
            messages.error(request, "L'email ou le mot de passe est incorrect.")

    return render(request, 'login.html')

def logout_user(request):
    logout(request)  # Déconnexion de l'utilisateur
    return redirect('accounts:signIn')  # Redirection vers la page de connexion après déconnexion


@login_required(login_url='accounts:signIn')
def home(request):
    return redirect('personnel:dashboard')

def send_otp(request):
    if request.method == "POST":
        email = request.POST.get('email')

        # Vérifier si l'adresse email existe dans la base de données
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "Cet email n'est pas enregistré.")
            return redirect('accounts:password_reset')  # Redirige vers la page de récupération

        # Générer un OTP
        otp_code = get_random_string(5, allowed_chars='0123456789')

        # Sauvegarder l'OTP dans la session utilisateur
        request.session['otp_code'] = otp_code
        request.session['email'] = email

        # Envoyer un email avec l'OTP
        subject = "Votre code de réinitialisation de mot de passe"
        message = f"Votre code OTP est : {otp_code}"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

        messages.success(request, "Un code OTP a été envoyé à votre adresse email.")
        return redirect('accounts:verify_otp')  # Redirige vers la page de vérification de l'OTP

    return render(request, 'login_forget_password.html')  # Template pour le formulaire

def verify_otp(request):
    if request.method == "POST":
        otp_input = request.POST.get('otp')
        email = request.session.get('email')
        otp_code = request.session.get('otp_code')
        otp_sent_at = request.session.get('otp_sent_at')

        # Récupérer le nombre de tentatives
        attempts = request.session.get('otp_attempts', 0)

        # Vérifier si l'OTP a expiré
        if otp_sent_at:
            otp_sent_time = timezone.datetime.fromisoformat(otp_sent_at)
            if timezone.now() > otp_sent_time + timedelta(minutes=5):
                messages.error(request, "Le code OTP a expiré. Veuillez en demander un nouveau.")
                return redirect('accounts:password_reset')  # Redirige vers la page de récupération

        # Vérifier si l'OTP correspond
        if otp_input == otp_code:
            # Réinitialiser le compteur d'essai
            request.session['otp_attempts'] = 0
            return redirect('accounts:change_password')
        else:
            attempts += 1
            request.session['otp_attempts'] = attempts
            messages.error(request, "Le code OTP est incorrect.")

            # Vérifier si le nombre maximum de tentatives est atteint
            if attempts >= 5:  # Limitez à 5 tentatives
                messages.error(request, "Nombre maximum de tentatives atteint. Veuillez demander un nouveau code OTP.")
                return redirect('accounts:password_reset')

            return redirect('accounts:verify_otp')

    return render(request, 'login_confirme_otp.html')  # Template pour la vérification de l'OTP

def change_password(request):
    email = request.session.get('email')  # Récupérer l'email depuis la session
    if request.method == 'POST':
        password = request.POST.get('password')  # Récupère le mot de passe depuis le formulaire

        try:
            user = CustomUser.objects.get(email=email)  # Récupérer l'utilisateur par email
        except CustomUser.DoesNotExist:
            messages.error(request, "L'utilisateur associé à cet email n'existe pas.")
            return redirect('accounts:password_reset')  # Redirige vers la page de récupération

        # Crée une instance du formulaire de changement de mot de passe
        form = SetPasswordForm(user=user, data={'new_password1': password, 'new_password2': password})

        if form.is_valid():
            form.save()  # Sauvegarde le nouveau mot de passe
            messages.success(request, 'Votre mot de passe a été mis à jour avec succès!')
            return redirect('accounts:update_password_success')  # Redirige vers une page de succès
        else:
            messages.error(request, 'Il y a eu une erreur lors de la mise à jour de votre mot de passe.')
    else:
        form = SetPasswordForm(user=None)  # Pas d'utilisateur connecté

    return render(request, 'login_new_password.html', {'form': form})

def update_password_success(request):
    return render(request, 'login_new_password_done.html')  # Remplacez par le nom de votre template