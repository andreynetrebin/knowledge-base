from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib.auth import views as auth_views
from .models import Article, Category, Tag, Comment, Favorite, ArticleVersion
from .forms import ArticleForm, ArticleCreateForm, ArticleUpdateForm, ArticleVersionForm
from .comments_forms import CommentForm
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth import logout


class ArticleListView(ListView):
    model = Article
    template_name = 'docs/articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        # Показываем только статьи с текущей версией
        return Article.objects.filter(
            status='published',
            current_version__isnull=False
        ).select_related('author', 'category', 'current_version')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['pinned_articles'] = Article.objects.filter(
            status='published',
            is_pinned=True,
            current_version__isnull=False
        )[:5]
        context['popular_tags'] = Tag.objects.annotate(
            num_articles=Count('articles')
        ).filter(num_articles__gt=0).order_by('-num_articles')[:20]
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'docs/articles/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        """Исправленный queryset без комбинирования уникальных и неуникальных запросов"""
        return Article.objects.filter(
            status='published'
        ).select_related(
            'author', 'category', 'current_version'
        ).prefetch_related(
            'tags', 'ratings', 'favorited_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        # Проверяем наличие текущей версии
        if not article.current_version:
            messages.error(self.request, 'Эта статья не имеет содержимого.')
            return context

        # Увеличиваем счетчик просмотров
        article.increment_view_count()

        # Конвертируем Markdown в HTML
        extensions = [
            FencedCodeExtension(),
            CodeHiliteExtension(css_class='codehilite', linenums=False)
        ]

        context['html_content'] = markdown.markdown(
            article.current_version.content,
            extensions=extensions,
            output_format='html5'
        )

        # Форма для комментариев
        context['comment_form'] = CommentForm()

        # Комментарии статьи
        context['comments'] = Comment.objects.filter(
            article=article,
            is_approved=True,
            is_deleted=False,
            parent__isnull=True
        ).select_related('author').prefetch_related('children').order_by('-created_at')

        # Информация об оценках пользователя
        if self.request.user.is_authenticated:
            try:
                context['user_rating'] = article.get_user_rating(self.request.user)
                context['is_favorite'] = Favorite.objects.filter(
                    user=self.request.user,
                    article=article
                ).exists()
            except Exception as e:
                context['user_rating'] = None
                context['is_favorite'] = False
                print(f"Error getting user rating/favorite: {e}")
        else:
            context['user_rating'] = None
            context['is_favorite'] = False

        # Статистика
        try:
            context['like_count'] = article.get_like_count()
            context['dislike_count'] = article.get_dislike_count()
            context['comment_count'] = article.get_comment_count()
        except Exception as e:
            context['like_count'] = 0
            context['dislike_count'] = 0
            context['comment_count'] = 0
            print(f"Error getting counts: {e}")

        # Похожие статьи (только с текущей версией)
        try:
            related_articles = Article.objects.filter(
                status='published',
                current_version__isnull=False,
                category=article.category
            ).exclude(id=article.id)[:4]

            tag_ids = article.tags.values_list('id', flat=True)
            if tag_ids:
                related_articles = related_articles.filter(
                    tags__id__in=tag_ids
                ).distinct()

            if related_articles.count() < 4:
                category_articles = Article.objects.filter(
                    category=article.category,
                    status='published',
                    current_version__isnull=False
                ).exclude(id=article.id)
                # Используем union вместо |
                from django.db.models import Q
                related_articles = related_articles.union(category_articles)[:4]

            context['related_articles'] = related_articles[:4]
        except Exception as e:
            context['related_articles'] = Article.objects.none()
            print(f"Error getting related articles: {e}")

        # Популярные теги для сайдбара
        try:
            context['popular_tags'] = Tag.objects.annotate(
                num_articles=Count('articles')
            ).filter(num_articles__gt=0).order_by('-num_articles')[:15]
        except Exception as e:
            context['popular_tags'] = Tag.objects.none()
            print(f"Error getting popular tags: {e}")

        return context

    def get(self, request, *args, **kwargs):
        """Переопределяем get для проверки наличия текущей версии"""
        try:
            self.object = self.get_object()

            # Если нет текущей версии и пользователь - автор, предлагаем создать
            if not self.object.current_version and self.object.author == request.user:
                messages.warning(
                    request,
                    'У этой статьи нет содержимого. Перейдите к редактированию, чтобы создать первую версию.'
                )
                return redirect('docs:edit_article', slug=self.object.slug)
            elif not self.object.current_version:
                messages.error(request, 'Эта статья временно недоступна.')
                return redirect('docs:article_list')

            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        except Exception as e:
            messages.error(request, 'Произошла ошибка при загрузке статьи.')
            print(f"Error in ArticleDetailView: {e}")
            return redirect('docs:article_list')


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    template_name = 'docs/articles/article_form.html'
    form_class = ArticleCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # Устанавливаем автора перед сохранением
        article = form.save(commit=False)
        article.author = self.request.user

        # Сохраняем статью (это вызовет метод save() формы)
        article = form.save()

        # Создаем первую версию
        version = ArticleVersion(
            article=article,
            title=form.cleaned_data['title'],
            content=form.cleaned_data['content'],
            excerpt=form.cleaned_data['excerpt'],
            author=self.request.user,
            change_reason=form.cleaned_data['change_reason'] or 'Первоначальная версия'
        )
        version.save()

        # Устанавливаем как текущую версию
        article.current_version = version
        article.save()

        # Показываем сообщение о созданных тегах
        new_tags = form.cleaned_data.get('new_tags', [])
        if new_tags:
            messages.success(
                self.request,
                f'Статья создана! Добавлены новые теги: {", ".join(new_tags)}'
            )
        else:
            if article.status == 'published':
                messages.success(self.request, 'Статья успешно создана и опубликована!')
            else:
                messages.success(self.request, 'Статья успешно сохранена как черновик!')

        return redirect('docs:article_detail', slug=article.slug)


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    template_name = 'docs/articles/article_form.html'
    form_class = ArticleUpdateForm

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование: {self.object.title}'
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        article = self.object

        # Сохраняем метаданные статьи
        article = form.save()

        # Проверяем, нужно ли создавать новую версию
        current_version = article.current_version
        needs_new_version = (
                not current_version or
                form.cleaned_data['content'] != current_version.content or
                form.cleaned_data['excerpt'] != current_version.excerpt
        )

        if needs_new_version:
            # Создаем новую версию
            new_version = ArticleVersion(
                article=article,
                title=article.title,  # Заголовок берем из статьи
                content=form.cleaned_data['content'],
                excerpt=form.cleaned_data['excerpt'],
                author=self.request.user,
                change_reason=form.cleaned_data.get('change_reason', 'Обновление статьи')
            )
            new_version.save()

            # Устанавливаем новую версию как текущую
            article.current_version = new_version
            article.save()

            if current_version:
                messages.success(self.request, f'Статья обновлена! Создана версия v{new_version.version_number}')
            else:
                messages.success(self.request, 'Содержимое статьи добавлено!')
        else:
            messages.success(self.request, 'Метаданные статьи обновлены!')

        return redirect('docs:article_detail', slug=article.slug)


class TagArticlesView(ListView):
    model = Article
    template_name = 'docs/articles/tag_articles.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return Article.objects.filter(
            tags=self.tag,
            status='published',
            current_version__isnull=False
        ).select_related('author', 'category', 'current_version').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['categories'] = Category.objects.all()
        context['popular_tags'] = Tag.objects.annotate(
            num_articles=Count('articles')
        ).filter(num_articles__gt=0).order_by('-num_articles')[:15]
        return context


