from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .api.serializers import RegestrationSerializer
from service_app.models import Profiles

class AuthTests(APITestCase):

    def setUp(self):
        user = User.objects.create_user(username='Lea', email='lea@hotmail.com', password='test1234')
        Profiles.objects.create(user = user)


    def test_existing_username_raises_error(self):
            data = {
                'username': 'Lea',
                'email': 'lea@web.com',
                'password': 'pass1234',
                'repeated_password': 'pass1234'
            }
            serializer = RegestrationSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('username', serializer.errors)
    

    def test_password_mismatch_raises_error(self):
        data = {
            'username': 'Lily',
            'email': 'lily@web.com',
            'password': 'pass1234',
            'repeated_password': 'differentpass'
        }
        serializer = RegestrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    

    def test_existing_email_raises_error(self):
        data = {
            'username': 'Leadina',
            'email': 'lea@hotmail.com', 
            'password': 'pass1234',
            'repeated_password': 'pass1234'
        }
        serializer = RegestrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


    def test_missing_email_raises_error(self):
        data = {
            'username': 'Leanouser',
            'password': 'pass1234',
            'repeated_password': 'pass1234'
        }
        serializer = RegestrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


    def test_valid_registration_data(self):
        data = {
            'username': 'Marie',
            'email': 'marie@web.com',
            'password': 'pass1234',
            'repeated_password': 'pass1234'
        }
        serializer = RegestrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())


    def test_user_login_fail(self):
        url = reverse('login')
        data = {
            'username': 'lea@hotmail.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    

    def test_user_login_success(self):
        url = reverse('login')
        data = {
            "email": "lea@hotmail.com",
            "password": "test1234"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)