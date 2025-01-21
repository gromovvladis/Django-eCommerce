
var waitingPayment = document.querySelector('[data-id="waiting-payment"]');
var paymentStatus = document.querySelector('[data-id="payment-status"]');
var paymentSvg = document.querySelector('[data-id="payment-icon-svg"]');
var waitingSeconds = 15;
var interval;

if (waitingPayment) {
    getPaymentInfo();
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
        closeModal(data);
    })
    .catch(error => console.error('Error:', error));
}

function closeModal(response = null) {
    if (!response?.order_status) return;

    const { order_status } = response;

    if (paymentStatus) {
        paymentStatus.innerHTML = order_status;
    }

    if (paymentSvg) {
        const svgMap = {
            "Ожидает оплаты": "#svg-order-pending",
            "Отменен": "#svg-order-cancel",
        };
        const svgHref = svgMap[order_status] || "#svg-order-success";
        paymentSvg.innerHTML = `<use xlink:href="${svgHref}"></use>`;
    }

    clearInterval(interval);

    if (waitingPayment) {
        waitingPayment.classList.add('d-none');
    }
}
