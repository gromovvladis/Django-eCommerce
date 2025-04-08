if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
        .catch(err => console.error('Ошибка регистрации Service Worker', err));
}