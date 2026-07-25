from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationAPITests(APITestCase):

    def setUp(self):
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.me_url = reverse('auth_me')

        self.user_data = {
            'username': 'martinien',
            'email': 'martinien@example.com',
            'password': 'Password123!'
        }

    def test_user_registration_success(self):
        """Verify successful user registration with default STUDENT role."""
        response = self.client.post(self.register_url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.username, 'martinien')
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.is_staff)

    def test_registration_prevents_privilege_escalation(self):
        """Verify that passing 'role': 'ADMIN' during public registration is ignored."""
        malicious_data = self.user_data.copy()
        malicious_data['role'] = User.Role.ADMIN

        response = self.client.post(self.register_url, malicious_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # User must still be created as a STUDENT
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.is_staff)

    def test_single_active_session_enforcement(self):
        """
        Verify that a new login issues a new jti and immediately invalidates
        the access token of any prior active session.
        """
        # Create user
        User.objects.create_user(**self.user_data)

        # 1. Login on Device A
        response_a = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        token_a = response_a.data['access']

        # 2. Access profile with Token A -> Success (200 OK)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_a}')
        res_profile_a = self.client.get(self.me_url)
        self.assertEqual(res_profile_a.status_code, status.HTTP_200_OK)

        # 3. Login on Device B (overwrites active_jti in DB)
        response_b = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)
        token_b = response_b.data['access']

        # 4. Device A attempts to use Token A again -> Rejected (401 Unauthorized)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_a}')
        res_revoked = self.client.get(self.me_url)
        self.assertEqual(res_revoked.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res_revoked.data['detail'].code, 'concurrent_session')

        # 5. Device B uses Token B -> Success (200 OK)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_b}')
        res_valid = self.client.get(self.me_url)
        self.assertEqual(res_valid.status_code, status.HTTP_200_OK)

    def test_get_user_profile(self):
        """Verify profile endpoint returns correct user structure."""
        User.objects.create_user(**self.user_data)

        # Login to obtain token
        login_res = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        token = login_res.data['access']

        # Get profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertEqual(response.data['role'], User.Role.STUDENT)
        self.assertIn('is_premium', response.data)
        self.assertIn('premium_until', response.data)

    def test_admin_user_role_sync(self):
        """Verify programmatic creation of ADMIN user sets is_staff to True."""
        admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='AdminPassword123!',
            role=User.Role.ADMIN
        )
        self.assertTrue(admin_user.is_staff)
        self.assertEqual(admin_user.role, User.Role.ADMIN)