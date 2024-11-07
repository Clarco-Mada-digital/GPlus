from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import signIn, home, logout_user, send_otp, update_password_success, change_password, verify_otp
from personnel.views import DashboardAPIView
from django.conf.urls.static import static
from django.conf import settings

app_name = 'accounts'


"""
Définit le modèle d'URL pour la vue de l'application accounts.
"""
urlpatterns = [
    path('signIn/', signIn, name='signIn'),  # Page de connexion
    path('home/', home, name='home'),  # Page d'accueil après connexion
    path('logout/', logout_user, name='logout'),  # déconnexion

    path('password-reset/', send_otp, name='password_reset'),
    path('confirme-otp/', verify_otp, name='verify_otp'),

    path('change-password/', change_password, name='change_password'),
    path('update-password-success/', update_password_success, name='update_password_success'),

    #path('api/login/', LoginView.as_view(), name='login'),
    #path('api/logout/', CustomLogoutView.as_view(), name='logout'),
   # path('api/', DashboardAPIView.as_view(), name='dashboard'),

    # URL pour obtenir le token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # URL pour rafraîchir le token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)