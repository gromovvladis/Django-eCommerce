// Получаем элементы по идентификатору и атрибутам
var saveAddress = document.getElementById('save_address');
// var line1 = document.getElementById('id_line1'); // предполагается, что line1 уже был объявлен
var line2 = document.getElementById('id_line2');
var line3 = document.getElementById('id_line3');
var line4 = document.getElementById('id_line4');
var checkoutErrors = document.querySelector('[data-id="checkout-error-list"]');
var errorAddress = checkoutErrors.querySelector('[data-error="address"]');
var errorFlat = checkoutErrors.querySelector('[data-error="flat"]');
var errorEnter = checkoutErrors.querySelector('[data-error="enter"]');
var errorFloor = checkoutErrors.querySelector('[data-error="floor"]');

// Инициализация адреса при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    var adr = line1.value;
    if (adr) {
        line1.readOnly = true;
        line1.setAttribute('captured', 'true');
        createMap(adr);
    }
    validateAddress();
});

// Активируем метки в полях ввода и добавляем обработчики событий
document.querySelectorAll('[data-id="v-input-field"]').forEach(function(wrapper) {
    var inputField = wrapper.querySelector('.v-input');
    if (inputField.value !== "") {
        wrapper.classList.add('v-input__label-active');
    }
    inputField.addEventListener('focusin', function() {
        wrapper.classList.add('v-input__label-active');
    });
    inputField.addEventListener('focusout', function() {
        if (inputField.value === "") {
            wrapper.classList.remove('v-input__label-active');
        }
        validateAddress();
    });
});

// Не отправлять форму при нажатии Enter
document.getElementById('edit-address').addEventListener('keypress', function(event) {
    if (event.target.tagName === 'INPUT' && event.key === 'Enter') {
        event.preventDefault();
    }
});

// Валидация адреса
function validateAddress() {
    var valid = true;
    
    // Проверка поля line1
    if (!line1.value || line1.getAttribute('captured') === "false" || line1.getAttribute('valid') === "false") {
        console.log('line1 invalid');
        valid = false;
        errorAddress.classList.remove('d-none');
        line1.classList.add("not-valid");
    } else {
        errorAddress.classList.add('d-none');
        line1.classList.remove("not-valid");
    }

    // Проверка поля line2
    if (line2.value > 1000 || line2.value < 1) {
        console.log('line2 invalid');
        valid = false;
        errorFlat.classList.remove('d-none');
        line2.classList.add("not-valid");
    } else {
        errorFlat.classList.add('d-none');
        line2.classList.remove("not-valid");
    }

    // Проверка поля line3
    if (line3.value > 100 || line3.value < 1) {
        console.log('line3 invalid');
        valid = false;
        errorEnter.classList.remove('d-none');
        line3.classList.add("not-valid");
    } else {
        errorEnter.classList.add('d-none');
        line3.classList.remove("not-valid");
    }

    // Проверка поля line4
    if (line4.value > 100 || line4.value < 1) {
        console.log('line4 invalid');
        valid = false;
        errorFloor.classList.remove('d-none');
        line4.classList.add("not-valid");
    } else {
        errorFloor.classList.add('d-none');
        line4.classList.remove("not-valid");
    }

    console.log("validate " + valid);

    // Управление доступностью кнопки сохранения и ошибок
    saveAddress.disabled = !valid;
    checkoutErrors.classList.toggle('d-none', valid);
}
