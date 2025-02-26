const CACHE_NAME = 'pwa-cache-v1';
const urlsToCache = [
  '/',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Установка Service Worker и кэширование ресурсов
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

// Перехват сетевых запросов
self.addEventListener('fetch', (event) => {
  event.respondWith(
      caches.match(event.request).then((response) => {
          return response || fetch(event.request).then((networkResponse) => {
              if (event.request.url.includes('/static/')) {
                  return caches.open(CACHE_NAME).then((cache) => {
                      cache.put(event.request, networkResponse.clone());
                      return networkResponse;
                  });
              }
              return networkResponse;
          });
      }).catch((error) => console.error('Ошибка загрузки ресурса:', error))
  );
});

self.addEventListener('push', function (event) {
  const data = event.data.json();
  self.registration.showNotification(data.title, {
    body: data.body,
    icon: data.icon || '/static/icons/default.png'
  });
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  if (event.notification.data && event.notification.data.url) {
    clients.openWindow(event.notification.data.url);
  }
});