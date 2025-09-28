// Расширенный перевод для MDEditor
function translateMDEditor() {
    console.log('Translating MDEditor...');

    const translations = {
        // Основные кнопки панели
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
        '上传中': 'Загружается',
        '实时预览': 'Просмотр',
        '关闭预览': 'Закрыть просмотр',
        '预览': 'Предпросмотр',
        '全屏': 'Полный экран',
        '退出全屏': 'Выйти из полного экрана',
        '清空': 'Очистить',
        '导出': 'Экспорт',
        '导入': 'Импорт',

        // Модальное окно изображения
        '上传图片': 'Загрузить изображение',
        '在线图片': 'Из интернета',
        '本地图片': 'С компьютера',
        '图片链接地址': 'URL изображения',
        '图片描述': 'Описание изображения',
        '确定': 'OK',
        '取消': 'Отмена',
        '提交': 'Отправить',
        '关闭': 'Закрыть',
        '选择': 'Выбрать',

        // Модальное окно ссылки
        '链接地址': 'URL ссылки',
        '链接文本': 'Текст ссылки',

        // Модальное окно кода
        '代码语言': 'Язык программирования',
        '请输入代码语言': 'Введите язык программирования',

        // Другие элементы
        '目录': 'Содержание',
        '脚注': 'Сноска',
        '表情': 'Эмодзи',
        '搜索': 'Поиск',
        '帮助': 'Помощь'



    };

    function applyTranslations() {
        // Переводим title атрибуты
        document.querySelectorAll('[title]').forEach(element => {
            translateAttribute(element, 'title');
        });

        // Переводим data-original-title атрибуты
        document.querySelectorAll('[data-original-title]').forEach(element => {
            translateAttribute(element, 'data-original-title');
        });

        // Переводим текстовые узлы в модальных окнах
        document.querySelectorAll('.editormd-dialog, .editormd-form, .editormd-dialog-header, .editormd-dialog-body, .editormd-dialog-footer').forEach(container => {
            translateTextNodes(container);
        });

        // Переводим кнопки
        document.querySelectorAll('button, input[type="button"], input[type="submit"], a.btn').forEach(button => {
            translateTextNodes(button);
        });

        // Переводим labels
        document.querySelectorAll('label').forEach(label => {
            translateTextNodes(label);
        });

        console.log('MDEditor translation applied');
    }

    function translateAttribute(element, attrName) {
        const value = attrName === 'data-original-title' ?
            element.dataset.originalTitle : element[attrName];

        if (value) {
            let newValue = value;
            Object.keys(translations).forEach(chinese => {
                if (newValue.includes(chinese)) {
                    newValue = newValue.replace(new RegExp(chinese, 'g'), translations[chinese]);
                }
            });

            if (attrName === 'data-original-title') {
                element.dataset.originalTitle = newValue;
            } else {
                element[attrName] = newValue;
            }
        }
    }

    function translateTextNodes(element) {
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let node;
        while (node = walker.nextNode()) {
            let text = node.textContent;
            Object.keys(translations).forEach(chinese => {
                if (text.includes(chinese)) {
                    text = text.replace(new RegExp(chinese, 'g'), translations[chinese]);
                }
            });
            node.textContent = text;
        }
    }

    // Запускаем перевод сразу
    applyTranslations();

    // Повторяем перевод каждые 100ms в течение 5 секунд для динамических элементов
    let attempts = 0;
    const maxAttempts = 50; // 5 секунд

    const interval = setInterval(() => {
        applyTranslations();
        attempts++;

        if (attempts >= maxAttempts) {
            clearInterval(interval);
            console.log('MDEditor translation finished');
        }
    }, 100);

    // Отслеживаем появление модальных окон
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.classList && (
                            node.classList.contains('editormd-dialog') ||
                            node.classList.contains('editormd-form') ||
                            node.querySelector('.editormd-dialog')
                        )) {
                            setTimeout(() => {
                                applyTranslations();
                            }, 50);
                        }
                    }
                });
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Также переводим при открытии модальных окон
    document.addEventListener('click', function(e) {
        if (e.target.matches('.editormd-toolbar [title*="图片链接"], .editormd-toolbar [title*="链接"]')) {
            setTimeout(applyTranslations, 200);
        }
    });
}

// Запускаем когда страница загружена
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', translateMDEditor);
} else {
    translateMDEditor();
}

// Также переводим при полной загрузке страницы
window.addEventListener('load', translateMDEditor);