from rest_framework.test import APIClient, APITestCase
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from cart.models import Cart



User = get_user_model()

class UserAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ashkan@test.com',
            password='test123'
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.cart = Cart.objects.create(user=self.user)

    def test_get_cart_authenticated(self):
        url = reverse('cart_api:cart_list_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_cart_unauthenticated(self):
        new_client = APIClient()
        url = reverse('cart_api:cart_list_api')
        response = new_client.get(url)
        self.assertEqual(response.status_code, 401)


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='ashkan@test.com',
            password='test123'
        )
        self.assertEqual(user.email, 'ashkan@test.com')
        self.assertTrue(user.check_password('test123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.check_password('admin123'))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


