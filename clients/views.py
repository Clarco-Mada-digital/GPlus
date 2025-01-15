from django.shortcuts import render
import requests

# Create your views here.
def index(request):
    
  return render(request, "client_pages/index.html")

def client(request):
  url = 'https://jsonplaceholder.typicode.com/users'
  res = requests.get(url)
  clients = res.json()
  # print(clients)
  context = {
    "clients_list" : clients
  }
  return render(request, "client_pages/client.html", context)