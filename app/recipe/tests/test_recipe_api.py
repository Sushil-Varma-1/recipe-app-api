'''Tests for recipe api'''

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredients
from recipe.serializers import (RecipeSerializer,
                                RecipeDetailSerializer)
from decimal import Decimal


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    '''Create and return a recipe detail URL'''
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    '''create and return a recipe'''

    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'httpp://example.com/recipe.pdf'
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


def create_user(**params):
    '''create and return new user'''
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITest(TestCase):
    '''Test unauthorized API requests'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required to call API'''

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    '''Test authorized API requests'''

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com',
                                password='testpass123')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        '''Test retrieving a list of recipes'''

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_listed_to_user(self):
        '''Test list of Recipes is limited to authenticated user.'''

        other_user = create_user(email='otheruser@example.com',
                                 password='otherpass123')

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        '''Test get recipe detail'''

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)

        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        '''Test creating a recipe'''

        payload = {
            'title': 'Sample recipe title 1',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'description': 'Sample description',
            'link': 'httpp://example.com/recipe.pdf'
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        '''Test partial update of Recipe'''

        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe title 3',
            link=original_link,
        )

        payload = {'title': 'Recipe Title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        '''Test full update of recipe'''

        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe title 3',
            link='https://example.com/recipe.pdf',
            description='Sample Recipe Description'
        )

        payload = {
            'title': 'New recipe title 1',
            'time_minutes': 20,
            'price': Decimal('4.25'),
            'description': 'New Sample description',
            'link': 'httpp://example.com/new-recipe.pdf'
        }
        url = detail_url(recipe.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        '''Test changing the Recipe user results in an error'''

        new_user = create_user(email='new_user@example.com',
                               password='newpass123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        '''Test deleting a recipe Successful'''

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        '''test trying to delete recipes gives error'''

        new_user = create_user(email='new_user@example.com',
                               password='test123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tag(self):
        '''Test creating a recipe with new Tags'''

        payload = {
            'title': 'samosha',
            'time_minutes': 20,
            'price': Decimal('20.5'),
            'tags': [{'name': 'tasty'}, {'name': 'Breakfast'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
                ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        '''Test creating a rcipe with existing tag'''

        tag_indian = Tag.objects.create(user=self.user, name='Indian')

        payload = {
            'title': 'samosha',
            'time_minutes': 20,
            'price': Decimal('20.5'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()

            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        '''Test creating tag when updating a recipe.'''

        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': 'Launch'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Launch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_aasign_tag(self):
        '''Test assigning an existing tag when updating a recipe'''

        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        '''Test clearing a recipe tags'''

        tag = Tag.objects.create(user=self.user, name='Desert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_crete_recipe_with_new_ingredients(self):
        '''Test creating a recipe with new ingredients'''

        payload = {
            'title': 'Samosa',
            'time_minutes': 20,
            'price': Decimal('10'),
            'ingredients': [
                {'name': 'potato'},
                {'name': 'pea'},
                {'name': 'spices'}
                ]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        '''Test creating a new recipe with existing ingredients.'''

        ingredient = Ingredients.objects.create(user=self.user, name='salt')
        payload = {
            'title': 'Samosa',
            'time_minutes': 20,
            'price': Decimal('10'),
            'ingredients': [
                {'name': 'potato'},
                {'name': 'pea'},
                {'name': 'salt'}
            ]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()

            self.assertTrue(exists)

    def test_create_ingredients_on_update(self):
        '''Test creating an ingredient'''

        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'sugar'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredients.objects.get(user=self.user, name='sugar')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        '''Test assigning an existing ingredient when updating a recipe'''

        ingredient1 = Ingredients.objects.create(user=self.user, name='salt')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredients.objects.create(user=self.user, name='pepper')
        payload = {'ingredients': [{'name': 'pepper'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        '''Test clering a recipe ingredients'''

        ingredient = Ingredients.objects.create(user=self.user, name='Garlic')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
