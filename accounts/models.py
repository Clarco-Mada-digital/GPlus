from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Create your models here.
class CustomUser(AbstractUser):
  photo = models.ImageField(upload_to='photos/', null=True, blank=True)

  def __str__(self):
    return self.username

