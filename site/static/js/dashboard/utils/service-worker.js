self.addEventListener('push', function(event) {
  const data = event.data.json();
  self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon || '/static/icons/default.png'
  });
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  if (event.notification.data && event.notification.data.url) {
      clients.openWindow(event.notification.data.url);
  }
});