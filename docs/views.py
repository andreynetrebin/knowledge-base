from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views

from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth import logout

from .models import Article, Category, Tag, Comment, Favorite, ArticleVersion
from .forms import ArticleForm, ArticleCreateForm, ArticleUpdateForm, ArticleVersionForm
from .comments_forms import CommentForm
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from .forms import UserRegisterForm


class ArticleListView(ListView):
    model = Article
    template_name = 'docs/articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        """Возвращаем статьи с учетом прав доступа пользователя"""
        user = self.request.user

        # Базовый запрос - опубликованные статьи
        queryset = Article.objects.filter(
            status='published',
            current_version__isnull=False
        )

        # Если пользователь авторизован, добавляем его приватные статьи
        if user.is_authenticated:
            # Объединяем опубликованные статьи и приватные статьи пользователя
            from django.db.models import Q
            queryset = Article.objects.filter(
                Q(status='published') |
                Q(status='private', author=user) |
                Q(status='draft', author=user)
            ).filter(
                current_version__isnull=False
            )

        return queryset.select_related('author', 'category', 'current_version')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['categories'] = Category.objects.all()
        context['pinned_articles'] = Article.objects.filter(
            status='published',
            is_pinned=True,
            current_version__isnull=False
        )[:5]

        # Популярные теги (только для опубликованных статей)
        context['popular_tags'] = Tag.objects.annotate(
            num_articles=Count('articles')
        ).filter(num_articles__gt=0).order_by('-num_articles')[:20]

        # Добавляем информацию о пользователе для шаблона
        context['current_user'] = user

        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'docs/articles/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        """Возвращаем queryset с учетом прав доступа"""
        # Базовый queryset - все статьи
        queryset = Article.objects.all()
        return queryset

    def dispatch(self, request, *args, **kwargs):
        """Проверяем доступ к статье перед отображением"""
        try:
            article = self.get_object()

            # Проверяем доступ к статье
            if not article.is_accessible_by(request.user):
                if article.status == 'draft':
                    messages.error(request, 'Эта статья находится в черновиках и доступна только автору.')
                elif article.status == 'private':
                    messages.error(request, 'Эта статья приватная и доступна только автору.')
                elif article.status == 'archived':
                    messages.error(request, 'Эта статья находится в архиве и доступна только автору.')
                else:
                    messages.error(request, 'У вас нет доступа к этой статье.')
                return redirect('docs:article_list')

        except Article.DoesNotExist:
            messages.error(request, 'Статья не найдена.')
            return redirect('docs:article_list')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        # Проверяем наличие текущей версии
        if not article.current_version:
            messages.error(self.request, 'Эта статья не имеет содержимого.')
            return context

        # Увеличиваем счетчик просмотров только для опубликованных статей
        if article.status == 'published':
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

        # Форма для комментариев (только для опубликованных статей)
        if article.status == 'published':
            context['comment_form'] = CommentForm()

        # Комментарии статьи
        context['comments'] = Comment.objects.filter(
            article=article,
            is_approved=True,
            is_deleted=False,
            parent__isnull=True
        ).select_related('author').prefetch_related('children').order_by('-created_at')

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
        else:
            context['user_rating'] = None
            context['is_favorite'] = False

            # Статистика (только для опубликованных)
        try:
            context['like_count'] = article.get_like_count()
            context['dislike_count'] = article.get_dislike_count()
            context['comment_count'] = article.get_comment_count()
        except Exception as e:
            context['like_count'] = 0
            context['dislike_count'] = 0
            context['comment_count'] = 0
        else:
            # Для неопубликованных статей отключаем комментарии и оценки
            context['comment_form'] = None
            context['comments'] = []
            context['user_rating'] = None
            context['is_favorite'] = False
            context['like_count'] = 0
            context['dislike_count'] = 0
            context['comment_count'] = 0

            # Похожие статьи (только для опубликованных с текущей версией)
        if article.status == 'published':
            try:
                related_articles = Article.objects.filter(
                    status='published',
                    current_version__isnull=False,
                    category=article.category
                ).exclude(id=article.id)[:4]

                context['related_articles'] = related_articles
            except Exception as e:
                context['related_articles'] = Article.objects.none()
        else:
            context['related_articles'] = Article.objects.none()

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


class UserDashboardView(LoginRequiredMixin, TemplateView):
    """Личный кабинет пользователя"""
    template_name = 'docs/user/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        user_articles = Article.objects.filter(author=user).exclude(slug='')

        # Опубликованные статьи (публичные)
        published_articles = user_articles.filter(
            status='published'
        ).select_related('category', 'current_version').prefetch_related('tags')

        # Приватные статьи
        private_articles = user_articles.filter(
            status='private'
        ).select_related('category', 'current_version').prefetch_related('tags')

        # Черновики
        draft_articles = user_articles.filter(
            status='draft'
        ).select_related('category', 'current_version').prefetch_related('tags')

        # Статьи в архиве
        archived_articles = user_articles.filter(
            status='archived'
        ).select_related('category', 'current_version').prefetch_related('tags')

        # Статистика
        total_user_articles = Article.objects.filter(author=user)
        stats = {
            'total_articles': total_user_articles.count(),
            'published_count': published_articles.count(),
            'private_count': private_articles.count(),
            'draft_count': draft_articles.count(),
            'archived_count': archived_articles.count(),
            'total_views': total_user_articles.aggregate(total_views=Count('view_count'))['total_views'] or 0,
            'total_comments': Comment.objects.filter(article__author=user).count(),
        }

        recent_articles = user_articles.order_by('-updated_at')[:5]
        popular_articles = user_articles.filter(status='published').order_by('-view_count')[:5]

        context.update({
            'published_articles': published_articles,
            'private_articles': private_articles,
            'draft_articles': draft_articles,
            'archived_articles': archived_articles,
            'stats': stats,
            'recent_articles': recent_articles,
            'popular_articles': popular_articles,
        })

        return context
