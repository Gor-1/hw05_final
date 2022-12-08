
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.urls import reverse_lazy
from .models import Post, Group, User, Comment, Follow
from .constants import PUB_VALUE

# cache для разработкы
# from django.views.decorators.cache import cache_page


def page_list(request, post_list):
    # Показывать по 10 записей на странице.
    paginator = Paginator(post_list, PUB_VALUE)

    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')

    # Получаем набор записей для страницы с запрошенным номером
    return paginator.get_page(page_number)


# @cache_page(timeout=20, key_prefix='index_page')
def index(request):
    # в переменную posts будет сохранена выборка из 10 объектов модели Post,
    # отсортированных по полю pub_date по убыванию
    post_list = Post.objects.select_related()
    page_obj = page_list(request, post_list)
    # Отдаем в словаре контекста
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group_list.all()

    page_obj = page_list(request, post_list)

    context = {
        'text': slug,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):

    # Здесь код запроса к модели и создание словаря контекста
    author = get_object_or_404(User, username=username)
    posts_author = Post.objects.filter(author=author)
    is_my_profile = False
    following = False
    if request.user.is_authenticated:
        # проверяем пользователь в своем профыле
        if request.user.username == username:
            is_my_profile = True
        # проверяем подписан ли пользователь
        if Follow.objects.filter(author=author, user=request.user).exists():
            following = True

    page_obj = page_list(request, posts_author)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
        'is_my_profile': is_my_profile,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    # Здесь код запроса к модели и создание словаря контекста
    post = get_object_or_404(Post, id=post_id)
    form_comment = CommentForm()
    comments = Comment.objects.filter(post__comments__author=post_id)
    context = {
        'post': post,
        'count_posts': post.author.posts.count(),
        'comments': comments,
        'form': form_comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == "POST":
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.author = request.user
            new_form.save()
            return redirect('posts:profile', request.user)
        form = PostForm()
    context = {'form': form,
               }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    edited_post = get_object_or_404(Post, id=post_id)
    if request.user == edited_post.author:
        if request.method == 'POST':
            form = PostForm(
                request.POST or None,
                files=request.FILES or None,
                instance=edited_post
            )
            context = {
                'form': form,
                'is_edit': True,
            }
            if form.is_valid():
                form.save()
                return redirect(
                    reverse_lazy(
                        'posts:post_detail',
                        kwargs={'post_id': post_id}
                    )
                )
            return render(request, 'posts/create_post.html', context)
        form = PostForm(request.POST or None, instance=edited_post)
        context = {
            'form': form,
            'is_edit': True,
        }
        return render(request, 'posts/create_post.html', context)
    return redirect(
        reverse_lazy(
            'posts:post_detail',
            kwargs={'post_id': post_id}
        )
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # здесь выводим посты авторов, на которых подписан текущий пользователь.
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = page_list(request, post_list)
    # Отдаем в словаре контекста
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # подписаться на автора
    author = get_object_or_404(User, username=username)
    # это на всяки случаи если захочет подписаться на себя каким то образом
    # и проверяем подписан ли пользователь
    if Follow.objects.filter(author=author, user=request.user).exists() or (
        request.user.username == username
    ):
        return redirect('posts:profile', username=username)
    follow_record = Follow(user=request.user, author=author)
    follow_record.save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(requst, username):
    # отписаться от автора
    author = get_object_or_404(User, username=username)
    unfollow_db = Follow.objects.filter(author=author, user=requst.user)
    # проверяем подписан ли пользователь
    if unfollow_db.exists():
        unfollow_db.delete()
    return redirect('posts:profile', username=username)
