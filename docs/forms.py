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


class ArticleCreateForm(forms.Form):
    """Комбинированная форма для создания статьи и первой версии"""
    # Поля из Article
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Как настроить Django проект'
        }),
        help_text='Придумайте понятный и информативный заголовок'
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Выберите категорию",
        help_text='Выберите соответствующую категорию'
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'data-placeholder': 'Выберите теги...'
        }),
        required=False,
        help_text='Выберите теги для статьи'
    )
    status = forms.ChoiceField(
        choices=[
            ('draft', 'Черновик'),
            ('published', 'Опубликовано'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Опубликованные статьи видны всем пользователям'
    )

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

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Для обычных пользователей ограничиваем статусы
        if self.request and not self.request.user.is_superuser:
            self.fields['status'].choices = [
                ('draft', 'Черновик'),
                ('published', 'Опубликовано'),
            ]


class ArticleUpdateForm(forms.Form):
    """Комбинированная форма для обновления статьи и создания новой версии"""
    # Поля из Article (метаданные)
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Выберите категорию"
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )
    status = forms.ChoiceField(
        choices=[
            ('draft', 'Черновик'),
            ('published', 'Опубликовано'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Поля из ArticleVersion (новая версия)
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
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

    def __init__(self, *args, **kwargs):
        # Убираем параметр instance, так как это обычная Form
        self.request = kwargs.pop('request', None)
        article = kwargs.pop('article', None)
        super().__init__(*args, **kwargs)

        # Для обычных пользователей ограничиваем статусы
        if self.request and not self.request.user.is_superuser:
            self.fields['status'].choices = [
                ('draft', 'Черновик'),
                ('published', 'Опубликовано'),
            ]

        # Если статья существует, предзаполняем поля
        if article:
            current_version = article.current_version
            if current_version:
                self.fields['title'].initial = current_version.title
                self.fields['content'].initial = current_version.content
                self.fields['excerpt'].initial = current_version.excerpt

            self.fields['category'].initial = article.category
            self.fields['tags'].initial = article.tags.all()
            self.fields['status'].initial = article.status


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