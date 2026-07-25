from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Étudiant'
        ADMIN = 'ADMIN', 'Administrateur'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    active_jti = models.CharField(max_length=255, blank=True, null=True)
    premium_until = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def is_premium(self):
        if self.premium_until:
            return timezone.now() < self.premium_until
        return False

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)