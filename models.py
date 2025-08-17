from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import datetime


class BaseUser(AbstractUser):
    """
        Redefinition of User model to make type checker happy
    """
    id: int

    username = models.CharField[str, str](max_length=150, unique=True)
    first_name = models.CharField[str, str](max_length=150, blank=True)
    last_name = models.CharField[str, str](max_length=150, blank=True)
    email = models.EmailField[str, str](blank=True)
    is_staff = models.BooleanField[bool, bool](default=False)
    is_active = models.BooleanField[bool, bool](default=True)
    is_superuser = models.BooleanField[bool, bool](default=False)
    date_joined = models.DateTimeField[datetime, datetime](default=timezone.now)

    class Meta:
        abstract = True
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'