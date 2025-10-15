// docs/static/docs/js/tags_manager.js

document.addEventListener('DOMContentLoaded', function() {
    const tagsSelect = document.getElementById('tags-select');
    const newTagsInput = document.getElementById('new-tags-input');
    const tagsContainer = document.getElementById('tags-container');

    if (!tagsSelect || !newTagsInput) return;

    // Функция для создания визуального отображения тегов
    function updateTagsVisual() {
        if (!tagsContainer) return;

        tagsContainer.innerHTML = '';

        // Показываем выбранные теги
        Array.from(tagsSelect.selectedOptions).forEach(option => {
            const tagBadge = document.createElement('span');
            tagBadge.className = 'badge bg-primary me-2 mb-2';
            tagBadge.innerHTML = `
                ${option.text}
                <button type="button" class="btn-close btn-close-white ms-1"
                        style="font-size: 0.7rem;"
                        data-tag-id="${option.value}"></button>
            `;
            tagsContainer.appendChild(tagBadge);
        });

        // Показываем новые теги
        const newTags = newTagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
        newTags.forEach(tag => {
            const tagBadge = document.createElement('span');
            tagBadge.className = 'badge bg-success me-2 mb-2';
            tagBadge.innerHTML = `
                ${tag} (новый)
                <button type="button" class="btn-close btn-close-white ms-1"
                        style="font-size: 0.7rem;"
                        data-new-tag="${tag}"></button>
            `;
            tagsContainer.appendChild(tagBadge);
        });

        // Добавляем обработчики для удаления тегов
        tagsContainer.querySelectorAll('.btn-close').forEach(btn => {
            btn.addEventListener('click', function() {
                if (this.dataset.tagId) {
                    // Удаляем существующий тег
                    const option = tagsSelect.querySelector(`option[value="${this.dataset.tagId}"]`);
                    if (option) option.selected = false;
                } else if (this.dataset.newTag) {
                    // Удаляем новый тег
                    const currentTags = newTagsInput.value.split(',').map(tag => tag.trim());
                    const updatedTags = currentTags.filter(tag => tag !== this.dataset.newTag);
                    newTagsInput.value = updatedTags.join(', ');
                }
                updateTagsVisual();
            });
        });
    }

    // Обработчик для поля новых тегов
    newTagsInput.addEventListener('blur', function() {
        updateTagsVisual();
    });

    // Обработчик для мультиселекта
    tagsSelect.addEventListener('change', updateTagsVisual);

    // Автодополнение для новых тегов
    newTagsInput.addEventListener('input', function() {
        const cursorPosition = this.selectionStart;
        const textBeforeCursor = this.value.substring(0, cursorPosition);
        const lastComma = textBeforeCursor.lastIndexOf(',');
        const currentWord = textBeforeCursor.substring(lastComma + 1).trim();

        if (currentWord.length < 2) return;

        // Здесь можно добавить автодополнение из существующих тегов
        // Пока оставим пустым для простоты
    });

    // Инициализация при загрузке
    updateTagsVisual();
});