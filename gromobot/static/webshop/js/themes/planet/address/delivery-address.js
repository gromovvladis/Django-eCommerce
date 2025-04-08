var setAddressForm = document.getElementById('set_address');

// Инициализация адреса при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    var adr = getCookie("line1");

    if (adr && line1) {
        line1.readOnly = true;
        line1.setAttribute('captured', 'true');
        createMap(adr);
    }
});

// Обработчик отправки формы
setAddressForm.addEventListener('submit', function (event) {
    event.preventDefault(); // Отмена стандартного поведения отправки формы

    fetch(setAddressForm.action, {
        method: setAddressForm.method,
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf_token,
        },
        body: new URLSearchParams(new FormData(setAddressForm)).toString()
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.text(); // или response.json(), если ожидается JSON
        })
        .catch(error => {
            console.error('Error:', error); // обработка ошибок
        });
});

// Запрет отправки формы при нажатии Enter
setAddressForm.addEventListener('keypress', function (event) {
    if (event.target.tagName === 'INPUT' && event.key === 'Enter') {
        event.preventDefault();
    }
});

// Обработчик для кнопки сохранения
saveButton.addEventListener('click', function () {
    setTimeout(function () {
        setAddressForm.dispatchEvent(new Event('submit'));
    }, 0);
});
