from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Article
from .export_utils import ArticleExporter, create_export_record


@login_required
def export_article(request, slug, format_type):
    """Экспорт статьи в указанном формате"""
    article = get_object_or_404(Article, slug=slug)

    # Проверяем, что у статьи есть текущая версия
    if not article.current_version:
        messages.error(request, 'Нельзя экспортировать статью без содержимого.')
        return redirect('docs:article_detail', slug=slug)

    # Создаем экспортер
    exporter = ArticleExporter(article, request)

    try:
        # Выбираем формат экспорта
        if format_type == 'html':
            response = exporter.export_html()
            file_size = len(response.content)

        elif format_type == 'pdf':
            response = exporter.export_pdf()
            file_size = len(response.content)

        elif format_type == 'txt':
            response = exporter.export_text()
            file_size = len(response.content)

        else:
            messages.error(request, 'Неподдерживаемый формат экспорта.')
            return redirect('docs:article_detail', slug=slug)

        # Создаем запись об экспорте
        create_export_record(article, format_type, request.user, file_size)

        messages.success(request, f'Статья успешно экспортирована в формат {format_type.upper()}.')
        return response

    except Exception as e:
        messages.error(request, f'Ошибка при экспорте: {str(e)}')
        return redirect('docs:article_detail', slug=slug)


@login_required
def export_article_options(request, slug):
    """Страница выбора опций экспорта"""
    article = get_object_or_404(Article, slug=slug)

    if not article.current_version:
        messages.error(request, 'Нельзя экспортировать статью без содержимого.')
        return redirect('docs:article_detail', slug=slug)

    # Получаем историю экспортов
    export_history = article.exports.filter(exported_by=request.user).order_by('-exported_at')[:5]

    return render(request, 'docs/export/export_options.html', {
        'article': article,
        'export_history': export_history,
    })