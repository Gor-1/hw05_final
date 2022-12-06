import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Post, Group, Comment
from posts.forms import PostForm, CommentForm
from django.conf import settings

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='UserName')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Создадим запись в БД для проверки доступности адресов
        cls.group = Group.objects.create(
            title='tmp_title',
            slug='tmp_slug',
            description='tmp_description'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='tmp_post_text',
            group=cls.group
        )
        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаём экземпляр клиента. Он авторизован.
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_form_create_and_edit_test(self, False)

    def test_edit_post(self):
        """Валидная форма изменит запись в Post."""
        post_form_create_and_edit_test(self, True)

    def test_image_create_post(self):
        """Валидная форма создаст запись с картинкой в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'New Тестовый текст',
            'group': self.group.pk,
            'image': self.uploaded
        }
        # Отправляем POST-запрос
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.author.username}
            )
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверяем, что создалась запись
        self.assertTrue(Post.objects.filter(
            author=self.author,
            group=self.group,
            text='New Тестовый текст',
            image='posts/small.gif').exists()
        )


def post_form_create_and_edit_test(self, edit):
    # подсчитаем кол_во постов
    post_count = Post.objects.count()
    text = 'New Тестовый текст'
    if edit:
        text = 'Измененный текст'

    form_data = {
        'group': self.group.pk,
        'text': text
    }

    if edit:
        # отправляем запрос
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ))
    else:
        post_count += 1
        # Отправляем POST-запрос
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.author.username}
            ))

    # Проверяем, увеличилось ли число постов
    self.assertEqual(Post.objects.count(), post_count)
    # Проверяем, что создалась запись
    self.assertTrue(
        Post.objects.filter(
            author=self.author,
            group=self.group,
            text=text,
        ).exists()
    )

    # Проверим, что ничего не упало и страница отдаёт код 200
    self.assertEqual(response.status_code, 200)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='UserName')
        # Создадим запись в БД для проверки доступности адресов
        cls.group = Group.objects.create(
            title='TestComment',
            slug='TestComentSlug',
            description='TestingComment'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='TmpPostForCommentTest',
            group=cls.group
        )
        # Создаем форму, если нужна проверка атрибутов
        cls.form = CommentForm()

    def setUp(self):
        # Создаём экземпляр клиента. Он авторизован.
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_comment(self):
        """
        Комментировать посты может только авторизованный пользователь,
        неавторизованный при попитке отправляется на сайт входа.
        """
        comments_count = Comment.objects.count()
        form_data = {'text': 'Test comments'}
        # Отправляем POST-запрос
        response = self.authorized_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Test comments').exists()
        )

        # тоже самая проверка от не авторизованного пользователья
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )
        # Проверяем что не увеличилось число постов
        self.assertEqual(Comment.objects.count(), comments_count + 1)
