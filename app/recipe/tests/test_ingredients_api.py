'''Test for Igredients API'''

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredients, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredients-list')


def create_user(email='user@example.com', password='testpass123'):
    '''Create and return user'''
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(ingredient_id):
    '''create and return ingredient API url'''
    return reverse('recipe:ingredients-detail', args=[ingredient_id])


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

    def test_update_ingredients(self):
        '''Test updating an ingredients'''

        ingredients = Ingredients.objects.create(user=self.user, name='salt')

        payload = {'name': 'pepper'}
        url = detail_url(ingredients.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredients.refresh_from_db()
        self.assertEqual(ingredients.name, payload['name'])

    def test_delete_ingredients(self):
        '''Test deleting ingredient'''

        ingredient = Ingredients.objects.create(user=self.user, name='salt')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredients.objects.filter(user=self.user).exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        '''Test listing ingredients by those assigned to recipes'''

        in1 = Ingredients.objects.create(user=self.user, name='apple')
        in2 = Ingredients.objects.create(user=self.user, name='Turkey')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Apple Crumble',
            time_minutes=50,
            price=Decimal('2.5')
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtering_ingredients_unique(self):
        '''Test filtered ingredients returns a unique list.'''

        ing = Ingredients.objects.create(user=self.user, name='eggs')
        Ingredients.objects.create(user=self.user, name='lentils')

        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Eggs Benedict',
            time_minutes=50,
            price=Decimal('7.2')
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Herb Eggs',
            time_minutes=30,
            price=Decimal('2.2')
        )

        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
