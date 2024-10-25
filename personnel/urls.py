from django.urls import include, path

from personnel.views import Dashboard


app_name = 'personnel'

urlpatterns = [
    path("", Dashboard, name='dashboard'), 
]