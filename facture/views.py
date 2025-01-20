from django.shortcuts import render
from django.utils import timezone
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
  url = 'https://jsonplaceholder.typicode.com/users'
  res = requests.get(url)
  clients = res.json()
  # print(clients)
  context = {
    "clients_list" : clients
  }
  return render(request, "facture_pages/facture.html", context)