const CACHE_NAME = 'pwa-cache-v4';
const urlsToCache = [
  '/',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Установка Service Worker и кэширование ресурсов
self.addEventListener('install', (event) => {
  self.skipWaiting(); // Немедленно активируем новый SW
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
      .catch((err) => console.error('Ошибка кэширования:', err))
  );
});

// Очистка старого кэша при активации нового Service Worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('Удаление старого кэша:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim()) // Немедленно активируем новый SW для всех вкладок
  );
});

// Перехват сетевых запросов и динамическое обновление кэша
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cachedResponse = await cache.match(event.request);

      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (event.request.url.includes('/static/')) {
          cache.put(event.request, networkResponse.clone()); // Обновляем кэш
        }
        return networkResponse;
      }).catch((err) => console.error('Ошибка загрузки:', err));

      return cachedResponse || fetchPromise;
    }).catch((err) => console.error('Ошибка работы с кэшем:', err))
  );
});

// Принудительное обновление всех вкладок при обновлении SW
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
});

self.addEventListener('push', function (event) {
  const data = event.data.json();
  self.registration.showNotification(data.title, {
    body: data.body,
    icon: data.icon || '/static/icons/default.png',
    data: { url: data.url } // Добавляем URL для открытия
  });
});

// Открытие ссылки по клику на уведомление
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  if (event.notification.data && event.notification.data.url) {
    event.waitUntil(clients.openWindow(event.notification.data.url));
  }
});
