
if ('serviceWorker' in navigator && 'PushManager' in window) {
  console.log('Поддерживается Service Worker и PushManager.');

  if (Notification.permission != 'denied') {
    subscribe();
  }

} else {
  console.error('Service Worker или PushManager не поддерживаются в этом браузере.');
}


function subscribe() {

  // Регистрируем Service Worker
  navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
    .then(function (registration) {
      console.log('Service Worker успешно зарегистрирован:', registration);

      // Дожидаемся готовности Service Worker
      return navigator.serviceWorker.ready;
    })
    .then(function (registration) {
      console.log('Service Worker готов:', registration);

      // Подписываемся на push-уведомления
      return registration.pushManager.subscribe({
        userVisibleOnly: true, // Гарантируем, что уведомления будут отображаться пользователю
        applicationServerKey: 'BHuErJY5HcTiN8iGz5EOBgCP_vGhjrQmHhYMb81qP7hgmDm6IW2PmriE-GSVOOzlTLCqz5gbQKWhJc7R2OE437Q' // Ваш публичный VAPID ключ
      });
    })
    .then(function (subscription) {
      console.log('Подписка на push-уведомления успешно создана:', subscription);

      // Отправляем данные подписки на сервер
      return sendTokenToServer(subscription)
    })
    .catch(function (error) {
      console.error('Произошла ошибка:', error);
    });
}


// отправка ID на сервер
function sendTokenToServer(subscription) {
  currentToken = subscription.token
  if (!isTokenSentToServer(currentToken)) {
    console.log('Отправка токена на сервер...');

    // Отправляем данные подписки на сервер
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
        console.log('Ответ от сервера:', data);
      });

    setTokenSentToServer(currentToken);
  } else {
    console.log('Токен уже отправлен на сервер.');
  }
}

// используем localStorage для отметки того,
// что пользователь уже подписался на уведомления
function isTokenSentToServer(currentToken) {
  return window.localStorage.getItem('sentFirebaseMessagingToken') == currentToken;
}

function setTokenSentToServer(currentToken) {
  window.localStorage.setItem(
    'sentFirebaseMessagingToken',
    currentToken ? currentToken : ''
  );
}





