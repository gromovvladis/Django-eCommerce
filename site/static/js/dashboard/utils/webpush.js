if ('serviceWorker' in navigator && 'PushManager' in window) {
  if (Notification.permission != 'denied') {
    subscribe();
  }
}

function subscribe() {
  navigator.serviceWorker.ready
    .then(function (registration) {
      // Подписываемся на push-уведомления
      return registration.pushManager.subscribe({
        userVisibleOnly: true, // Гарантируем, что уведомления будут отображаться пользователю
        applicationServerKey: 'BHuErJY5HcTiN8iGz5EOBgCP_vGhjrQmHhYMb81qP7hgmDm6IW2PmriE-GSVOOzlTLCqz5gbQKWhJc7R2OE437Q' // Ваш публичный VAPID ключ
      });
    })
    .then(function (subscription) {
      // Извлекаем токен из endpoint
      const currentToken = extractToken(subscription.endpoint);
      // Отправляем данные подписки на сервер
      return sendTokenToServer(currentToken, subscription);
    })
    .catch(function (error) {
      console.error('Ошибка подписки на уведомления:', error);
    });
}

// Извлечение токена из endpoint
function extractToken(endpoint) {
  return endpoint.split('/').pop(); // Последний сегмент URL — это токен
}

// Отправка ID на сервер
function sendTokenToServer(currentToken, subscription) {
  if (!isTokenSentToServer(currentToken)) {
    // Отправляем данные подписки на сервер
    console.log('Сохранение подписки на сервере:', webpush_save_url);
    fetch(webpush_save_url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token // Замените на ваш CSRF токен
      },
      body: JSON.stringify({ subscription })
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Не удалось сохранить подписку на сервере.');
        }
        return response.json();
      })
      .then(function (data) {
        console.log('Подписка успешно сохранена:', data);
        setTokenSentToServer(currentToken);
      })
      .catch(function (error) {
        console.error('Ошибка сохранения подписки на сервере:', error);
      });
  }
}

// Используем localStorage для отметки, что пользователь уже подписался на уведомления
function isTokenSentToServer(currentToken) {
  return window.localStorage.getItem('sentFirebaseMessagingToken') === currentToken;
}

function setTokenSentToServer(currentToken) {
  window.localStorage.setItem(
    'sentFirebaseMessagingToken',
    currentToken ? currentToken : ''
  );
}
