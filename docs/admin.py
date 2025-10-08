from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Article, Category, Tag, Comment, Rating, Favorite
from django.utils import timezone
from django import forms
from mdeditor.fields import MDTextFormField


# Форма для админки с MDEditor
class ArticleAdminForm(forms.ModelForm):
    content = MDTextFormField()

    class Meta:
        model = Article
        fields = '__all__'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'article_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def article_count(self, obj):
        return obj.article_count()

    article_count.short_description = 'Кол-во статей'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'article_count', 'created_at']
    list_filter = ['created_at', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']

    def article_count(self, obj):
        return obj.articles.count()

    article_count.short_description = 'Кол-во статей'

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'parent', 'description')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm  # ← используем нашу форму

    def comment_count(self, obj):
        return obj.get_comment_count()

    comment_count.short_description = 'Комментарии'

    def like_count(self, obj):
        return obj.get_like_count()

    like_count.short_description = '👍'

    def dislike_count(self, obj):
        return obj.get_dislike_count()

    dislike_count.short_description = '👎'

    # Добавляем в list_display
    list_display = ['title', 'author', 'category', 'status', 'view_count',
                    'comment_count', 'like_count', 'dislike_count',  # Добавляем счетчики
                    'created_at', 'published_at', 'preview_link']

    list_filter = ['status', 'category', 'tags', 'created_at', 'published_at']
    search_fields = ['title', 'content', 'excerpt', 'author__username', 'tags__name']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'view_count']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    filter_horizontal = ['tags']  # Удобный выбор тегов

    # Поля для отображения в форме
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'author', 'category', 'excerpt')
        }),
        ('Теги', {
            'fields': ('tags',)
        }),
        ('Содержание', {
            'fields': ('content',)
        }),
        ('Статус и видимость', {
            'fields': ('status', 'is_pinned', 'view_count')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )

    def preview_link(self, obj):
        if obj.status == 'published' and obj.slug:
            return format_html(
                '<a href="/articles/{}/" target="_blank" class="button">👁️ Просмотр</a>',
                obj.slug
            )
        return '—'

    preview_link.short_description = 'Предпросмотр'

    # Автозаполнение автора при создании статьи
    def save_model(self, request, obj, form, change):
        if not change:  # Если это создание новой статьи
            obj.author = request.user
        super().save_model(request, obj, form, change)

    # Ограничение прав для не-суперпользователей
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(author=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author" and not request.user.is_superuser:
            kwargs["queryset"] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    actions = ['make_published', 'make_draft', 'make_archived']

    def make_published(self, request, queryset):
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} статей опубликовано')

    make_published.short_description = 'Опубликовать выбранные статьи'

    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} статей перемещено в черновики')

    make_draft.short_description = 'В черновики'

    def make_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} статей архивировано')

    make_archived.short_description = 'Архивировать'


# Кастомная админка для пользователей (опционально)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'is_staff', 'article_count', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']

    def article_count(self, obj):
        return obj.articles.count()

    article_count.short_description = 'Статей'


# Перерегистрируем User с кастомной админкой
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Настройки админ-панели
admin.site.site_header = 'Панель управления Базой знаний'
admin.site.site_title = 'База знаний'
admin.site.index_title = 'Добро пожаловать в панель управления'


class PublishedFilter(admin.SimpleListFilter):
    title = 'Статус публикации'
    parameter_name = 'publish_status'

    def lookups(self, request, model_admin):
        return (
            ('published', 'Опубликованные'),
            ('unpublished', 'Неопубликованные'),
            ('recent', 'Опубликованные за последние 7 дней'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'published':
            return queryset.filter(status='published')
        elif self.value() == 'unpublished':
            return queryset.exclude(status='published')
        elif self.value() == 'recent':
            return queryset.filter(
                status='published',
                published_at__gte=timezone.now() - timezone.timedelta(days=7)
            )


# Админка для комментариев
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'article', 'content_preview', 'parent',
                    'is_approved', 'is_deleted', 'is_edited', 'created_at']
    list_filter = ['is_approved', 'is_deleted', 'is_edited', 'created_at', 'article']
    search_fields = ['content', 'author__username', 'article__title']
    list_editable = ['is_approved', 'is_deleted']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_comments', 'reject_comments', 'soft_delete_comments']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Текст'

    fieldsets = (
        ('Основная информация', {
            'fields': ('article', 'author', 'parent', 'content')
        }),
        ('Статус', {
            'fields': ('is_approved', 'is_deleted', 'is_edited')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} комментариев одобрено')

    approve_comments.short_description = 'Одобрить выбранные комментарии'

    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} комментариев отклонено')

    reject_comments.short_description = 'Отклонить выбранные комментарии'

    def soft_delete_comments(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} комментариев помечено как удаленные')

    soft_delete_comments.short_description = 'Пометить как удаленные'


# Админка для оценок
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'article', 'rating_type', 'created_at']
    list_filter = ['rating_type', 'created_at', 'article']
    search_fields = ['user__username', 'article__title']
    readonly_fields = ['created_at']

    def has_add_permission(self, request):
        return False  # Запрещаем ручное создание оценок


# Админка для избранного
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'article', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'article__title']
    readonly_fields = ['created_at']
