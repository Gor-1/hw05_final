# Здесь будем тестировать работаспособность кэша
from django.core.cache import cache
from posts.models import Post, Group
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
User = get_user_model()


class CachePageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='CacheUser')

        cls.group = Group.objects.create(
            title='tmp_title',
            slug='tmp_slug',
            description='tmp_description'
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='cache_post_test',
            group=cls.group
        )

    def setUp(self):

        # Создаем неавторизованного клиента
        self.guest_client = Client()

    def test_index_cache(self):
        """ Проверяет работаспособность кэша на странице Index.html"""
        # сделаем запрс к index
        response = self.guest_client.get(
            reverse('posts:index')
        )
        # убеждаемся что этот пост который будем удалит существует
        self.assertContains(response, 'cache_post_test')
        # удяляем пост с бд
        Post.objects.filter(text='cache_post_test').delete()
        # убеждаемся что пост удален
        self.assertEqual(Post.objects.count(), 0)
        # снова делам запрос к index
        response = self.guest_client.get(
            reverse('posts:index')
        )
        # и получаем положительный результат что и значит что кэш работает
        self.assertContains(response, 'cache_post_test')
        # удаляем кэш
        cache.clear()
        # снова делаем запрос после удаления кэша
        # снова делам запрос к index
        response = self.guest_client.get(
            reverse('posts:index')
        )
        # Убеждаемся что пост после удаления кэша не появился на странице
        self.assertNotContains(response, 'cache_post_test')
