
var addressFields = document.getElementById('address_fields');
var submitBtn = document.getElementById('submit_order');

var checkoutErrors = document.querySelector('[data-id="checkout-error-list"]');
var errorAddress = checkoutErrors.querySelector('[data-error="address"]');
var errorFlat = checkoutErrors.querySelector('[data-error="flat"]');
var errorEnter = checkoutErrors.querySelector('[data-error="enter"]');
var errorFloor = checkoutErrors.querySelector('[data-error="floor"]');
var errorAmount = checkoutErrors.querySelector('[data-error="amount"]');

var amountValid = true;
var addressValid = true;

var orderTime = document.getElementById('id_order_time');
var deliveryTimeBtn = document.querySelectorAll('[data-id="delivery-time"]');
var deliveryTimeLater = document.getElementById('delivery_time_later');

var shippingMethodButtons = document.querySelectorAll('[data-id="delivery-method-button"]');
var methodSwaper = document.querySelector('[data-id="delivery-method-block"]');
var timeSwaper = document.querySelector('[data-id="delivery-time-block"]');
var timeTitle = document.querySelector('[data-id="order-time-title"]');
var shipping = document.getElementById('id_method_code');

var checkoutTotals = document.getElementById('checkout_totals');
var checkout_fields = document.querySelectorAll('[data-id="input-field"]');
var textares = document.querySelectorAll('textarea');
var paymentMethod = document.getElementById('id_payment_method');
var line2 = document.getElementById('id_line2');
var line3 = document.getElementById('id_line3');
var line4 = document.getElementById('id_line4');
var emailBlock = document.querySelector('[data-field="email-field"]');
var emailField = emailBlock.querySelector('#email_field_label');

const OFFLINE_PAYMENT = ['CASH', 'ELECTRON'];
const ONLINE_PAYMENT = ['SBP', 'ONLINECARD'];
const baseURL = window.location.origin;

var deliveryTimeMethod = "now";

// Инициализация адреса
document.addEventListener('DOMContentLoaded', function () {
    if (line1) {
        var addressInital = line1.value;
        if (addressInital) {
            line1.readOnly = true;
            line1.setAttribute('captured', true);
            createMap(addressInital);
        }
    }
    validateCheckout();
    textares.forEach(function (textarea) {
        if (textarea.scrollHeight < 77) {
            textarea.style.height = textarea.scrollHeight + 'px';
        } else {
            textarea.style.height = '77px';
        }
    });
});

// Смена метода доставки
if (shippingMethodButtons.length > 0) {
    shippingMethodButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            shippingMethod = this.value;
            shipping.value = shippingMethod;
            let leftPosition = this.getBoundingClientRect().left - this.parentElement.getBoundingClientRect().left;
            methodSwaper.style.left = `${leftPosition}px`;
            GetTime({ address: line1.value, coords: [lon.value, lat.value], shippingMethod: shippingMethod }).then(function (result) {
                timeCaptured(result);
            });
            if (shippingMethod === "self-pick-up") {
                addressFields.classList.add('d-none');
                timeTitle.innerHTML = 'Время самовывоза';
            } else {
                addressFields.classList.remove('d-none');
                timeTitle.innerHTML = 'Время доставки';
            }
            getNewTotals(shippingMethod);
        });
    });
}

// Выбрана доставка "самовывоз как можно скорее"
deliveryTimeBtn.forEach(function (time_btn) {
    time_btn.addEventListener('click', function () {
        let leftPosition = time_btn.getBoundingClientRect().left - time_btn.parentElement.getBoundingClientRect().left;
        timeSwaper.style.left = `${leftPosition}px`;
        deliveryTimeMethod = time_btn.getAttribute("data-type");
        if (deliveryTimeMethod === "now") {
            if (addressFields) {
                GetTime({ address: line1.value, coords: [lon.value, lat.value], shippingMethod: shippingMethod }).then(function (result) {
                    orderTime.value = result.timeUTC;
                    timeCaptured(result);
                });
            } else {
                GetTime({ shippingMethod: shippingMethod }).then(function (result) {
                    orderTime.value = result.timeUTC;
                    timeCaptured(result);
                });
            }
            deliveryTimeLater.classList.add('hidden');
            deliveryTimeLater.classList.remove('active');
        } else {
            deliveryTimeLater.classList.remove('hidden');
            deliveryTimeLater.classList.add('active');
            deliveryTime.classList.add('hidden');
            deliveryTime.classList.remove('active');
        }
    });
});

