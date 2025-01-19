from django.shortcuts import render
from django.utils import timezone

# Create your views here.

def index(request):
  today = timezone.now()
  years = range(today.year - 5, today.year + 1)
  
  context = {
    'years' : years,
  }
  return render(request, "facture_pages/index.html", context)


def facture(request):
  pass
  return render(request, "facture_pages/facture.html")