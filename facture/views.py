from django.shortcuts import render
from django.utils import timezone
from clients.models import Client
import requests

# Create your views here.

def index(request):
  today = timezone.now()
  years = range(today.year - 5, today.year + 1)
  
  context = {
    'years' : years,
  }
  return render(request, "facture_pages/index.html", context)


def facture(request):
  clients = Client.objects.all()
  # clients = res.json()
  # print(clients)
  context = {
    "clients_list" : clients
  }
  return render(request, "facture_pages/facture.html", context)