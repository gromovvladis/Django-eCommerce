let activeIntervals = new Map(); // Храним ID интервалов для каждого элемента
let debounceTimeout; // Для уменьшения частоты вызовов startUpdatingBadges

// Функция обновления одного badge
const updateBadge = (badge) => {
    try {
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
    } catch (error) {
        console.error("Error updating badge:", error);
    }
};

// Запускаем обновление для всех badge
const startUpdatingBadges = (badgeElements) => {
    badgeElements.forEach((badge) => {
        if (activeIntervals.has(badge)) return;
        updateBadge(badge);
        const intervalId = setInterval(() => {
            if (!document.body.contains(badge)) {
                clearInterval(intervalId);
                activeIntervals.delete(badge);
            } else {
                updateBadge(badge);
            }
        }, 60000);
        activeIntervals.set(badge, intervalId); // Сохраняем ID интервала
    });
    // Очищаем интервал для удалённых элементов
    activeIntervals.forEach((intervalId, badge) => {
        if (!document.body.contains(badge)) {
            clearInterval(intervalId);
            activeIntervals.delete(badge);
        }
    });
};


const badgeChanged = (allBadges) => {
    const newBadges = new Set(allBadges); // Уникальный набор всех текущих бейджей

    // Удаляем интервалы для элементов, которых больше нет
    activeIntervals.forEach((intervalId, badge) => {
        if (!newBadges.has(badge)) { // Если бейджа нет в текущем наборе
            clearInterval(intervalId); // Очищаем интервал
            activeIntervals.delete(badge); // Удаляем из активных интервалов
        }
    });

    // Добавляем или обновляем существующие бейджи
    allBadges.forEach((badge) => {
        if (!activeIntervals.has(badge)) { // Если бейдж ещё не отслеживается
            updateBadge(badge); // Обновляем его сразу
            const intervalId = setInterval(() => {
                if (!document.body.contains(badge)) { // Если бейдж удалён
                    clearInterval(intervalId); // Удаляем интервал
                    activeIntervals.delete(badge); // Удаляем из активных интервалов
                } else {
                    updateBadge(badge); // Иначе обновляем бейдж
                }
            }, 60000);
            activeIntervals.set(badge, intervalId); // Добавляем в активные интервалы
        }
    });
};

badgeChanged(document.querySelectorAll('span[data-id="order-badge"]'));
