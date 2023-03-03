from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

from http import HTTPStatus as hst


User = get_user_model()


class PostURLTests(TestCase):
    def setUp(self):
        self.user_auth = User.objects.create_user("auth")
        self.group = Group.objects.create(slug="slug")
        self.post = Post.objects.create(author=self.user_auth)

        self.user = User.objects.create_user("HasNoName")
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        # Авторизуем автора
        self.author_client.force_login(self.user_auth)

        self.clients = [
            self.guest_client,
            self.authorized_client,
            self.author_client
        ]

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        data = {
            "/": "posts/index.html",
            "/group/slug/": "posts/group_list.html",
            "/profile/auth/": "posts/profile.html",
            "/posts/1/": "posts/post_detail.html",
            "/posts/1/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
        }

        for address, template in data.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_accesses(self):
        """
        URL-адрес предоставляет корректные права доступа.
        Очерёдность проверки: неавторизованный, авторизованный, автор
        """

        data = {
            "/": [hst.OK, hst.OK, hst.OK],
            "/group/slug/": [hst.OK, hst.OK, hst.OK],
            "/profile/auth/": [hst.OK, hst.OK, hst.OK],
            "/posts/1/": [hst.OK, hst.OK, hst.OK],
            "/posts/1/edit/": [hst.FOUND, hst.FOUND, hst.OK],
            "/create/": [hst.FOUND, hst.OK, hst.OK],
            "/posts/1/comment/": [hst.FOUND, hst.FOUND, hst.FOUND],
        }

        for address, statuses in data.items():
            for status, client in zip(statuses, self.clients):
                with self.subTest(address=address, status=status):
                    response = client.get(address)
                    self.assertEqual(response.status_code, status)

    def test_urls_redirect(self):
        """
        URL-адрес корректно перенаправляет в зависимости от уровня доступа.
        Очерёдность проверки: неавторизованный, авторизованный, автор
        """

        data = {
            "/": ["", "", ""],
            "/group/slug/": ["", "", ""],
            "/profile/auth/": ["", "", ""],
            "/posts/1/": ["", "", ""],
            "/posts/1/edit/": [
                "/auth/login/?next=/posts/1/edit/",
                "/posts/1/",
                ""
            ],
            "/create/": ["/auth/login/?next=/create/", "", ""],
            "/posts/1/comment/": ["/auth/login/?next=/posts/1/comment/", "", ""],
        }

        for address, redirect_addresses in data.items():
            addrs_clnts_zip = zip(redirect_addresses, self.clients)
            for redirect_address, client in addrs_clnts_zip:
                message = dict(
                    address=address,
                    redirect_address=redirect_address
                )
                with self.subTest(message):
                    if redirect_address:
                        response = client.get(address)
                        self.assertRedirects(response, redirect_address)

    def test_404_page(self):
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, 404)
