from django.urls import path
from . import views
from . import comments_views
from . import version_views  # Новый файл для версионности

app_name = 'docs'

urlpatterns = [
    # Главная страница - список статей
    path('', views.ArticleListView.as_view(), name='article_list'),

    # Создание новой статьи
    path('articles/create/', views.ArticleCreateView.as_view(), name='create_article'),

    # Помощь по форматированию
    path('formatting-help/', views.formatting_help, name='formatting_help'),

    # Просмотр статьи
    path('articles/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),

    # Редактирование статьи (создание новой версии)
    path('articles/<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='edit_article'),

    # НОВЫЕ МАРШРУТЫ ДЛЯ ВЕРСИОННОСТИ
    path('articles/<slug:slug>/versions/', version_views.ArticleVersionListView.as_view(), name='version_list'),
    path('articles/<slug:slug>/versions/<int:version_id>/', version_views.VersionDetailView.as_view(), name='version_detail'),
    path('articles/<slug:slug>/versions/<int:version_id>/restore/', version_views.restore_version, name='restore_version'),
    path('articles/<slug:slug>/compare/', version_views.compare_versions, name='compare_versions'),

    # Маршруты для тегов
    path('tags/', views.tag_cloud, name='tag_cloud'),
    path('tag/<slug:slug>/', views.TagArticlesView.as_view(), name='tag_articles'),

    # Маршруты для комментариев и оценок
    path('articles/<slug:slug>/comment/', comments_views.add_comment, name='add_comment'),
    path('comments/<int:comment_id>/edit/', comments_views.edit_comment, name='edit_comment'),
    path('comments/<int:comment_id>/delete/', comments_views.delete_comment, name='delete_comment'),
    path('articles/<slug:slug>/rate/', comments_views.rate_article, name='rate_article'),
    path('articles/<slug:slug>/rate/remove/', comments_views.remove_rating, name='remove_rating'),
    path('articles/<slug:slug>/favorite/', comments_views.toggle_favorite, name='toggle_favorite'),
    path('articles/<slug:slug>/comments/', comments_views.comment_tree, name='comment_tree'),

    # Статьи по категории
    path('category/<slug:slug>/', views.CategoryArticlesView.as_view(), name='category_articles'),

    # Поиск статей
    path('search/', views.SearchView.as_view(), name='search'),

    # Аутентификация
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
]