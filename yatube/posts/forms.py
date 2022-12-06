from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        label = {'text': 'Введите текст', 'group': 'Выберите группу'}
        help_text = {
            'text': 'Пост который хотите добавить или редактировать',
            'group': 'Из уже существующих'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
