if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
        .then(reg => console.log('Service Worker зарегистрирован', reg))
        .catch(err => console.log('Ошибка регистрации Service Worker', err));
}