// Обновление итогов
function getNewTotals(selectedMethod, zonaId = null) {
    console.log('getNewTotals');

    // Формируем параметры запроса в URL
    const url = new URL(url_update_totals, baseURL);
    url.searchParams.append('shippingMethod', selectedMethod);
    // if (zonaId) {
    url.searchParams.append('zona_id', zonaId);
    // }


    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 202) {
                checkoutTotals.innerHTML = data.totals;
                errorAmount.innerHTML = data.min_order;
            }
        })
        .finally(() => {
            validateCheckout();
        });
}

// Сдача или чек
paymentMethod.addEventListener('change', function () {
    if (OFFLINE_PAYMENT.includes(this.value)) {
        emailField.innerHTML = 'Нужна сдача с ...';
        emailBlock.classList.remove('d-none-i');
    } else if (ONLINE_PAYMENT.includes(this.value)) {
        emailField.innerHTML = 'E-mail для получения чеков';
        emailBlock.classList.remove('d-none-i');
    } else {
        emailBlock.classList.add('d-none-i');
    }
});

// Лейблы при заполнении текста
checkout_fields.forEach(function (wrapper) {
    var input_field = wrapper.querySelector('.input');
    if (input_field.value !== "") {
        wrapper.classList.add('input__label-active');
    }
    input_field.addEventListener('focusin', function () {
        wrapper.classList.add('input__label-active');
    });
    input_field.addEventListener('focusout', function () {
        if (input_field.value === "") {
            wrapper.classList.remove('input__label-active');
        }
        validateAddress();
        checkValid();
    });
});

// Авторасширение текстовых полей
textares.forEach(function (textarea) {
    textarea.addEventListener('input', function () {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    });
    textarea.addEventListener('scroll', function () {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    });
});

// Не отправлять форму enter-ом
document.getElementById('place_order_form').addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
    }
});

function validate() {
    validateCheckout();
}

// Валидация по мин заказу и адресу
function validateCheckout() {
    console.log('validateCheckout');
    validateAddress();
    validateTotals();
    checkValid();
}

function checkValid() {
    if (amountValid && addressValid) {
        submitBtn.disabled = false;
        checkoutErrors.classList.add('d-none');
    } else {
        submitBtn.disabled = true;
        checkoutErrors.classList.remove('d-none');
    }
}

// Валидация по адресу
function validateAddress() {
    if (addressFields) {
        addressValid = true;
        shippingMethod = shipping.value;
        if (shippingMethod === "zona-shipping") {
            if (!line1.value || line1.getAttribute('captured') != "true" || line1.getAttribute('valid') != "true") {
                addressValid = false;
                errorAddress.classList.remove('d-none');
                line1_container.classList.add("not-valid");
            } else {
                errorAddress.classList.add('d-none');
                line1_container.classList.remove("not-valid");
            }

            if (line2.value > 1000 || line2.value < 1) {
                addressValid = false;
                errorFlat.classList.remove('d-none');
                line2.classList.add("not-valid");
            } else {
                errorFlat.classList.add('d-none');
                line2.classList.remove("not-valid");
            }

            if (line3.value > 100 || line3.value < 1) {
                addressValid = false;
                errorEnter.classList.remove('d-none');
                line3.classList.add("not-valid");
            } else {
                errorEnter.classList.add('d-none');
                line3.classList.remove("not-valid");
            }

            if (line4.value > 100 || line4.value < 1) {
                addressValid = false;
                errorFloor.classList.remove('d-none');
                line4.classList.add("not-valid");
            } else {
                errorFloor.classList.add('d-none');
                line4.classList.remove("not-valid");
            }
        }
    }
}

// Валидация по сумме заказа
function validateTotals() {
    amountValid = true;
    if (checkoutTotals.querySelector('[data-min-order]').getAttribute("data-min-order") === "false" && shippingMethod === "zona-shipping") {
        amountValid = false;
        errorAmount.classList.remove('d-none');
    } else {
        errorAmount.classList.add('d-none');
    }
}

// Начисляем стоимость доставки в зависимости от зоны
function shippingCharge(zonaId = null) {
    getNewTotals(shippingMethod, zonaId);
}

// Loading spinner
submitBtn.addEventListener('click', function () {
    this.classList.add('sending');
});

// Таймер обновления времени доставки к адресу каждые 2.5 минут
function updateTimes() {
    if (deliveryTimeMethod === "now" && deliveryTimeLater.classList.contains("hidden")) {
        if (addressFields) {
            GetTime({ address: line1.value, coords: [lon.value, lat.value], shippingMethod: shippingMethod }).then(function (result) {
                orderTime.value = result.timeUTC;
                timeCaptured(result);
            });
        } else {
            GetTime({ shippingMethod: shippingMethod }).then(function (result) {
                orderTime.value = result.timeUTC;
                timeCaptured(result);
            });
        }
    }
}

setInterval(function () { updateTimes() }, 300000);
updateTimes();
