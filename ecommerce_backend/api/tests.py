from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class HealthTests(APITestCase):
    def test_health(self):
        url = reverse('Health')  # Make sure the URL is named
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Server is up!"})


class RoutesSmokeTests(APITestCase):
    def test_categories_list_exists(self):
        response = self.client.get('/api/categories/')
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cart_requires_auth(self):
        response = self.client.get('/api/cart/')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_cart_authenticated_access(self):
        user = User.objects.create_user(username="u1", password="pass12345")
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
