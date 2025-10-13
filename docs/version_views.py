from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from .models import Article, ArticleVersion
from .forms import ArticleVersionForm
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from difflib import HtmlDiff


class ArticleVersionListView(LoginRequiredMixin, ListView):
    """Список версий статьи"""
    template_name = 'docs/versions/version_list.html'
    context_object_name = 'versions'
    paginate_by = 10

    def get_queryset(self):
        self.article = get_object_or_404(Article, slug=self.kwargs['slug'])
        return ArticleVersion.objects.filter(
            article=self.article
        ).select_related('author').order_by('-version_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['article'] = self.article
        return context


class VersionDetailView(DetailView):
    """Просмотр конкретной версии"""
    model = ArticleVersion
    template_name = 'docs/versions/version_detail.html'
    context_object_name = 'version'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        article_slug = self.kwargs.get('slug')
        return ArticleVersion.objects.filter(
            article__slug=article_slug
        ).select_related('article', 'author').order_by('-version_number')

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg)
        article_slug = self.kwargs.get('slug')

        version = get_object_or_404(queryset, pk=pk)

        if version.article.slug != article_slug:
            from django.http import Http404
            raise Http404("Версия не принадлежит указанной статье")

        return version

    def get_adjacent_versions(self, version):
        """Получаем предыдущую и следующую версии"""
        article_versions = ArticleVersion.objects.filter(
            article=version.article
        ).order_by('-version_number')

        versions_list = list(article_versions)
        current_index = None

        # Находим индекс текущей версии в списке
        for i, v in enumerate(versions_list):
            if v.id == version.id:
                current_index = i
                break

        prev_version = None
        next_version = None

        if current_index is not None:
            # Предыдущая версия (более новая)
            if current_index > 0:
                prev_version = versions_list[current_index - 1]
            # Следующая версия (более старая)
            if current_index < len(versions_list) - 1:
                next_version = versions_list[current_index + 1]

        return {
            'prev': prev_version,
            'next': next_version
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        version = self.object

        # Конвертируем Markdown в HTML
        extensions = [
            FencedCodeExtension(),
            CodeHiliteExtension(css_class='codehilite', linenums=False)
        ]

        context['html_content'] = markdown.markdown(
            version.content,
            extensions=extensions,
            output_format='html5'
        )

        # Проверяем, является ли эта версия текущей
        context['is_current'] = version.article.current_version == version

        # Добавляем статью в контекст для удобства
        context['article'] = version.article

        # Добавляем соседние версии
        context['adjacent_versions'] = self.get_adjacent_versions(version)

        return context

@login_required
def restore_version(request, slug, version_id):
    """Восстановление версии (создание новой версии на основе старой)"""
    article = get_object_or_404(Article, slug=slug)
    version_to_restore = get_object_or_404(
        ArticleVersion,
        id=version_id,
        article=article  # Проверяем, что версия принадлежит статье
    )

    if request.method == 'POST':
        restore_reason = request.POST.get('restore_reason', '')

        # Создаем новую версию на основе восстанавливаемой
        new_version = ArticleVersion.objects.create(
            article=article,
            title=version_to_restore.title,
            content=version_to_restore.content,
            excerpt=version_to_restore.excerpt,
            author=request.user,
            change_reason=restore_reason or f'Восстановление версии v{version_to_restore.version_number}'
        )

        # Устанавливаем новую версию как текущую
        article.current_version = new_version
        article.save()

        messages.success(
            request,
            f'Версия v{version_to_restore.version_number} восстановлена как v{new_version.version_number}!'
        )
        return redirect('docs:article_detail', slug=article.slug)

    return render(request, 'docs/versions/restore_confirm.html', {
        'article': article,
        'version': version_to_restore
    })


@login_required
def compare_versions(request, slug):
    """Сравнение двух версий"""
    article = get_object_or_404(Article, slug=slug)
    versions = ArticleVersion.objects.filter(article=article).order_by('-version_number')

    version1_id = request.GET.get('v1')
    version2_id = request.GET.get('v2')

    version1 = None
    version2 = None
    diff_html = None

    if version1_id and version2_id:
        version1 = get_object_or_404(ArticleVersion, id=version1_id, article=article)
        version2 = get_object_or_404(ArticleVersion, id=version2_id, article=article)

        # Создаем diff
        differ = HtmlDiff()
        diff_html = differ.make_table(
            version1.content.splitlines(),
            version2.content.splitlines(),
            fromdesc=f'Версия v{version1.version_number}',
            todesc=f'Версия v{version2.version_number}',
            context=True
        )

    return render(request, 'docs/versions/compare_versions.html', {
        'article': article,
        'versions': versions,
        'version1': version1,
        'version2': version2,
        'diff_html': diff_html
    })