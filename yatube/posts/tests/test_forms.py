from django.test import Client, TestCase
from ..forms import PostForm
from ..models import Post, User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


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
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

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

    def test_create_post_with_image(self):
        """
        Создаётся ли запись в базе данных при отправке поста с картинкой.
        """
        form_data = {
            'text': 'текст',
            'image': self.image,
        }

        self.authorized_client.post(
            reverse("posts:create_post"), data=form_data, follow=True
        )

        self.assertEqual(Post.objects.count(), 2)

        # Создалась ли запись с картинкой
        self.assertTrue(
            Post.objects.filter(image=self.image).exists()
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

    def test_comment_post_can_only_authenticated_user(self):
        """Комментировать посты может только авторизованный пользователь."""
        self.client = Client()
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        )
        self.assertContains(
            response, 'Вы должны быть зарегистрированы', status_code=401)

        # self.client.login(username='testuser', password='testpass')
        # response = self.client.post(
        #     reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
        #     data={'text': 'текст комментария'}
        # )
        # self.assertEqual(response.status_code, 302)
        # self.assertEqual(Comment.objects.count(), 1)

    # def test_comment_appears_on_post_page(self):
    #     """Комментирование поста авторизованным пользователем"""
    #     self.client.login(
    #         username='testuser',
    #         password='testpass'
    #     )
    #     response = self.client.post(
    #         reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
    #         data={'text': 'текст комментария'}
    #     )

    #     # Проверка, что комментарий отображается на странице поста
    #     response = self.client.get(reverse
    #     ('posts:post_detail', kwargs={'post_id': self.post.id}))
    #     self.assertContains(response, 'текст комментария')
