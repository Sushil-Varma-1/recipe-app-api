'''Test Tag API'''

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAG_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    '''Create and return tag detail url'''
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='testpass123'):
    '''Create and return a user'''
    return get_user_model().objects.create_user(email, password)


class PublicTagsApiTest(TestCase):
    '''Test unauthenticated API requests'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required for retrieving tags'''
        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    '''Test authenticated API requests'''

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        '''Test retrieving a list of tags'''

        Tag.objects.create(user=self.user, name='python')
        Tag.objects.create(user=self.user, name='django')

        res = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Test list of tags is limited to authenticated user'''
        user2 = create_user(email='user2@example.com', password='testpass123')
        Tag.objects.create(user=user2, name='jagga')
        tag = Tag.objects.create(user=self.user, name='jd')

        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        '''Test updating a tags'''

        tag = Tag.objects.create(user=self.user, name='high')
        payload = {'name': 'low'}

        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        '''Test deleting a Tag'''

        tag = Tag.objects.create(user=self.user, name='python')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())

    def test_filter_tags_assigned_to_recipes(self):
        '''Test listing tags to those assigned to recipes.'''

        tag1 = Tag.objects.create(user=self.user, name='Breakefast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')

        recipe = Recipe.objects.create(
            user=self.user,
            title='Eggs Benedict',
            time_minutes=50,
            price=Decimal('7.2')
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAG_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        '''Test filtered tags return a unique list.'''

        tag = Tag.objects.create(user=self.user, name='Breakefast')
        Tag.objects.create(user=self.user, name='Dinner')

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
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAG_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
