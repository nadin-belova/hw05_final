from django.test import Client, TestCase, override_settings
from ..models import Post, User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
import tempfile
import shutil


settings.TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=settings.TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user("auth")
        cls.group = Group.objects.create(slug="slug")
        cls.image = SimpleUploadedFile(name='', content='')
        cls.post = Post.objects.create(
            author=cls.user,
            text="пост",
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            "text": self.post.text * 2,
            "goup": self.group,
        }

        self.authorized_client.post(
            reverse("posts:create_post"), data=form_data, follow=True
        )

        self.assertEqual(Post.objects.count(), 2)

        # Создалась ли запись с заданным текстом
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text * 2,
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {
            "text": self.post.text * 3,
            "goup": self.group,
        }

        # Отправляем POST-запрос
        self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        # Осталось ли число постов прежним
        self.assertEqual(Post.objects.count(), 1)

        # Создалась ли запись с заданным текстом
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text * 3,
            ).exists()
        )
