"""
URL configuration for GPP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

from theme.views import change_theme
from caisse.views import index


urlpatterns = [
    path("", include("accounts.urls", namespace='accounts')),
    path('admin/', admin.site.urls),
    path('switch-theme/', change_theme, name='change_theme'),
    path('caisse/', include("caisse.urls", namespace='caisse')),
    path("personnel/", include("personnel.urls", namespace='personnel')),
    path("facture/", include("facture.urls", namespace='facture')),          # Pour la module du facture et devise
    path("client/", include("clients.urls", namespace='client')),          # Pour la module du clients et prospects
    path("__reload__/", include("django_browser_reload.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
