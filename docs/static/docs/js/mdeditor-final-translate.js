// Полный перевод для MDEditor
function translateMDEditor() {
    console.log('Starting MDEditor translation...');

    const translations = {
        // Основные кнопки панели инструментов
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

        // Модальное окно изображения (ваши скриншоты)
        '添加图片': 'Добавить изображение',
        '图片地址': 'URL изображения',
        '本地上传': 'Загрузить с компьютера',
        '图片描述': 'Описание изображения',
        '图片链接': 'Ссылка на изображение',
        '确定': 'OK',
        '取消': 'Отмена',
        '提交': 'Отправить',
        '关闭': 'Закрыть',
        '选择': 'Выбрать',

        // Модальное окно ссылки
        '添加链接': 'Добавить ссылку',
        '链接地址': 'URL ссылки',
        '链接文本': 'Текст ссылки',

        // Модальное окно кода
        '添加代码': 'Добавить код',
        '代码语言': 'Язык программирования',
        '请输入代码语言': 'Введите язык программирования',

        // Заголовки и текст
        '在线图片': 'Из интернета',
        '本地图片': 'С компьютера',
        '图片URL': 'URL изображения',
        '图片标题': 'Заголовок изображения',
        '目录': 'Содержание',
        '脚注': 'Сноска',
        '表情': 'Эмодзи',
        '搜索': 'Поиск',
        '帮助': 'Помощь',

        // Ошибки и сообщения
        '上传失败': 'Ошибка загрузки',
        '上传成功': 'Успешно загружено',
        '文件过大': 'Файл слишком большой',
        '不支持的格式': 'Неподдерживаемый формат',
        '正在上传...': 'Загружается...',
        '选择文件': 'Выбрать файл',
        '未选择文件': 'Файл не выбран',
        '拖拽文件到此处或': 'Перетащите файл сюда или',
        '点击上传': 'нажмите для загрузки'
    };

    function translateText(text) {
        let translated = text;
        Object.keys(translations).forEach(chinese => {
            if (translated.includes(chinese)) {
                translated = translated.replace(new RegExp(escapeRegExp(chinese), 'g'), translations[chinese]);
            }
        });
        return translated;
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function translateElement(element) {
        // Переводим атрибуты
        ['title', 'placeholder', 'alt'].forEach(attr => {
            if (element.hasAttribute(attr)) {
                const value = element.getAttribute(attr);
                const translated = translateText(value);
                if (translated !== value) {
                    element.setAttribute(attr, translated);
                }
            }
        });

        // Переводим data-атрибуты
        if (element.dataset.originalTitle) {
            element.dataset.originalTitle = translateText(element.dataset.originalTitle);
        }

        // Переводим текстовые узлы
        if (element.childNodes.length > 0) {
            element.childNodes.forEach(child => {
                if (child.nodeType === Node.TEXT_NODE && child.textContent.trim()) {
                    const translated = translateText(child.textContent);
                    if (translated !== child.textContent) {
                        child.textContent = translated;
                    }
                }
            });
        }

        // Переводим value у кнопок
        if (element.tagName === 'INPUT' && (element.type === 'button' || element.type === 'submit')) {
            const translated = translateText(element.value);
            if (translated !== element.value) {
                element.value = translated;
            }
        }
    }

    function applyTranslations() {
        // Переводим все элементы на странице
        const allElements = document.querySelectorAll('*');
        allElements.forEach(translateElement);

        // Специально переводим модальные окна MDEditor
        const modalSelectors = [
            '.editormd-dialog',
            '.editormd-form',
            '.editormd-dialog-header',
            '.editormd-dialog-body',
            '.editormd-dialog-footer',
            '.editormd-toolbar',
            '.faq'
        ];

        modalSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(translateElement);
        });

        // Переводим кнопки отдельно
        document.querySelectorAll('button, .btn, input[type="button"], input[type="submit"]').forEach(translateElement);

        // Переводим labels и заголовки
        document.querySelectorAll('label, h1, h2, h3, h4, h5, h6, p, span, div').forEach(translateElement);

        console.log('MDEditor translation completed');
    }

    // Основная функция перевода
    function startTranslation() {
        // Немедленный перевод
        applyTranslations();

        // Переводчик с интервалом для динамических элементов
        let translationAttempts = 0;
        const maxAttempts = 20;

        const translationInterval = setInterval(() => {
            applyTranslations();
            translationAttempts++;

            if (translationAttempts >= maxAttempts) {
                clearInterval(translationInterval);
                console.log('MDEditor translation finished after', maxAttempts, 'attempts');
            }
        }, 300);

        // Отслеживаем появление новых элементов
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length) {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Если это модальное окно MDEditor
                            if (node.classList && (
                                node.classList.contains('editormd-dialog') ||
                                node.classList.contains('editormd-form') ||
                                node.querySelector('.editormd-dialog')
                            )) {
                                setTimeout(() => {
                                    applyTranslations();
                                }, 100);
                            } else {
                                translateElement(node);
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

        // Переводим при клике на кнопки изображения и ссылки
        document.addEventListener('click', function(e) {
            if (e.target.closest('.editormd-toolbar')) {
                setTimeout(applyTranslations, 200);
            }
        });

        // Переводим при фокусе на элементах формы
        document.addEventListener('focus', function(e) {
            if (e.target.closest('.editormd-dialog')) {
                setTimeout(applyTranslations, 100);
            }
        }, true);
    }

    // Запускаем перевод
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startTranslation);
    } else {
        startTranslation();
    }

    // Дублируем на случай если редактор загрузился позже
    window.addEventListener('load', startTranslation);
}

// Запускаем перевод
translateMDEditor();