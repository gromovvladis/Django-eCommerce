let activeIntervals = new Map(); // Храним ID интервалов для каждого элемента
let debounceTimeout; // Для уменьшения частоты вызовов startUpdatingBadges

// Функция обновления одного badge
const updateBadge = (badge) => {
    const seconds = parseInt(badge.dataset.seconds, 10);
    if (isNaN(seconds)) return;
    const newSeconds = seconds - 60; // Уменьшаем на 1 минуту
    badge.dataset.seconds = newSeconds;

    const absSeconds = Math.abs(newSeconds);
    const inFuture = newSeconds > 0;

    // Определяем текст и цвет бейджа
    let badgeText = "";
    let badgeClass = "";

    if (absSeconds >= 86400) { // 1 день в секундах
        const days = Math.floor(absSeconds / 86400);
        const hours = Math.floor((absSeconds % 86400) / 3600);
        badgeText = `${days} дн. ${hours} ч.`;
        badgeClass = inFuture ? "badge-success" : "badge-danger";
    } else if (absSeconds >= 3600) { // 1 час в секундах
        const hours = Math.floor(absSeconds / 3600);
        const minutes = Math.floor((absSeconds % 3600) / 60);
        badgeText = `${hours} ч. ${minutes} мин.`;
        badgeClass = inFuture ? "badge-success" : "badge-danger";
    } else {
        const minutes = Math.floor(absSeconds / 60);
        badgeText = `${minutes} мин.`;
        badgeClass = inFuture 
            ? (minutes < 5 ? "badge-warning" : "badge-success")
            : "badge-danger";
    }

    // Обновляем текст и класс
    badge.textContent = badgeText;
    badge.className = `badge ${badgeClass}`;
};

// Запускаем обновление для всех badge
const startUpdatingBadges = (badgeElements) => {
    badgeElements.forEach((badge) => {
        if (activeIntervals.has(badge)) return;
        const intervalId = setInterval(() => updateBadge(badge), 60000);
        activeIntervals.set(badge, intervalId); // Сохраняем ID интервала
    });

    // Удаляем интервалы для элементов, которые больше не существуют
    activeIntervals.forEach((intervalId, badge) => {
        if (!document.body.contains(badge)) {
            clearInterval(intervalId);
            activeIntervals.delete(badge);
        }
    });
};

// Обработчик изменений в DOM
const handleDomChanges = () => {
    const badgeElements = document.querySelectorAll('span[data-id="order-badge"]');
    startUpdatingBadges(badgeElements);
};

// Наблюдаем за изменениями в DOM
const observer = new MutationObserver(() => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(handleDomChanges, 5000); // Debounce для уменьшения частоты вызовов
});

// Запускаем наблюдение за основным контейнером
observer.observe(document.body, { childList: true, subtree: true });

// Инициализация
handleDomChanges();
