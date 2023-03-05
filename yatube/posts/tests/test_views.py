from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import PostForm

from ..models import Comment, Group, Post

from django.core.cache import cache


User = get_user_model()


class PostPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("auth")
        self.group = Group.objects.create(
            title="группа",
            slug="slug",
            description="описание",
        )

        self.post = Post.objects.create(
            author=self.user,
            text="пост",
            group=self.group,
        )

        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
        )
        self.comment.post = self.post

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        cache.clear()

    def test_pages_use_template_by_url_name(self):
        """Корректен ли адрес 'name' функции path() и формируемой по
        этому адресу странице html"""

        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            reverse('posts:create_post'),
        ]

        templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
        ]

        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_page_contains_single_post(self):
        """
        На главной странице пользователь __точно__
        увидит единственный пост (создаём в "setUp").
        """
        response = self.authorized_client.get(reverse("posts:index"))
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.group.slug, self.group.slug)
        self.assertEqual(
            first_object.group.description, self.group.description
        )

        self.assertEqual(
            first_object.author.username,
            self.post.author.get_username()
        )
        self.assertEqual(first_object.text, self.post.text)

    def test_group_list_contains_posts_filtered_by_group(self):
        """
        Context страницы /group_list содержит список постов
        отфильтрованных по группе
        """
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        first_object = response.context["page_obj"][0]

        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.group.slug, self.group.slug)
        self.assertEqual(
            first_object.group.description,
            self.group.description
        )

        self.assertEqual(
            first_object.author.username,
            self.post.author.get_username()
        )
        self.assertEqual(first_object.text, self.post.text)

        self.group_2 = Group.objects.create(
            title="группа 2",
            slug="slug_2",
            description="описание группы 2",
        )

        self.post_2 = Post.objects.create(
            author=self.user,
            text="пост 2",
            group=self.group_2,
        )

        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group_2.slug})
        )
        self.assertEqual(
            response.context["page_obj"][0].text,
            self.post_2.text
        )

    def test_profile_page_contains_posts_filtered_by_user(self):
        """
        Context страницы /profile содержит список постов
        отфильтрованных по пользователю
        """
        response = self.authorized_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": self.user.get_username()}
            )
        )
        first_object = response.context["page_obj"][0]

        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.group.slug, self.group.slug)
        self.assertEqual(
            first_object.group.description,
            self.group.description
        )

        self.assertEqual(
            first_object.author.username,
            self.post.author.get_username()
        )
        self.assertEqual(first_object.text, self.post.text)

        self.user_2 = User.objects.create_user('user_2')

        self.post_2 = Post.objects.create(
            author=self.user_2,
            text="пост 2",
        )

        response = self.authorized_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": self.user_2.get_username()}
            )
        )
        self.assertEqual(
            response.context["page_obj"][0].text,
            self.post_2.text
        )

    def test_post_detail_contains_single_post(self):
        """
        Context страницы /post_detail содержит один пост
        отфильтрованный по id
        """
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        post = response.context["post"]

        self.assertEqual(post.group.title, self.group.title)
        self.assertEqual(post.group.slug, self.group.slug)
        self.assertEqual(post.group.description, self.group.description)
        self.assertEqual(post.author.username, self.post.author.get_username())
        self.assertEqual(post.text, self.post.text)

        count = response.context["post_count"]
        self.assertEqual(count, 1)

    def test_edit_post_page_contains_edit_post_form(self):
        """
        Context страницы /create_post
        содержит форму редактирования поста отфильтрованного по id
        """
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )

        form = response.context["form"]
        self.assertIsInstance(form, PostForm)

        is_edit = response.context["is_edit"]
        self.assertEqual(is_edit, True)

        post_id = response.context["post_id"]
        self.assertEqual(post_id, 1)

    def test_create_post_page_contains_create_post_form(self):
        """
        Context страницы /create_post содержит форму создания поста
        """
        response = self.authorized_client.get(reverse("posts:create_post"))

        form = response.context["form"]
        self.assertIsInstance(form, PostForm)

    def test_add_comment_post_detail_contains_one_comment(self):
        """
        Context страницы /post_detail содержит один коментарий
        """

        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )

        first_comment = response.context["comments"][0]
        self.assertEqual(first_comment, self.comment)


