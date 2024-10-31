from django.db import models
from django.contrib.auth.models import AbstractUser
from simple_history.models import HistoricalRecords

# Create your models here.
class CustomUser(AbstractUser):
      photo = models.ImageField(upload_to='photos/', blank=True, default="photos/pdp_defaut.png")
