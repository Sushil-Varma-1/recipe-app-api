'''Test for Igredients API'''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredients
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredients-list')


def create_user(email='user@example.com', password='testpass123'):
    '''Create and return user'''
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTest(TestCase):
    '''Test unauthenticated API requets'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required for retrieving ingredients.'''

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    '''Test Authenticated API request.'''

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        '''Test rectrieving a list of Ingredients.'''

        Ingredients.objects.create(user=self.user, name='potato')
        Ingredients.objects.create(user=self.user, name='tomato')
        Ingredients.objects.create(user=self.user, name='pea')

        res = self.client.get(INGREDIENTS_URL)

        ingredient = Ingredients.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredient, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        '''Test list of ingredients is limited to authenticated user'''

        user2 = create_user(email='user2@example.com', password='testpass123')
        Ingredients.objects.create(user=user2, name='sugar')
        ingredient = Ingredients.objects.create(user=self.user, name='pepper')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)
