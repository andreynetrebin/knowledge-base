from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from mdeditor.fields import MDTextField
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid


class Tag(models.Model):
    """Модель для тегов статей"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='URL-тег')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('docs:tag_articles', kwargs={'slug': self.slug})

    def article_count(self):
        return self.articles.filter(status='published').count()


class Category(MPTTModel):
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Описание")
    parent = TreeForeignKey('self', on_delete=models.CASCADE,
                            null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('docs:category_articles', kwargs={'slug': self.slug})


class Article(models.Model):
    """Основная модель статьи (метаданные)"""
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, verbose_name="URL")

    # Связь с текущей версией
    current_version = models.ForeignKey(
        'ArticleVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_for_article',
        verbose_name="Текущая версия"
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name="Автор"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name="Категория"
    )

    # ОБНОВЛЕННЫЕ СТАТУСЫ
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('private', 'Приватный'),
        ('published', 'Опубликовано'),
        ('archived', 'В архиве'),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )

    # # НОВОЕ ПОЛЕ - ВИДИМОСТЬ СТАТЬИ
    # VISIBILITY_CHOICES = [
    #     ('public', 'Публичная'),
    #     ('private', 'Приватная'),
    # ]
    # visibility = models.CharField(
    #     max_length=10,
    #     choices=VISIBILITY_CHOICES,
    #     default='public',
    #     verbose_name="Видимость"
    # )

    view_count = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    is_pinned = models.BooleanField(default=False, verbose_name="Закреплено")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Опубликовано")

    tags = models.ManyToManyField(Tag, blank=True, related_name='articles', verbose_name='Теги')

    comments = models.ManyToManyField(
        User,
        through='Comment',
        through_fields=('article', 'author'),
        related_name='article_comments'
    )

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            if Article.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{uuid.uuid4().hex[:8]}"

        # Устанавливаем published_at только для опубликованных статей
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status != 'published':
            self.published_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('docs:article_detail', kwargs={'slug': self.slug})

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_comment_count(self):
        """Количество комментариев к статье"""
        try:
            return self.comments_article.filter(
                is_approved=True,
                is_deleted=False
            ).count()
        except Exception as e:
            print(f"Error getting comment count: {e}")
            return 0

    def get_like_count(self):
        """Количество лайков статьи"""
        try:
            return self.ratings.filter(rating_type='like').count()
        except Exception as e:
            print(f"Error getting like count: {e}")
            return 0

    def get_dislike_count(self):
        """Количество дизлайков статьи"""
        try:
            return self.ratings.filter(rating_type='dislike').count()
        except Exception as e:
            print(f"Error getting dislike count: {e}")
            return 0

    def get_user_rating(self, user):
        """Рейтинг пользователя для этой статьи"""
        if user.is_authenticated:
            try:
                rating = self.ratings.filter(user=user).first()
                return rating.rating_type if rating else None
            except Exception as e:
                print(f"Error getting user rating: {e}")
                return None
        return None

    def get_status_badge_class(self):
        """Возвращает класс CSS для бейджа статуса"""
        status_classes = {
            'published': 'bg-success',
            'draft': 'bg-warning',
            'archived': 'bg-secondary',
        }
        return status_classes.get(self.status, 'bg-secondary')

    def get_status_icon(self):
        """Возвращает иконку для статуса"""
        status_icons = {
            'published': 'bi-eye',
            'draft': 'bi-file-earmark',
            'archived': 'bi-archive',
        }
        return status_icons.get(self.status, 'bi-question')

    def is_accessible_by(self, user):
        """Проверяет, может ли пользователь просматривать статью"""
        # Автор всегда видит все свои статьи
        if user.is_authenticated and user == self.author:
            return True

        # Другие пользователи видят только опубликованные статьи
        if self.status == 'published':
            return True

        return False

    def get_status_badge_class(self):
        """Возвращает класс CSS для бейджа статуса"""
        status_classes = {
            'published': 'bg-success',
            'private': 'bg-info',
            'draft': 'bg-warning',
            'archived': 'bg-secondary',
        }
        return status_classes.get(self.status, 'bg-secondary')

    def get_status_icon(self):
        """Возвращает иконку для статуса"""
        status_icons = {
            'published': 'bi-eye',
            'private': 'bi-lock',
            'draft': 'bi-file-earmark',
            'archived': 'bi-archive',
        }
        return status_icons.get(self.status, 'bi-question')

    def get_status_description(self):
        """Возвращает описание статуса"""
        status_descriptions = {
            'published': 'Видна всем пользователям',
            'private': 'Видна только вам',
            'draft': 'Видна только вам (в разработке)',
            'archived': 'Видна только вам (скрыта)',
        }
        return status_descriptions.get(self.status, 'Неизвестный статус')

    @property
    def content(self):
        """Для обратной совместимости - возвращает контент текущей версии"""
        if self.current_version:
            return self.current_version.content
        return ""

    @property
    def excerpt(self):
        """Для обратной совместимости - возвращает описание текущей версии"""
        if self.current_version:
            return self.current_version.excerpt
        return ""


class ArticleVersion(models.Model):
    """Модель версии статьи"""
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='versions'
    )

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = MDTextField(verbose_name="Содержание")
    excerpt = models.TextField(blank=True, verbose_name="Краткое описание")

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор версии"
    )

    version_number = models.PositiveIntegerField(default=1, verbose_name="Номер версии")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания версии")

    change_reason = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Причина изменений"
    )

    is_draft = models.BooleanField(default=False, verbose_name="Черновик версии")

    class Meta:
        verbose_name = "Версия статьи"
        verbose_name_plural = "Версии статей"
        ordering = ['-version_number']
        unique_together = ['article', 'version_number']

    def save(self, *args, **kwargs):
        if not self.pk:
            # Автоматически определяем номер версии
            last_version = ArticleVersion.objects.filter(
                article=self.article
            ).order_by('-version_number').first()
            self.version_number = last_version.version_number + 1 if last_version else 1

        # Сохраняем версию
        super().save(*args, **kwargs)

        # Устанавливаем как текущую версию только если это первая версия
        # и статья еще не имеет текущей версии
        if (self.version_number == 1 and
                hasattr(self.article, 'current_version') and
                self.article.current_version is None):
            Article.objects.filter(id=self.article.id).update(current_version=self)

    def __str__(self):
        return f"{self.article.title} v{self.version_number}"

    def get_absolute_url(self):
        return reverse('docs:version_detail', kwargs={
            'slug': self.article.slug,
            'version_id': self.id
        })


class Comment(MPTTModel):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments_article',
        verbose_name='Статья'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments_authored',
        verbose_name='Автор'
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительский комментарий'
    )
    content = models.TextField(max_length=1000, verbose_name='Текст комментария')
    is_edited = models.BooleanField(default=False, verbose_name='Редактировался')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    # Модерация
    is_approved = models.BooleanField(default=True, verbose_name='Одобрен')
    is_deleted = models.BooleanField(default=False, verbose_name='Удален')

    class MPTTMeta:
        order_insertion_by = ['created_at']

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'is_approved', 'is_deleted']),
            models.Index(fields=['author', 'created_at']),
        ]

    def __str__(self):
        return f'Комментарий от {self.author.username} к "{self.article.title}"'

    def save(self, *args, **kwargs):
        if self.pk:
            self.is_edited = True
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{self.article.get_absolute_url()}#comment-{self.pk}"

    def can_edit(self):
        """Может ли текущий пользователь редактировать комментарий"""
        from django.contrib.auth.models import AnonymousUser
        # Получаем пользователя из контекста запроса
        # В реальном приложении нужно передавать user как параметр или использовать другой подход
        return False  # Временно возвращаем False

    def can_delete(self):
        """Может ли текущий пользователь удалить комментарий"""
        from django.contrib.auth.models import AnonymousUser
        # Получаем пользователя из контекста запроса
        return False  # Временно возвращаем False

    # Альтернативный подход - свойства
    @property
    def editable_by_current_user(self):
        """Свойство для проверки прав редактирования"""
        # Здесь нужен доступ к request.user, что сложно в моделях
        return False

    @property
    def deletable_by_current_user(self):
        """Свойство для проверки прав удаления"""
        return False


# МОДЕЛЬ ОЦЕНОК (ЛАЙКИ/ДИЗЛАЙКИ)
class Rating(models.Model):
    RATING_TYPES = [
        ('like', '👍 Нравится'),
        ('dislike', '👎 Не нравится'),
    ]

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Статья'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings_given',
        verbose_name='Пользователь'
    )
    rating_type = models.CharField(
        max_length=10,
        choices=RATING_TYPES,
        verbose_name='Тип оценки'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата оценки')

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        unique_together = ['article', 'user']  # Один пользователь - одна оценка на статью
        indexes = [
            models.Index(fields=['article', 'rating_type']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.get_rating_type_display()} - {self.article.title}'

    def clean(self):
        """Валидация - пользователь не может оценивать свои статьи"""
        if self.article.author == self.user:
            raise ValidationError('Вы не можете оценивать свои собственные статьи')


# МОДЕЛЬ ИЗБРАННЫХ СТАТЕЙ
class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Статья'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        unique_together = ['user', 'article']  # Одна статья может быть в избранном у пользователя только один раз
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.article.title}'


class ArticleExport(models.Model):
    """Модель для отслеживания экспорта статей"""
    FORMAT_CHOICES = [
        ('html', 'HTML'),
        ('pdf', 'PDF'),
        ('txt', 'Plain Text'),
    ]

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='exports',
        verbose_name='Статья'
    )
    export_format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        verbose_name='Формат экспорта'
    )
    exported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Экспортировал'
    )
    exported_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата экспорта')
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name='Размер файла')

    class Meta:
        verbose_name = 'Экспорт статьи'
        verbose_name_plural = 'Экспорты статей'
        ordering = ['-exported_at']

    def __str__(self):
        return f'{self.article.title} - {self.get_export_format_display()}'
