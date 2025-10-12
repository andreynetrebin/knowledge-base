// Простой перевод для MDEditor
function translateMDEditor() {
    console.log('Translating MDEditor...');

    // Ждем пока загрузится редактор
    const checkEditor = setInterval(() => {
        const editor = document.querySelector('.editormd');
        if (editor) {
            clearInterval(checkEditor);
            applyTranslations();
        }
    }, 500);

    function applyTranslations() {
        // Основные переводы для title атрибутов
        const translations = {
            '粗体': 'Жирный',
            '斜体': 'Курсив',
            '标题': 'Заголовок',
            '引用': 'Цитата',
            '无序列表': 'Маркированный список',
            '有序列表': 'Нумерованный список',
            '横线': 'Разделитель',
            '链接': 'Ссылка',
            '图片链接': 'Изображение',
            '代码': 'Код',
            '代码块': 'Блок кода',
            '表格': 'Таблица',
            '上传': 'Загрузить',
            '实时预览': 'Просмотр',
            '关闭预览': 'Закрыть просмотр',
            '预览': 'Предпросмотр',
            '全屏': 'Полный экран',
            '退出全屏': 'Выйти из полного экрана',
            '清空': 'Очистить'
        };

        // Переводим title атрибуты
        document.querySelectorAll('[title]').forEach(element => {
            let title = element.title;
            Object.keys(translations).forEach(chinese => {
                if (title.includes(chinese)) {
                    title = title.replace(chinese, translations[chinese]);
                    element.title = title;
                }
            });
        });

        // Переводим data-original-title атрибуты
        document.querySelectorAll('[data-original-title]').forEach(element => {
            let title = element.dataset.originalTitle;
            Object.keys(translations).forEach(chinese => {
                if (title.includes(chinese)) {
                    title = title.replace(chinese, translations[chinese]);
                    element.dataset.originalTitle = title;
                }
            });
        });

        console.log('MDEditor translation applied');
    }

    // Также переводим при изменении DOM
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                setTimeout(applyTranslations, 100);
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Запускаем когда страница загружена
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', translateMDEditor);
} else {
    translateMDEditor();
}