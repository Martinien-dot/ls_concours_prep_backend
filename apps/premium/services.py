import hashlib
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import PremiumCode


def hash_code(raw_code: str) -> str:
    """Computes SHA-256 hash for a raw code string."""
    return hashlib.sha256(raw_code.strip().encode('utf-8')).hexdigest()


@transaction.atomic
def activate_premium_code(user, raw_code: str):
    """
    Validates a raw code, stacks 30 days of Premium access onto the user's account,
    and marks the code as used.
    """
    code_hash = hash_code(raw_code)

    # 1. Look up the code hash with a database lock to handle concurrent activation attempts safely
    try:
        code_obj = PremiumCode.objects.select_for_update().get(code_hash=code_hash)
    except PremiumCode.DoesNotExist:
        raise ValidationError({'code': 'Code Premium invalide.'})

    # 2. Reject if the code was already redeemed
    if code_obj.is_used:
        raise ValidationError({'code': 'Ce code Premium a déjà été utilisé.'})

    now = timezone.now()

    # 3. Time Stacking Logic (+30 days)
    if user.is_premium and user.premium_until and user.premium_until > now:
        # User has an active subscription: extend current expiration date by 30 days
        user.premium_until += timedelta(days=30)
    else:
        # Subscription expired or brand new: set to 30 days from right now
        user.is_premium = True
        user.premium_until = now + timedelta(days=30)

    user.save()

    # 4. Mark the code as consumed
    code_obj.is_used = True
    code_obj.used_by = user
    code_obj.used_at = now
    code_obj.save()

    return user