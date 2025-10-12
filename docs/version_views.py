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

    def get_queryset(self):
        return ArticleVersion.objects.select_related('article', 'author')

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

        return context


@login_required
def restore_version(request, slug, version_id):
    """Восстановление версии (создание новой версии на основе старой)"""
    article = get_object_or_404(Article, slug=slug)
    version_to_restore = get_object_or_404(
        ArticleVersion,
        id=version_id,
        article=article
    )

    if request.method == 'POST':
        # Создаем новую версию на основе восстанавливаемой
        new_version = ArticleVersion.objects.create(
            article=article,
            title=version_to_restore.title,
            content=version_to_restore.content,
            excerpt=version_to_restore.excerpt,
            author=request.user,
            change_reason=f'Восстановление версии v{version_to_restore.version_number}'
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