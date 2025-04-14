from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)  # This is crucial
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.URLField(max_length=500, blank=True, null=True)
    
    class Meta:
        db_table = 'tbl_user'

    def __str__(self):
        return self.email