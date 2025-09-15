from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    # Главная страница - список статей
    path('', views.ArticleListView.as_view(), name='article_list'),

    # Создание новой статьи
    path('articles/create/', views.ArticleCreateView.as_view(), name='article_create'),

    # Просмотр статьи
    path('articles/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),

    # Редактирование статьи
    path('articles/<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),

    # Статьи по категории
    path('category/<slug:slug>/', views.CategoryArticlesView.as_view(), name='category_articles'),

    # Поиск статей
    path('search/', views.SearchView.as_view(), name='search'),

    # Аутентификация
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
]