from django.urls import include, path
from accounts.views import index, logout_user, signup


urlpatterns = [
    path("", index, name="index"),
    path("login", signup, name="login_user"),
    path("logout", logout_user, name="logout_user"),
]