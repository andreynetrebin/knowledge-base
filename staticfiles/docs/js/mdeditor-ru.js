// Русская локализация для MDEditor
document.addEventListener('DOMContentLoaded', function() {
    // Ждем пока загрузится MDEditor
    setTimeout(function() {
        if (typeof MDEditor !== 'undefined') {
            MDEditor.locales = {
                'ru': {
                    'Bold': 'Жирный',
                    'Italic': 'Курсив',
                    'Header': 'Заголовок',
                    'Underline': 'Подчеркивание',
                    'Strikethrough': 'Зачеркивание',
                    'Mark': 'Маркер',
                    'Superscript': 'Надстрочный',
                    'Subscript': 'Подстрочный',
                    'Left align': 'По левому краю',
                    'Center align': 'По центру',
                    'Right align': 'По правому краю',
                    'Unordered list': 'Маркированный список',
                    'Ordered list': 'Нумерованный список',
                    'Quote': 'Цитата',
                    'Line': 'Разделитель',
                    'Link': 'Ссылка',
                    'Image Link': 'Изображение',
                    'Code': 'Код',
                    'Table': 'Таблица',
                    'Upload': 'Загрузить',
                    'Uploading': 'Загрузка',
                    'Normal': 'Обычный',
                    'Heading 1': 'Заголовок 1',
                    'Heading 2': 'Заголовок 2',
                    'Heading 3': 'Заголовок 3',
                    'Heading 4': 'Заголовок 4',
                    'Heading 5': 'Заголовок 5',
                    'Heading 6': 'Заголовок 6',
                    'Code Language': 'Язык кода',
                    'Watch': 'Просмотр',
                    'Unwatch': 'Закрыть просмотр',
                    'Preview': 'Предпросмотр',
                    'Fullscreen': 'Полный экран',
                    'Exit Fullscreen': 'Выйти из полного экрана',
                    'Clear': 'Очистить',
                    'Export': 'Экспорт',
                    'Import': 'Импорт'
                }
            };
            MDEditor.locale = 'ru';
        }
    }, 100);
});