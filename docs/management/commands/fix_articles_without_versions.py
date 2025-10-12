from django.core.management.base import BaseCommand
from docs.models import Article, ArticleVersion
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Создает версии для статей без текущей версии'

    def handle(self, *args, **options):
        articles_without_versions = Article.objects.filter(current_version__isnull=True)

        self.stdout.write(f'Найдено статей без версий: {articles_without_versions.count()}')

        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('Не найден суперпользователь для создания версий'))
            return

        for article in articles_without_versions:
            # Сначала создаем версию
            version = ArticleVersion(
                article=article,
                title=article.title,
                content='Содержимое этой статьи будет добавлено позже.',
                excerpt='',
                author=admin_user,
                change_reason='Автоматическое создание версии'
            )
            version.save()  # Сохраняем версию отдельно

            # Затем обновляем статью
            article.current_version = version
            article.save(update_fields=['current_version'])

            self.stdout.write(
                self.style.SUCCESS(f'Создана версия для статьи: {article.title}')
            )