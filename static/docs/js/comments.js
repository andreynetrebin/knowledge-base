// comments.js - AJAX функциональность для комментариев и оценок
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех обработчиков
    initComments();
    initRatings();
    initFavorites();
    initSorting();
});

// ===== КОММЕНТАРИИ =====
function initComments() {
    // Обработчик отправки формы комментария
    const commentForms = document.querySelectorAll('.comment-form');
    commentForms.forEach(form => {
        form.addEventListener('submit', handleCommentSubmit);
    });

    // Обработчики кнопок ответа
    document.querySelectorAll('.reply-btn, .reply-btn-mobile').forEach(btn => {
        btn.addEventListener('click', handleReply);
    });

    // Обработчики редактирования
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', handleEdit);
    });

    // Обработчики отмены редактирования
    document.querySelectorAll('.cancel-edit').forEach(btn => {
        btn.addEventListener('click', handleCancelEdit);
    });

    // Обработчики удаления
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', handleDelete);
    });

    // Обработчик отмены ответа
    document.querySelectorAll('.cancel-reply').forEach(btn => {
        btn.addEventListener('click', handleCancelReply);
    });
}

function handleCommentSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    // Показываем индикатор загрузки
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Отправка...';
    submitBtn.disabled = true;

    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Комментарий успешно добавлен!', 'success');
            form.reset();

            // Если это ответ, скрываем форму ответа
            const replyForm = document.querySelector('.comment-form[data-is-reply="true"]');
            if (replyForm) {
                replyForm.remove();
            }

            // Перезагружаем страницу для отображения нового комментария
            setTimeout(() => {
                window.location.reload();
            }, 1000);

        } else {
            showMessage('Ошибка: ' + (data.error || 'Неизвестная ошибка'), 'error');
            // Показываем ошибки валидации
            if (data.errors) {
                displayFormErrors(form, data.errors);
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Ошибка сети. Попробуйте еще раз.', 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

function handleReply(e) {
    const commentId = e.target.dataset.commentId;
    const username = e.target.dataset.username;

    // Удаляем существующую форму ответа
    const existingReplyForm = document.querySelector('.comment-form[data-is-reply="true"]');
    if (existingReplyForm) {
        existingReplyForm.remove();
    }

    // Находим комментарий
    const comment = document.getElementById(`comment-${commentId}`);
    if (!comment) return;

    // Создаем новую форму ответа
    const formHtml = `
        <div class="card mb-3" data-is-reply="true">
            <div class="card-body">
                <form method="post" action="${window.location.pathname}comment/" class="comment-form" data-is-reply="true">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">
                    <input type="hidden" name="parent" value="${commentId}">

                    <div class="alert alert-info mb-3">
                        <strong>Ответ пользователю:</strong> ${username}
                        <button type="button" class="btn-close cancel-reply float-end" aria-label="Отмена"></button>
                    </div>

                    <div class="mb-3">
                        <textarea class="form-control" name="content" rows="3" placeholder="Ваш ответ..." maxlength="1000"></textarea>
                        <div class="form-text">Максимум 1000 символов</div>
                    </div>

                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">Ответ пользователю ${username}</small>
                        <button type="submit" class="btn btn-primary btn-sm">
                            <i class="bi bi-send"></i> Ответить
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;

    // Вставляем форму после комментария
    comment.insertAdjacentHTML('afterend', formHtml);

    // Добавляем обработчики для новой формы
    const newForm = document.querySelector('.comment-form[data-is-reply="true"]');
    newForm.addEventListener('submit', handleCommentSubmit);

    const cancelBtn = newForm.querySelector('.cancel-reply');
    cancelBtn.addEventListener('click', handleCancelReply);

    // Прокручиваем к форме
    newForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
    newForm.querySelector('textarea').focus();
}

function handleEdit(e) {
    const commentId = e.target.dataset.commentId;
    const comment = document.getElementById(`comment-${commentId}`);
    if (!comment) return;

    const contentDiv = comment.querySelector('.comment-content');
    const editForm = comment.querySelector('.comment-edit-form');
    const editTextarea = editForm.querySelector('textarea');

    // Сохраняем оригинальный текст
    editTextarea.value = contentDiv.textContent.trim();

    // Показываем форму редактирования
    contentDiv.classList.add('d-none');
    editForm.classList.remove('d-none');

    // Фокусируемся на текстовом поле
    editTextarea.focus();

    // Добавляем обработчик отправки формы редактирования
    const editFormElement = editForm.querySelector('form');
    editFormElement.addEventListener('submit', handleEditSubmit);
}

function handleEditSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Комментарий обновлен!', 'success');

            // Обновляем содержимое комментария
            const commentId = form.action.split('/').filter(Boolean).pop();
            const comment = document.getElementById(`comment-${commentId}`);
            const contentDiv = comment.querySelector('.comment-content');
            const editForm = comment.querySelector('.comment-edit-form');

            contentDiv.innerHTML = data.content.replace(/\n/g, '<br>');
            contentDiv.classList.remove('d-none');
            editForm.classList.add('d-none');

            // Добавляем метку "ред."
            const timestamp = comment.querySelector('.text-muted');
            if (!timestamp.querySelector('.badge')) {
                timestamp.innerHTML += ' <span class="badge bg-secondary">ред.</span>';
            }

        } else {
            showMessage('Ошибка при обновлении: ' + (data.error || 'Неизвестная ошибка'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Ошибка сети', 'error');
    });
}

function handleCancelEdit(e) {
    const editForm = e.target.closest('.comment-edit-form');
    const contentDiv = editForm.previousElementSibling;

    editForm.classList.add('d-none');
    contentDiv.classList.remove('d-none');
}

function handleDelete(e) {
    const commentId = e.target.dataset.commentId;

    if (!confirm('Вы уверены, что хотите удалить этот комментарий?')) {
        return;
    }

    fetch(`/comments/${commentId}/delete/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Комментарий удален', 'success');
            document.getElementById(`comment-${commentId}`).remove();
        } else {
            showMessage('Ошибка при удалении', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Ошибка сети', 'error');
    });
}

function handleCancelReply(e) {
    e.target.closest('.card[data-is-reply="true"]').remove();
}

// ===== ОЦЕНКИ =====
function initRatings() {
    document.querySelectorAll('.rating-btn').forEach(btn => {
        btn.addEventListener('click', handleRating);
    });
}

function handleRating(e) {
    const btn = e.target.closest('.rating-btn');
    const ratingType = btn.dataset.ratingType;
    const articleSlug = window.location.pathname.split('/').filter(Boolean).pop();

    // Если кнопка уже активна - удаляем оценку
    if (btn.classList.contains('active')) {
        removeRating(articleSlug);
        return;
    }

    fetch(`/articles/${articleSlug}/rate/`, {
        method: 'POST',
        body: new URLSearchParams({
            'rating_type': ratingType,
            'csrfmiddlewaretoken': getCSRFToken()
        }),
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateRatingUI(data);
        } else {
            showMessage('Ошибка: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Ошибка сети', 'error');
    });
}

function removeRating(articleSlug) {
    fetch(`/articles/${articleSlug}/rate/remove/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateRatingUI(data);
        } else {
            showMessage('Ошибка: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Ошибка сети', 'error');
    });
}

function updateRatingUI(data) {
    // Обновляем счетчики
    document.querySelector('.like-count').textContent = data.like_count;
    document.querySelector('.dislike-count').textContent = data.dislike_count;

    // Обновляем активные кнопки
    document.querySelectorAll('.rating-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    if (data.user_rating === 'like') {
        document.querySelector('.rating-btn[data-rating-type="like"]').classList.add('active');
    } else if (data.user_rating === 'dislike') {
        document.querySelector('.rating-btn[data-rating-type="dislike"]').classList.add('active');
    }
}

// ===== ИЗБРАННОЕ =====
function initFavorites() {
    document.querySelectorAll('.favorite-btn').forEach(btn => {
        btn.addEventListener('click', handleFavorite);
    });
}

function handleFavorite(e) {
    const btn = e.target.closest('.favorite-btn');
    const articleSlug = window.location.pathname.split('/').filter(Boolean).pop();

    fetch(`/articles/${articleSlug}/favorite/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');

            // Обновляем кнопку
            if (data.is_favorite) {
                btn.classList.remove('btn-outline-warning');
                btn.classList.add('btn-warning');
                btn.innerHTML = '<i class="bi bi-star-fill"></i> В избранном';
            } else {
                btn.classList.remove('btn-warning');
                btn.classList.add('btn-outline-warning');
                btn.innerHTML = '<i class="bi bi-star"></i> В избранное';
            }
        } else {
            showMessage('Ошибка: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Ошибка сети', 'error');
    });
}

// ===== СОРТИРОВКА =====
function initSorting() {
    document.querySelectorAll('[data-sort]').forEach(btn => {
        btn.addEventListener('click', handleSort);
    });
}

function handleSort(e) {
    const sortType = e.target.dataset.sort;

    // Обновляем активную кнопку
    document.querySelectorAll('[data-sort]').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');

    // Здесь можно добавить AJAX-сортировку комментариев
    // Пока просто перезагружаем страницу с параметром сортировки
    const url = new URL(window.location);
    url.searchParams.set('sort', sortType);
    window.location.href = url.toString();
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function showMessage(message, type) {
    // Создаем элемент сообщения
    const alert = document.createElement('div');
    alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Вставляем в начало страницы
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alert, container.firstChild);

    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function displayFormErrors(form, errors) {
    // Очищаем предыдущие ошибки
    form.querySelectorAll('.text-danger').forEach(el => el.remove());

    // Показываем новые ошибки
    for (const field in errors) {
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-danger small mt-1';
            errorDiv.textContent = errors[field].join(', ');
            input.parentNode.appendChild(errorDiv);
        }
    }
}