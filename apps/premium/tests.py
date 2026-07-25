import hashlib
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.cache import cache
from premium.models import PremiumCode

User = get_user_model()


class PremiumActivationAPITests(APITestCase):

    def setUp(self):
        # Clear Redis cache before running throttle tests
        cache.clear()

        self.user = User.objects.create_user(
            username="student_tester",
            email="tester@example.com",
            password="Password123!"
        )

        # Create a valid hashed code in DB (Raw code: "PREMIUM-2026-KEY")
        self.raw_code = "PREMIUM-2026-KEY"
        code_hash = hashlib.sha256(self.raw_code.encode('utf-8')).hexdigest()
        self.premium_code = PremiumCode.objects.create(code_hash=code_hash)

        self.activate_url = reverse('premium_activate')
        self.client.force_authenticate(user=self.user)

    def test_successful_code_activation(self):
        """Validating an unused code must activate 30 days of Premium access."""
        response = self.client.post(self.activate_url, {'code': self.raw_code})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_premium'])

        # Verify DB updates
        self.user.refresh_from_db()
        self.premium_code.refresh_from_db()

        self.assertTrue(self.user.is_premium)
        self.assertTrue(self.premium_code.is_used)
        self.assertEqual(self.premium_code.used_by, self.user)

        # Verify 30-day duration window
        expected_expiration = timezone.now() + timedelta(days=30)
        self.assertAlmostEqual(
            self.user.premium_until.timestamp(),
            expected_expiration.timestamp(),
            delta=5  # Allow 5-second execution tolerance
        )

    def test_invalid_code_rejection(self):
        """Submitting a non-existent or invalid code must return a 400 error."""
        response = self.client.post(self.activate_url, {'code': 'INVALID-CODE-999'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_premium)

    def test_reusing_consumed_code_fails(self):
        """A code that has already been consumed cannot be activated a second time."""
        # Consume code first time
        self.client.post(self.activate_url, {'code': self.raw_code})

        # Create second user
        user2 = User.objects.create_user(
            username="student_tester_2",
            email="tester2@example.com",
            password="Password123!"
        )
        self.client.force_authenticate(user=user2)

        # Second activation attempt must fail
        response = self.client.post(self.activate_url, {'code': self.raw_code})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limiting_protects_brute_force(self):
        """More than 5 activation requests within one minute must trigger HTTP 429."""
        # Make 5 allowed requests
        for _ in range(5):
            self.client.post(self.activate_url, {'code': 'WRONG-CODE'})

        # The 6th attempt must be throttled
        response = self.client.post(self.activate_url, {'code': 'WRONG-CODE'})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)