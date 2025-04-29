from django.contrib.auth.models import AbstractUser
from datetime import datetime
from django.db import models

class Users(AbstractUser):
    username = models.CharField(db_column='Username', max_length=100, unique=True)
    password = models.CharField(db_column='Password', max_length=100)
    email = models.EmailField(db_column='Email', max_length=255, unique=True)
    full_name = models.CharField(db_column='FullName', max_length=200, blank=True, null=True, default='Unknown FullName')
    effective_date = models.DateTimeField(db_column='EffectiveDate', blank=True, null=True, default=datetime(1900, 1, 1))
    last_login_date = models.DateTimeField(db_column='LastLoginDate', blank=True, null=True)

    # Eliminar campos innecesarios que vienen de AbstractUser
    first_name = None
    last_name = None
    date_joined = None
    last_login = None
    
    class Meta:
        db_table = 'Users'  # Cambiado a plural para consistencia con convención en inglés
