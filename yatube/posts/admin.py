from django.contrib import admin
from .models import Post, Group, Comment


class PostAdmin(admin.ModelAdmin):
    # перчисляем поля которые должны отображаться в админке
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    # добавляем интерфейс для поиска по тексту постов
    list_editable = ('group',)
    search_fields = ('text',)
    # добавляем возможность филтряции по дате
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'text', 'created')
    list_filter = ('created',)
    search_fields = ('author', 'post', 'text')

# При регистрации модели Post источником конфигурации для неё назначаем
# класс PostAdmin


admin.site.register(Comment, CommentAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Group)
