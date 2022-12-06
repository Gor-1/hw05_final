# Тесты адресов
# posts/tests/test_urls.py
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адресов
        cls.user = User.objects.create_user(username='User')
        cls.not_author_user = User.objects.create_user(
            username='Not_authorUser'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='tmpslug',
            description='Тестовое опысание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для тестов',
            group=cls.group
        )

    def setUp(self):
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()
        # создаем второго клиента и авторизуем пользователя
        self.authorized_client = Client()
        self.authorized_not_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_not_author.force_login(self.not_author_user)

    def test_urls_authorized(self):
        """
        URL-адрес использует соответствующий шаблон.
        доступность всех URL приложения для авторизованного пользователя:
        """
        # Шаблоны по адресам
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/tmpslug/',
            'posts/profile.html': '/profile/User/',
            'posts/post_detail.html': '/posts/1/',
            'posts/create_post.html': '/create/'
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_guest(self):
        """
        доступность всех URL приложения для неавторизованного пользователя:
        """
        # Шаблоны по адресам к которым имеет доступ неавторизованный
        templates_url_names = [
            '/',
            '/group/tmpslug/',
            f'/profile/{self.user.username}/',
            '/posts/1/'
        ]
        for template in templates_url_names:
            response = self.guest_client.get(template)
            self.assertEqual(response.status_code, 200)

        # проверяем что запрос к несуществующей странице вернёт ошибку 404
        response = self.guest_client.get('/notpage/')
        self.assertEqual(response.status_code, 404)

    def test_rendering_no_access(self):
        # проверям что гость не сможет добавить пост
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, 302)

        # проверяем Redirect неавторизованного пользователья
        # при попитке отредактировать пост на страницу входа
        response = self.guest_client.get(
            '/posts/1/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

        # Проверяем что другой зареганий пользовател не может
        # редактировать чужой пост
        response = self.authorized_not_author.get(
            '/posts/1/edit/',
            follow=True
        )
        self.assertRedirects(response, '/posts/1/')
