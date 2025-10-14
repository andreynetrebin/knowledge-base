import os
import tempfile
from datetime import datetime
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension


class ArticleExporter:
    """Класс для экспорта статей в различные форматы"""

    def __init__(self, article, request=None):
        self.article = article
        self.request = request
        self.version = article.current_version

    def _prepare_context(self):
        """Подготавливает контекст для шаблонов"""
        # Конвертируем Markdown в HTML
        extensions = [
            FencedCodeExtension(),
            CodeHiliteExtension(css_class='codehilite', linenums=False)
        ]

        html_content = markdown.markdown(
            self.version.content,
            extensions=extensions,
            output_format='html5'
        )

        return {
            'article': self.article,
            'version': self.version,
            'html_content': html_content,
            'export_date': datetime.now(),
            'request': self.request,
        }

    def export_html(self):
        """Экспорт в HTML"""
        context = self._prepare_context()
        html_content = render_to_string('docs/export/article_html.html', context)

        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        filename = f'{self.article.slug}_{datetime.now().strftime("%Y%m%d_%H%M")}.html'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    def export_pdf(self):
        """Экспорт в PDF"""
        context = self._prepare_context()
        html_content = render_to_string('docs/export/article_pdf.html', context)

        # Создаем временный файл для PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            # Конфигурация для поддержки русских шрифтов
            font_config = FontConfiguration()

            # Генерируем PDF
            HTML(string=html_content).write_pdf(
                tmp_file.name,
                font_config=font_config,
                stylesheets=[
                    # Можно добавить кастомные CSS
                ]
            )

            # Читаем сгенерированный PDF
            with open(tmp_file.name, 'rb') as pdf_file:
                pdf_content = pdf_file.read()

            # Удаляем временный файл
            os.unlink(tmp_file.name)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f'{self.article.slug}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    def export_text(self):
        """Экспорт в простой текст"""
        context = self._prepare_context()
        text_content = render_to_string('docs/export/article_text.txt', context)

        response = HttpResponse(text_content, content_type='text/plain; charset=utf-8')
        filename = f'{self.article.slug}_{datetime.now().strftime("%Y%m%d_%H%M")}.txt'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


def create_export_record(article, export_format, user, file_size=None):
    """Создает запись об экспорте в базе данных"""
    from .models import ArticleExport

    return ArticleExport.objects.create(
        article=article,
        export_format=export_format,
        exported_by=user,
        file_size=file_size
    )