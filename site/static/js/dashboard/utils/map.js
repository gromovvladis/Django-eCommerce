function openMap(destination) {
    
    const yandexMapAppUrl = `yandexmaps://maps.yandex.ru/?text=Красноясрк,%20${encodeURIComponent(destination)}`;
    const yandexMapWebUrl = `https://yandex.ru/maps/?text=Красноясрк,%20${encodeURIComponent(destination)}`;
    // Проверяем, является ли устройство мобильным
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    if (isMobile) {
        // Попробуем открыть приложение Яндекс.Карты
        window.open(yandexMapAppUrl, '_blank');
        // Если приложение не установлено, откроется веб-версия
        setTimeout(() => {
            window.open(yandexMapWebUrl, '_blank');
        }, 500); // Задержка для обработки попытки открытия приложения
    } else {
        // Открываем веб-версию на ПК
        window.open(yandexMapWebUrl, '_blank');
    }
}

function createRote(destination) {
  
  const yandexRouteAppUrl = `yandexmaps://maps.yandex.ru/?rtext=~Красноясрк,%20${encodeURIComponent(destination)}&rtt=auto`;
  const yandexRouteWebUrl = `https://yandex.ru/maps/?rtext=~Красноясрк,%20${encodeURIComponent(destination)}&rtt=auto`;
  // Проверяем, является ли устройство мобильным
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

  if (isMobile) {
      // Попробуем открыть приложение Яндекс.Карты
      window.open(yandexRouteAppUrl, '_blank');
      // Если приложение не установлено, откроется веб-версия
      setTimeout(() => {
          window.open(yandexRouteWebUrl, '_blank');
      }, 500); // Задержка для обработки попытки открытия приложения
  } else {
      // Открываем веб-версию на ПК
      window.open(yandexRouteWebUrl, '_blank');
  }
}
