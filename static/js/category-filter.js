document.addEventListener('DOMContentLoaded', function() {
    const categoryCheckboxes = document.querySelectorAll('.category-checkbox:not(#categoryAll)');
    const allCheckbox = document.getElementById('categoryAll');
    const categoryCards = document.querySelectorAll('.category-filter-card');
    
    // Обработчик для чекбокса "Все категории"
    if (allCheckbox) {
        allCheckbox.addEventListener('change', function() {
            if (this.checked) {
                // Сбрасываем все категории и переходим на главную
                window.location.href = '/';
            }
        });
    }
    
    // Обработчик для чекбоксов категорий
    categoryCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateCategoryFilter();
        });
    });
    
    // Клик по карточке переключает чекбокс
    categoryCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Не реагируем если кликнули по самому чекбоксу или label
            if (e.target.type === 'checkbox' || e.target.tagName === 'LABEL') {
                return;
            }
            
            const categoryId = this.dataset.categoryId;
            const checkbox = document.getElementById('category' + categoryId);
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                updateCategoryFilter();
            }
        });
    });
    
    // Функция обновления фильтра
    function updateCategoryFilter() {
        // Собираем ID выбранных категорий
        const selectedIds = Array.from(categoryCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        // Если ничего не выбрано, переходим на главную (все товары)
        if (selectedIds.length === 0) {
            window.location.href = '/';
            return;
        }
        
        // Формируем URL с параметрами
        const categoriesParam = selectedIds.join(',');
        window.location.href = '/?categories=' + categoriesParam;
    }
});
