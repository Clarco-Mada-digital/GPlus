from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
      photo = models.ImageField(upload_to='photos/', blank=True, null=True)
      phone = models.CharField(max_length=15, blank=True)