class PaginatorViewsTest(TestCase):
    ALL_POSTS_COUNT = 12
    FIRST_PAGE_POSTS_COUNT = 10
    SECOND_PAGE_POSTS_COUNT = ALL_POSTS_COUNT - FIRST_PAGE_POSTS_COUNT
    PAGE_ID = 2

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user("auth")

        cls.group = Group.objects.create(
            title="группа",
            slug="slug",
            description="описание",
        )

        cls.posts = []
        for _ in range(cls.ALL_POSTS_COUNT):
            post = Post.objects.create(
                author=cls.user,
                text="пост",
                group=cls.group,
            )
            cls.posts.append(post)

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

        cache.clear()

    def __test_paginator(self, reverse_name: str, kwargs=None):
        response = self.authorized_client.get(
            reverse(reverse_name, kwargs=kwargs) + f"?page={self.PAGE_ID}"
        )
        self.assertEqual(
            len(response.context["page_obj"]), self.SECOND_PAGE_POSTS_COUNT
        )

        response = self.authorized_client.get(reverse(reverse_name, kwargs=kwargs))
        self.assertEqual(
            len(response.context["page_obj"]),
            self.FIRST_PAGE_POSTS_COUNT
        )

    def test_index_paginator(self):
        self.__test_paginator("posts:index")

    def test_group_list_paginator(self):
        self.__test_paginator(
            "posts:group_list",
            kwargs={"slug": self.group.slug}
        )

    def test_profile_paginator(self):
        self.__test_paginator(
            "posts:profile", kwargs={"username": self.user.get_username()}
        )


class ImagePostPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("auth")
        self.group = Group.objects.create(
            slug="slug",
        )
        uploaded = SimpleUploadedFile(name='', content='')

        self.post = Post.objects.create(
            author=self.user,
            group=self.group,
            image=uploaded,
        )

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        cache.clear()

    def test_index_page_contains_single_post_with_image(self):
        """
        На главной странице пользователь __точно__
        увидит единственный пост с картинкой (создаём в setUp).
        """
        response = self.authorized_client.get(reverse("posts:index"))
        first_object = response.context["page_obj"][0]

        self.assertEqual(first_object.image, self.post.image)

    def test_profile_page_contains_single_post_with_image(self):
        """
        На странице профиля пользователь __точно__
        увидит единственный пост с картинкой (создаём в setUp).
        """
        response = self.authorized_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": self.user.get_username()}
            ))
        first_object = response.context["page_obj"][0]

        self.assertEqual(first_object.image, self.post.image)

    def test_group_list_page_contains_single_post_with_image(self):
        """
        На странице группы пользователь __точно__
        увидит единственный пост с картинкой (создаём в setUp).
        """
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        first_object = response.context["page_obj"][0]

        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_contains_single_post_with_image(self):
        """
        На странице поста пользователь __точно__
        увидит единственный пост с картинкой (создаём в setUp).
        """
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        post = response.context["post"]

        self.assertEqual(post.image, self.post.image)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author')

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.post = Post.objects.create(
            author=cls.author,
        )

    def setUp(self):
        cache.clear()

    def test_index_page_cache(self):
        """
        Проверяем, что на главной странице используется кеш.
        """
        post = Post.objects.create(
            author=self.author,
        )

        response_predelete = self.client.get(reverse('posts:index'))
        post.delete()
        response_afterdelete = self.client.get(reverse('posts:index'))
        self.assertEqual(response_predelete.content,
                         response_afterdelete.content)

        cache.clear()
        response_after_clear_cash = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response_afterdelete.content,
                            response_after_clear_cash.content)


class FolowingTests(TestCase):
    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

        cache.clear()

    