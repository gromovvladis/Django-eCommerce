var cartNums = document.querySelectorAll('[data-id="cart-nums"]');
var cartAdded = () => {};

document.addEventListener('DOMContentLoaded', function () {
    findNewForms();
});

function findNewForms() {
    var addBasketCompactForms = document.querySelectorAll("[data-id='add-to-cart-form-compact']");
    
    if (addBasketCompactForms.length > 0) {
        addBasketCompactForms.forEach(function (form) {
            form.addEventListener('submit', function (event) {
                event.preventDefault();
                
                const btn = form.querySelector('[data-id="add-to-cart-btn-compact"]');
                const span = btn.querySelector('[data-id="add-to-cart-btn-span"]');
                btn.disabled = true;
                btn.classList.add('clicked');
                const btnText = span.innerHTML;
                span.innerHTML = 'Добавлено';

                fetch(form.action, {
                    method: form.method,
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrf_token,
                    },
                    body: new URLSearchParams(new FormData(form))
                })
                .then(response => response.json().then(data => ({ status: response.status, data })))
                .then(({ status, data }) => {
                    if (status >= 200 && status < 300) {
                        cartNums.forEach(element => {
                            element.innerHTML = data.cart_nums; // Вставляем HTML в каждый элемент
                        });
                        cartAdded();
                    } else if (status >= 400 && status < 500) {
                        const errorElement = btn.closest('.product-description').querySelector('[data-id="add-to-cart-error-compact"]');
                        errorElement.innerHTML = '<div class="error-badge">' + data.errors + "</div>";
                    }
                })
                .catch(error => {
                    console.error('Error occurred during the request', error);
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.classList.remove('clicked');
                    span.innerHTML = btnText;
                });

            });
        });
    }
}
