from django.core.management.base import BaseCommand
from docs.models import Article
from django.utils.text import slugify
import uuid


class Command(BaseCommand):
    help = 'Исправляет статьи без slug'

    def handle(self, *args, **options):
        articles_without_slug = Article.objects.filter(slug='')

        self.stdout.write(f'Найдено статей без slug: {articles_without_slug.count()}')

        for article in articles_without_slug:
            # Создаем slug из заголовка
            new_slug = slugify(article.title)

            # Если slug уже существует, добавляем UUID
            if Article.objects.filter(slug=new_slug).exists():
                new_slug = f"{new_slug}-{uuid.uuid4().hex[:8]}"

            article.slug = new_slug
            article.save()

            self.stdout.write(
                self.style.SUCCESS(f'Исправлен slug для статьи: {article.title} -> {new_slug}')
            )