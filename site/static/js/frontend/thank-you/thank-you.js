
var waitingPayment = document.querySelector('[data-id="waiting-payment"]');
var paymentStatus = document.querySelector('[data-id="payment-status"]');
var paymentSvg = document.querySelector('[data-id="payment-icon-svg"]');
var waitingSeconds = 15;
var interval;

if (waitingPayment) {
    interval = setInterval(function() {
        if (waitingSeconds > 0) {
            waitingSeconds -= 3;
            getPaymentInfo();
        } else {
            closeModal();
            if (paymentStatus) {
                paymentStatus.innerHTML = "Ответ от банка не получен. Обновите страницу";
            }
        }
    }, 3000);
}

function getPaymentInfo() {
    fetch(update_payment_url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token,
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        closeModal(data);
    })
    .catch(error => console.error('Error:', error));
}

function closeModal(response = null) {
    console.log(response);
    if (response) {
        if (paymentStatus) {
            paymentStatus.innerHTML = response.status;
        }
        if (paymentSvg) {
            if (response.status === "Ожидает оплаты") {
                paymentSvg.innerHTML = '<use xlink:href="#svg-order-pending"></use>';
            } else if (response.status === "Отменен") {
                paymentSvg.innerHTML = '<use xlink:href="#svg-order-cancel"></use>';
            } else {
                paymentSvg.innerHTML = '<use xlink:href="#svg-order-success"></use>';
            }
        }
    }
    clearInterval(interval);
    if (waitingPayment) {
        waitingPayment.classList.add('d-none');
    }
}
