from django import forms
from .models import Article, Category, Tag, ArticleVersion
from mdeditor.fields import MDTextFormField
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class ArticleForm(forms.ModelForm):
    """Форма для создания/редактирования статьи (метаданные)"""

    class Meta:
        model = Article
        fields = ['title', 'category', 'status', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Как настроить Django проект'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'data-placeholder': 'Выберите теги...'
            }),
        }
        help_texts = {
            'title': 'Придумайте понятный и информативный заголовок',
            'category': 'Выберите соответствующую категорию',
            'status': 'Опубликованные статьи видны всем пользователям',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Выберите категорию"
        self.fields['tags'].queryset = Tag.objects.all()

        # Ограничиваем выбор статуса для обычных пользователей
        if self.request and not self.request.user.is_superuser:
            self.fields['status'].choices = [
                ('draft', 'Черновик'),
                ('published', 'Опубликовано'),
            ]


class ArticleVersionForm(forms.ModelForm):
    """Форма для создания/редактирования версии статьи"""
    content = MDTextFormField(
        label='Содержание статьи',
        help_text='Используйте панель инструментов для форматирования текста.'
    )

    class Meta:
        model = ArticleVersion
        fields = ['title', 'content', 'excerpt', 'change_reason', 'is_draft']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок статьи'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание того, о чем эта статья...'
            }),
            'change_reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: исправление опечаток, добавление новой информации...'
            }),
            'is_draft': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'change_reason': 'Опишите, что было изменено в этой версии',
            'is_draft': 'Если отмечено, версия будет сохранена как черновик',
        }


class ArticleCreateForm(forms.ModelForm):
    """Комбинированная форма для создания статьи и первой версии"""
    # Поля из ArticleVersion
    content = MDTextFormField(
        label='Содержание статьи',
        help_text='Используйте панель инструментов для форматирования текста.'
    )
    excerpt = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Краткое описание того, о чем эта статья...'
        }),
        help_text='Необязательное поле. Кратко опишите содержание статьи'
    )
    change_reason = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: первоначальная версия статьи...'
        }),
        help_text='Опишите, что содержит эта версия'
    )

    # Поле для создания новых тегов
    new_tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mt-2',
            'placeholder': 'Введите новые теги через запятую...',
            'id': 'new-tags-input'
        }),
        help_text='🔸 Добавьте новые теги, разделяя их запятыми'
    )

    class Meta:
        model = Article
        fields = ['title', 'category', 'status', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Как настроить Django проект'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'data-placeholder': 'Выберите теги...',
                'id': 'tags-select'
            }),
        }
        help_texts = {
            'title': 'Придумайте понятный и информативный заголовок',
            'category': 'Выберите соответствующую категорию',
            'status': 'Опубликованные статьи видны всем пользователям',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Выберите категорию"
        self.fields['tags'].queryset = Tag.objects.all()

        # Для обычных пользователей ограничиваем статусы
        if self.request and not self.request.user.is_superuser:
            self.fields['status'].choices = [
                ('draft', 'Черновик'),
                ('published', 'Опубликовано'),
            ]

    def clean_new_tags(self):
        """Валидация новых тегов"""
        new_tags = self.cleaned_data.get('new_tags', '').strip()
        if not new_tags:
            return []

        tags_list = [tag.strip() for tag in new_tags.split(',') if tag.strip()]

        # Проверяем длину каждого тега
        for tag in tags_list:
            if len(tag) > 50:
                raise ValidationError(f'Тег "{tag}" слишком длинный (максимум 50 символов)')
            if len(tag) < 2:
                raise ValidationError(f'Тег "{tag}" слишком короткий (минимум 2 символа)')

        return tags_list

    def save(self, commit=True):
        """Сохраняем статью и создаем новые теги"""
        # Сохраняем статью сначала без тегов
        article = super().save(commit=False)

        if commit:
            article.save()

            # Сохраняем выбранные теги
            self.save_m2m()

            # Создаем и добавляем новые теги
            new_tags = self.cleaned_data.get('new_tags', [])
            created_tags = []
            for tag_name in new_tags:
                # Создаем slug для тега
                from django.utils.text import slugify
                tag_slug = slugify(tag_name)

                # Создаем или получаем тег
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': tag_slug}
                )
                article.tags.add(tag)
                if created:
                    created_tags.append(tag_name)

            # Сохраняем статью снова, чтобы обновить M2M
            article.save()

        return article

class ArticleUpdateForm(forms.ModelForm):
    """Комбинированная форма для обновления статьи и создания новой версии"""
    # Поля из ArticleVersion
    content = MDTextFormField(
        label='Содержание статьи'
    )
    excerpt = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        })
    )
    change_reason = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Опишите, что изменилось в этой версии...'
        })
    )

    class Meta:
        model = Article
        fields = ['category', 'status', 'tags']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Предзаполняем поля версии из текущей версии
        if self.instance and self.instance.current_version:
            current_version = self.instance.current_version
            self.fields['content'].initial = current_version.content
            self.fields['excerpt'].initial = current_version.excerpt

        # Для обычных пользователей ограничиваем статусы
        if self.request and not self.request.user.is_superuser:
            self.fields['status'].choices = [
                ('draft', 'Черновик'),
                ('published', 'Опубликовано'),
            ]


# UserRegisterForm остается без изменений
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Придумайте имя пользователя'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Это имя пользователя уже занято')
        return username
