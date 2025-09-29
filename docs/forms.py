from django import forms
from .models import Article, Category, Tag
from mdeditor.fields import MDTextFormField
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class ArticleForm(forms.ModelForm):
    content = MDTextFormField(
        label='Содержание статьи',
        help_text='Используйте панель инструментов для форматирования текста. Не нужно знать Markdown!'
    )

    # ДОБАВЛЯЕМ ПОЛЕ ТЕГОВ
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'data-placeholder': 'Выберите теги...'
        }),
        required=False,
        label='Теги'
    )

    class Meta:
        model = Article
        fields = ['title', 'content', 'excerpt', 'category', 'status']  # Добавили status обратно
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Как настроить Django проект'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание того, о чем эта статья...'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'title': 'Придумайте понятный и информативный заголовок',
            'excerpt': 'Необязательное поле. Кратко опишите содержание статьи',
            'category': 'Выберите соответствующую категорию',
            'status': 'Опубликованные статьи видны всем пользователям',
        }
        labels = {
            'status': 'Статус публикации',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Выберите категорию"

        # Ограничиваем выбор статуса для обычных пользователей
        if self.request and not self.request.user.is_superuser:
            self.fields['status'].choices = [
                ('draft', 'Черновик'),
                ('published', 'Опубликовано'),
            ]


class ArticleAdminForm(forms.ModelForm):
    """Форма для админки с полем статуса"""
    content = MDTextFormField()

    class Meta:
        model = Article
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()


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

