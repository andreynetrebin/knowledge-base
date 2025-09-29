from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    # Главная страница - список статей
    path('', views.ArticleListView.as_view(), name='article_list'),

    # Создание новой статьи
    path('articles/create/', views.ArticleCreateView.as_view(), name='create_article'),  # ИЗМЕНИЛИ: article_create → create_article

    # Помощь по форматированию
    path('formatting-help/', views.formatting_help, name='formatting_help'),

    # Просмотр статьи
    path('articles/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),

    # Редактирование статьи
    path('articles/<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='edit_article'),  # ДОБАВИЛИ: согласованное имя

    # ДОБАВЛЯЕМ МАРШРУТЫ ДЛЯ ТЕГОВ
    path('tags/', views.tag_cloud, name='tag_cloud'),
    path('tag/<slug:slug>/', views.TagArticlesView.as_view(), name='tag_articles'),

    # Статьи по категории
    path('category/<slug:slug>/', views.CategoryArticlesView.as_view(), name='category_articles'),

    # Поиск статей
    path('search/', views.SearchView.as_view(), name='search'),

    # Аутентификация
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
]