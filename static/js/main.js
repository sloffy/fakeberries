document.addEventListener('DOMContentLoaded', () => {
    initFlashClose();
    initFileInputHints();
    initBasketAjax();
    moveServerFlashMessages();
});

function initFlashClose() {
    document.querySelectorAll('[data-close-flash]').forEach(button => {
        button.addEventListener('click', () => {
            const flash = button.closest('.fb-flash');
            if (flash) {
                flash.style.animation = 'slideUp 0.3s ease-out';
                setTimeout(() => flash.remove(), 300);
            }
        });
    });
}

function moveServerFlashMessages() {
    // Перемещаем flash-сообщения с сервера в фиксированный контейнер
    const serverFlashes = document.querySelectorAll('[data-flash-message]');
    if (serverFlashes.length === 0) return;
    
    let container = document.querySelector('.fb-flashes-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'fb-flashes-container';
        document.body.insertBefore(container, document.body.firstChild);
    }
    
    serverFlashes.forEach(flash => {
        flash.removeAttribute('data-flash-message');
        container.appendChild(flash);
        
        // Автоматически закрываем через 3 секунды
        setTimeout(() => {
            flash.style.animation = 'slideUp 0.3s ease-out';
            setTimeout(() => flash.remove(), 300);
        }, 3000);
    });
}

function initFileInputHints() {
    const fileInputs = document.querySelectorAll('input[type="file"][name="image"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', () => {
            const file = input.files && input.files[0];
            if (!file) {
                return;
            }
            const maxSize = 8 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('Размер изображения не должен превышать 8 МБ.');
                input.value = '';
            }
        });
    });
}

function initBasketAjax() {
    const forms = document.querySelectorAll('.add-to-basket-form');
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const button = form.querySelector('button[type="submit"]');
            const originalText = button.textContent;
            const productId = parseInt(form.dataset.productId);
            
            // Сохраняем позицию скролла
            const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
            
            // Блокируем кнопку
            button.disabled = true;
            button.textContent = 'Добавление...';
            
            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Обновляем счётчик
                    const quantityContainer = document.querySelector(`.fb-card__quantity-container[data-product-id="${productId}"]`);
                    const quantityElement = quantityContainer?.querySelector('.fb-card__quantity');
                    const quantityValue = quantityContainer?.querySelector('.quantity-value');
                    
                    if (quantityElement && quantityValue) {
                        const newQuantity = data.quantity;
                        quantityValue.textContent = newQuantity;
                        quantityElement.style.display = newQuantity > 0 ? 'block' : 'none';
                    }
                    
                    // Показываем уведомление (опционально)
                    showFlashMessage(data.message, 'success');
                } else {
                    showFlashMessage('Ошибка при добавлении товара в корзину', 'error');
                }
            } catch (error) {
                console.error('Ошибка:', error);
                showFlashMessage('Ошибка при добавлении товара в корзину', 'error');
            } finally {
                // Восстанавливаем кнопку
                button.disabled = false;
                button.textContent = originalText;
                
                // Восстанавливаем позицию скролла
                window.scrollTo(0, scrollPosition);
            }
        });
    });
}

function showFlashMessage(message, type) {
    // Получаем или создаём контейнер для flash-сообщений
    let container = document.querySelector('.fb-flashes-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'fb-flashes-container';
        document.body.insertBefore(container, document.body.firstChild);
    }
    
    // Создаём элемент уведомления
    const flash = document.createElement('div');
    flash.className = `fb-flash fb-flash--${type}`;
    flash.innerHTML = `
        <span>${message}</span>
        <button type="button" data-close-flash aria-label="Закрыть">×</button>
    `;
    
    // Вставляем в контейнер
    container.appendChild(flash);
    
    // Автоматически закрываем через 3 секунды
    setTimeout(() => {
        flash.style.animation = 'slideUp 0.3s ease-out';
        setTimeout(() => flash.remove(), 300);
    }, 3000);
    
    // Инициализируем кнопку закрытия
    const closeBtn = flash.querySelector('[data-close-flash]');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            flash.style.animation = 'slideUp 0.3s ease-out';
            setTimeout(() => flash.remove(), 300);
        });
    }
}