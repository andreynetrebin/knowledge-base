from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Article, Comment, Rating, Favorite
from .comments_forms import CommentForm, CommentEditForm


@login_required
@require_POST
def add_comment(request, slug):
    """Добавление комментария к статье"""
    article = get_object_or_404(Article, slug=slug, status='published')
    form = CommentForm(request.POST)

    if form.is_valid():
        try:
            with transaction.atomic():
                comment = form.save(commit=False)
                comment.article = article
                comment.author = request.user

                # Обработка родительского комментария (для ответов)
                parent_id = form.cleaned_data.get('parent')
                if parent_id:
                    parent_comment = get_object_or_404(Comment, id=parent_id, article=article)
                    comment.parent = parent_comment

                comment.save()

                messages.success(request, 'Комментарий успешно добавлен!')

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Комментарий добавлен',
                        'comment_id': comment.id
                    })

        except Exception as e:
            messages.error(request, 'Ошибка при добавлении комментария')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
    else:
        messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)

    return redirect('docs:article_detail', slug=slug)


@login_required
@require_POST
def edit_comment(request, comment_id):
    """Редактирование комментария"""
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    form = CommentEditForm(request.POST, instance=comment)

    if form.is_valid():
        form.save()
        messages.success(request, 'Комментарий успешно обновлен!')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Комментарий обновлен',
                'content': comment.content
            })
    else:
        messages.error(request, 'Ошибка при обновлении комментария')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)

    return redirect('docs:article_detail', slug=comment.article.slug)


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(Comment, id=comment_id)

    # Проверяем права на удаление
    if not comment.can_delete(request.user):
        messages.error(request, 'У вас нет прав для удаления этого комментария')
        return redirect('docs:article_detail', slug=comment.article.slug)

    comment.is_deleted = True
    comment.save()

    messages.success(request, 'Комментарий удален')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Комментарий удален'
        })

    return redirect('docs:article_detail', slug=comment.article.slug)


@login_required
@require_POST
def rate_article(request, slug):
    """Оценка статьи (лайк/дизлайк)"""
    article = get_object_or_404(Article, slug=slug, status='published')
    rating_type = request.POST.get('rating_type')

    if rating_type not in ['like', 'dislike']:
        return JsonResponse({
            'success': False,
            'error': 'Неверный тип оценки'
        }, status=400)

    try:
        with transaction.atomic():
            # Удаляем существующую оценку пользователя
            Rating.objects.filter(article=article, user=request.user).delete()

            # Создаем новую оценку
            rating = Rating.objects.create(
                article=article,
                user=request.user,
                rating_type=rating_type
            )

            like_count = article.get_like_count()
            dislike_count = article.get_dislike_count()

            return JsonResponse({
                'success': True,
                'like_count': like_count,
                'dislike_count': dislike_count,
                'user_rating': rating_type
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def remove_rating(request, slug):
    """Удаление оценки статьи"""
    article = get_object_or_404(Article, slug=slug, status='published')

    try:
        Rating.objects.filter(article=article, user=request.user).delete()

        like_count = article.get_like_count()
        dislike_count = article.get_dislike_count()

        return JsonResponse({
            'success': True,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'user_rating': None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def toggle_favorite(request, slug):
    """Добавление/удаление статьи из избранного"""
    article = get_object_or_404(Article, slug=slug, status='published')

    try:
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            article=article
        )

        if not created:
            # Если уже в избранном - удаляем
            favorite.delete()
            is_favorite = False
            message = 'Статья удалена из избранного'
        else:
            is_favorite = True
            message = 'Статья добавлена в избранное'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_favorite': is_favorite,
                'message': message
            })
        else:
            messages.success(request, message)
            return redirect('docs:article_detail', slug=slug)

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        else:
            messages.error(request, 'Ошибка при работе с избранным')
            return redirect('docs:article_detail', slug=slug)


def comment_tree(request, slug):
    """Получение дерева комментариев для статьи"""
    article = get_object_or_404(Article, slug=slug, status='published')
    comments = Comment.objects.filter(
        article=article,
        is_approved=True,
        is_deleted=False
    ).select_related('author').prefetch_related('children')

    # Здесь будет логика для рендеринга дерева комментариев
    # Вернем JSON или рендерим шаблон
    pass