from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from catalog.models import Concours, Annee, Epreuve

User = get_user_model()


class CatalogAPITests(APITestCase):

    def setUp(self):
        # Create Catalog sample data
        self.concours = Concours.objects.create(nom="ENS", description="École Normale Supérieure")
        self.annee = Annee.objects.create(valeur=2024)
        self.epreuve = Epreuve.objects.create(
            concours=self.concours,
            annee=self.annee,
            titre="Mathématiques I",
            sujet_pdf_url="https://r2.storage.com/free/sujet_2024.pdf",
            corrige_pdf_url="https://r2.storage.com/premium/corrige_2024.pdf",
            corrige_video_hls_id="hls_stream_99812"
        )

        # Standard non-premium user
        self.standard_user = User.objects.create_user(
            username="standard_student",
            email="standard@test.com",
            password="Password123!"
        )

        # Premium user (valid for 30 days)
        self.premium_user = User.objects.create_user(
            username="premium_student",
            email="premium@test.com",
            password="Password123!",
            premium_until=timezone.now() + timedelta(days=30)
        )

        self.detail_url = reverse('catalog_epreuve_detail', kwargs={'pk': self.epreuve.pk})

    def test_standard_user_sees_redacted_solutions(self):
        """Standard users must see free subject PDF, but null for premium solutions."""
        self.client.force_authenticate(user=self.standard_user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sujet_pdf_url'], "https://r2.storage.com/free/sujet_2024.pdf")
        self.assertIsNone(response.data['corrige_pdf_url'])
        self.assertIsNone(response.data['corrige_video_hls_id'])
        self.assertFalse(response.data['is_premium_unlocked'])

    def test_premium_user_sees_unlocked_solutions(self):
        """Premium users must receive full access to PDFs and video HLS IDs."""
        self.client.force_authenticate(user=self.premium_user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sujet_pdf_url'], "https://r2.storage.com/free/sujet_2024.pdf")
        self.assertEqual(response.data['corrige_pdf_url'], "https://r2.storage.com/premium/corrige_2024.pdf")
        self.assertEqual(response.data['corrige_video_hls_id'], "hls_stream_99812")
        self.assertTrue(response.data['is_premium_unlocked'])