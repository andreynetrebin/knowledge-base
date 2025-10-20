import os
import tempfile
from datetime import datetime
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from io import BytesIO
import base64


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

    def _create_pdf_compatible_html(self):
        """Создает HTML совместимый с xhtml2pdf"""
        context = self._prepare_context()

        # Используем упрощенный шаблон без проблемного CSS
        html_content = render_to_string('docs/export/article_pdf_compatible.html', context)
        return html_content

    def export_html(self):
        """Экспорт в HTML"""
        context = self._prepare_context()
        html_content = render_to_string('docs/export/article_html.html', context)

        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        filename = f'{self.article.slug}_{datetime.now().strftime("%Y%m%d_%H%M")}.html'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    def export_pdf(self):
        """Экспорт в PDF с использованием xhtml2pdf"""
        html_content = self._create_pdf_compatible_html()

        # Создаем BytesIO объект для PDF
        pdf_buffer = BytesIO()

        # Конвертируем HTML в PDF с настройками для кириллицы
        pisa_status = pisa.CreatePDF(
            src=html_content,
            dest=pdf_buffer,
            encoding='utf-8',
            link_callback=self._link_callback
        )

        # Проверяем успешность конвертации
        if pisa_status.err:
            # В случае ошибки возвращаем текстовое сообщение об ошибке
            error_response = HttpResponse(
                f"Ошибка при создании PDF: {pisa_status.err}",
                content_type='text/plain; charset=utf-8'
            )
            error_response['Content-Disposition'] = 'attachment; filename="error.txt"'
            return error_response

        # Получаем PDF данные из буфера
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f'{self.article.slug}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    def _link_callback(self, uri, rel):
        """
        Callback для обработки ссылок и изображений
        """
        # Для локальных файлов можно добавить обработку
        return uri

    def export_pdf_to_file(self, output_path):
        """Экспорт в PDF файл (для использования в фоновых задачах)"""
        html_content = self._create_pdf_compatible_html()

        with open(output_path, 'w+b') as output_file:
            pisa_status = pisa.CreatePDF(
                src=html_content,
                dest=output_file,
                encoding='utf-8',
                link_callback=self._link_callback
            )

        return not pisa_status.err

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