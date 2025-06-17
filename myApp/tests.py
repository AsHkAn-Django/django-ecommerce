from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Book

User = get_user_model()

class BookViewsetTests(APITestCase):

    def setUp(self):
        # Create admin and regular user
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.user = User.objects.create_user(username='user', password='userpass')

        # Create some books
        self.book1 = Book.objects.create(title='Django for Beginners', author='William', price=20, stock=5)
        self.book2 = Book.objects.create(title='Python Crash Course', author='Eric', price=25, stock=2)

    def test_list_books(self):
        url = reverse('api:books-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_books_by_title(self):
        url = reverse('api:books-list') + '?title=django'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Django for Beginners')

    def test_retrieve_book(self):
        url = reverse('api:books-detail', args=[self.book1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.book1.title)
        self.assertIn('average_rate', response.data)
        self.assertIn('rate_numbers', response.data)

    def test_create_book_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:books-list')
        data = {
            'title': 'New Book',
            'author': 'Author',
            'price': '15.50',
            'stock': 10
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)
        self.client.force_authenticate(user=None)  # Logout after test

    def test_create_book_non_admin(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:books-list')
        data = {
            'title': 'Not Allowed Book',
            'author': 'Author',
            'price': 10.00,
            'stock': 5
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Book.objects.count(), 2)
        self.client.force_authenticate(user=None)

    def test_update_book_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:books-detail', args=[self.book1.id])
        data = {'price': '22.00'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book1.refresh_from_db()
        self.assertEqual(str(self.book1.price), '22.00')
        self.client.force_authenticate(user=None)

    def test_update_book_non_admin(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:books-detail', args=[self.book1.id])
        data = {'price': '22.00'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.book1.refresh_from_db()
        self.assertNotEqual(str(self.book1.price), '22.00')
        self.client.force_authenticate(user=None)

    def test_delete_book_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:books-detail', args=[self.book2.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 1)
        self.client.force_authenticate(user=None)

    def test_delete_book_non_admin(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:books-detail', args=[self.book2.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Book.objects.count(), 2)
        self.client.force_authenticate(user=None)
