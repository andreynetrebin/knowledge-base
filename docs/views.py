from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib.auth import views as auth_views
from .models import Article, Category
from .forms import ArticleForm
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
        return Article.objects.filter(status='published').select_related('author', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['pinned_articles'] = Article.objects.filter(
            status='published', is_pinned=True
        )[:5]
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'docs/articles/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.filter(status='published')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        # Увеличиваем счетчик просмотров
        article.increment_view_count()

        # Конвертируем Markdown в HTML
        extensions = [
            FencedCodeExtension(),
            CodeHiliteExtension(css_class='codehilite', linenums=False)
        ]

        context['html_content'] = markdown.markdown(
            article.content,
            extensions=extensions,
            output_format='html5'
        )

        # Похожие статьи
        context['related_articles'] = Article.objects.filter(
            category=article.category,
            status='published'
        ).exclude(id=article.id)[:4]

        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'docs/articles/article_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Статья успешно создана!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('docs:article_detail', kwargs={'slug': self.object.slug})


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'docs/articles/article_form.html'

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Статья успешно обновлена!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('docs:article_detail', kwargs={'slug': self.object.slug})


class CategoryArticlesView(ListView):
    model = Article
    template_name = 'docs/articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Article.objects.filter(
            category=self.category, status='published'
        ).select_related('author', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.all()
        return context


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
                Q(content__icontains=query) |
                Q(excerpt__icontains=query),
                status='published'
            ).select_related('author', 'category')
        return Article.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['categories'] = Category.objects.all()
        return context


# Аутентификация
class LoginView(auth_views.LoginView):
    template_name = 'docs/auth/login.html'


# Удаляем класс LogoutView и заменяем на:
def logout_view(request):
    """Представление для выхода из системы"""
    if request.method == 'POST':
        logout(request)
        return redirect('docs:login')
    else:
        # Для GET запросов перенаправляем на страницу подтверждения
        return render(request, 'docs/auth/logout_confirm.html')


# Добавляем после существующих представлений

def register_view(request):
    """Представление для регистрации новых пользователей"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически входим после регистрации
            messages.success(request, 'Аккаунт успешно создан! Добро пожаловать!')
            return redirect('docs:article_list')
    else:
        form = UserRegisterForm()

    return render(request, 'docs/auth/register.html', {'form': form})
