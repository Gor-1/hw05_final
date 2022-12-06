from django.contrib.auth import get_user_model
from posts.models import Post, Follow
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

User = get_user_model()


class FollowPostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user_1 = User.objects.create_user(username='Pushkin')
        cls.test_user_2 = User.objects.create_user(username='Mike')
        cls.test_user_3 = User.objects.create_user(username='Conor')
        cls.post = Post.objects.create(
            author=cls.test_user_1,
            text='Типо очень интересный пост!'
        )
        cls.follow = Follow.objects.create(
            author=cls.test_user_1,
            user=cls.test_user_2
        )

    def setUp(self):
        self.test_user_mike = Client()
        self.test_user_conor = Client()
        self.test_user_mike.force_login(self.test_user_2)
        self.test_user_conor.force_login(self.test_user_3)

    def test_following_authorized_user_views(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        """
        # создаем новый пост Pushkina
        Post.objects.create(
            author=self.test_user_1,
            text='Очень креативный пост'
        )

        # проверяем добавились ли данные в бд
        self.assertTrue(Post.objects.filter(
            author=self.test_user_1,
            text='Очень креативный пост').exists()
        )
        cache.clear()
        # проверяем что теперь в follow_index
        #  Mike видет посты Pushkin а Conor Нет
        response = self.test_user_mike.get('/follow/')
        self.assertContains(response, 'Очень креативный пост')
        # Conor
        cache.clear()
        response = self.test_user_conor.get('/follow/')
        self.assertNotContains(response, 'Очень креативный пост')

    def test_following_and_unfollowing(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        # тут Conor подпишется на Пушкина
        self.test_user_conor.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.test_user_1.username}
            )
        )
        # Проверяем что в таблицу Follower Добавились данные
        self.assertTrue(Follow.objects.filter(
            author=self.test_user_1,
            user=self.test_user_3).exists()
        )
        # теперь отпишемся
        self.test_user_conor.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.test_user_1.username}
            )
        )
        # и проверим что данные удалились из бд
        self.assertFalse(Follow.objects.filter(
            author=self.test_user_1,
            user=self.test_user_3).exists()
        )
