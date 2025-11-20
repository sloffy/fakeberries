document.addEventListener('DOMContentLoaded', () => {
    initFlashClose();
    initFileInputHints();
});

function initFlashClose() {
    document.querySelectorAll('[data-close-flash]').forEach(button => {
        button.addEventListener('click', () => {
            const flash = button.closest('.fb-flash');
            if (flash) {
                flash.remove();
            }
        });
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