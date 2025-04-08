if (line1) {
    var saveAddressBtn = document.getElementById('save_address');
    var line2 = document.getElementById('id_line2');
    var line3 = document.getElementById('id_line3');
    var line4 = document.getElementById('id_line4');
    var fieldsErrors = document.querySelector('[data-id="checkout-error-list"]');
    var errorAddress = fieldsErrors.querySelector('[data-error="address"]');
    var errorFlat = fieldsErrors.querySelector('[data-error="flat"]');
    var errorEnter = fieldsErrors.querySelector('[data-error="enter"]');
    var errorFloor = fieldsErrors.querySelector('[data-error="floor"]');

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
    document.querySelectorAll('[data-id="input-field"]').forEach(function (wrapper) {
        var inputField = wrapper.querySelector('.input');
        if (inputField.value !== "") {
            wrapper.classList.add('input__label-active');
        }
        inputField.addEventListener('focusin', function () {
            wrapper.classList.add('input__label-active');
        });
        inputField.addEventListener('focusout', function () {
            if (inputField.value === "") {
                wrapper.classList.remove('input__label-active');
            }
            validateAddress();
        });
    });

    // Не отправлять форму при нажатии Enter
    document.getElementById('edit-address').addEventListener('keypress', function (event) {
        if (event.target.tagName === 'INPUT' && event.key === 'Enter') {
            event.preventDefault();
        }
    });

    // Валидация адреса
    function validateAddress() {
        var valid = true;

        // Проверка поля line1
        if (!line1.value || line1.getAttribute('captured') != "true" || line1.getAttribute('valid') != "true") {
            valid = false;
            errorAddress.classList.remove('d-none');
            line1_container.classList.add("not-valid");
        } else {
            errorAddress.classList.add('d-none');
            line1_container.classList.add("not-valid");
        }

        // Проверка поля line2
        if (line2.value > 1000 || line2.value < 1) {
            valid = false;
            errorFlat.classList.remove('d-none');
            line2.classList.add("not-valid");
        } else {
            errorFlat.classList.add('d-none');
            line2.classList.remove("not-valid");
        }

        // Проверка поля line3
        if (line3.value > 100 || line3.value < 1) {
            valid = false;
            errorEnter.classList.remove('d-none');
            line3.classList.add("not-valid");
        } else {
            errorEnter.classList.add('d-none');
            line3.classList.remove("not-valid");
        }

        // Проверка поля line4
        if (line4.value > 100 || line4.value < 1) {
            valid = false;
            errorFloor.classList.remove('d-none');
            line4.classList.add("not-valid");
        } else {
            errorFloor.classList.add('d-none');
            line4.classList.remove("not-valid");
        }

        // Управление доступностью кнопки сохранения и ошибок
        saveAddressBtn.disabled = !valid;
        fieldsErrors.classList.toggle('d-none', valid);
    }
}

