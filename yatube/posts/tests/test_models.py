from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    def test_post_long_and_short_text_str_info(self):
        """У модели Post метод __str__ выводит первые 15 символов."""

        text = 'Короткий пост'
        self.assertEqual(Post(text=text).__str__(), 'Короткий пост...')

        text = 'Не более 15 символов может уместиться в превью'
        self.assertEqual(Post(text=text).__str__(), 'Не более 15 сим...')

    def test_group_title_str_info(self):
        """У моделей метод __str__ выводит первые 15 символов."""
        group = Group.objects.create(slug="slug", title='title')
        self.assertEqual(str(group), 'title')
