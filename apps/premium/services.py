# apps/premium/services.py
import hashlib
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import PremiumCode

def activate_premium_code(user, raw_code: str):
    # Calcul du hash SHA-256 du code fourni
    code_hash = hashlib.sha256(raw_code.strip().encode('utf-8')).hexdigest()
    
    with transaction.atomic():
        try:
            premium_code = PremiumCode.objects.select_for_update().get(code_hash=code_hash, is_used=False)
        except PremiumCode.DoesNotExist:
            raise ValidationError("Code invalide ou déjà utilisé.")

        # Calcul de la nouvelle période de validité
        now = timezone.now()
        user.premium_until = now + timedelta(days=30)[cite: 1]
        user.save()

        # Marquage du code comme consommé
        premium_code.is_used = True
        premium_code.used_at = now
        premium_code.used_by = user
        premium_code.save()

    return user