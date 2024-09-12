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

    var xhr = new XMLHttpRequest();
    xhr.open(setAddressForm.method, setAddressForm.action, true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.send(new URLSearchParams(new FormData(setAddressForm)).toString());
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