class CategoryArticlesView(ListView):
    model = Article
    template_name = 'docs/articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Article.objects.filter(
            category=self.category,
            status='published',
            current_version__isnull=False
        ).select_related('author', 'category', 'current_version').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.all()
        context['popular_tags'] = Tag.objects.annotate(
            num_articles=Count('articles')
        ).filter(num_articles__gt=0).order_by('-num_articles')[:15]
        return context


def tag_cloud(request):
    """Облако тегов"""
    tags = Tag.objects.annotate(
        num_articles=Count('articles')
    ).filter(num_articles__gt=0).order_by('-num_articles')

    return render(request, 'docs/tags/tag_cloud.html', {
        'tags': tags,
        'categories': Category.objects.all(),
        'popular_tags': tags[:15]
    })


class SearchView(ListView):
    model = Article
    template_name = 'docs/articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            return Article.objects.filter(
                Q(title__icontains=query) |
                Q(current_version__content__icontains=query) |
                Q(current_version__excerpt__icontains=query),
                status='published',
                current_version__isnull=False
            ).select_related('author', 'category', 'current_version')
        return Article.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['categories'] = Category.objects.all()
        return context


# Аутентификация
class LoginView(auth_views.LoginView):
    template_name = 'docs/auth/login.html'


def logout_view(request):
    """Представление для выхода из системы"""
    if request.method == 'POST':
        logout(request)
        return redirect('docs:login')
    else:
        return render(request, 'docs/auth/logout_confirm.html')


def register_view(request):
    """Представление для регистрации новых пользователей"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Аккаунт успешно создан! Добро пожаловать!')
            return redirect('docs:article_list')
    else:
        form = UserRegisterForm()

    return render(request, 'docs/auth/register.html', {'form': form})


def formatting_help(request):
    """Страница помощи по форматированию"""
    return render(request, 'docs/formatting_help.html')
