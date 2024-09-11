var cart_nums = document.querySelectorAll('[data-id="cart-nums"]');
var cartAdded = () => {};

document.addEventListener('DOMContentLoaded', function () {
    findNewForms();
});

function findNewForms() {
    var addBasketCompactForms = document.querySelectorAll("[data-id='add-to-cart-form-compact']");
    
    if (addBasketCompactForms.length > 0) {
        addBasketCompactForms.forEach(function (form) {
            form.addEventListener('submit', function (event) {
                event.preventDefault(); // Предотвращаем стандартное действие формы
                
                var btn = form.querySelector('[data-id="add-to-cart-btn-compact"]');
                var span = btn.querySelector('[data-id="add-to-cart-btn-span"]');
                btn.disabled = true;
                btn.classList.add('clicked');
                var btnText = span.innerHTML;
                span.innerHTML = 'Добавлено';

                var xhr = new XMLHttpRequest();
                xhr.open(form.method, form.action, true);
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.onload = function () {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        var response = JSON.parse(xhr.responseText);
                        cart_nums.forEach(function(element) {
                            element.innerHTML = response.cart_nums; // Вставляем HTML в каждый элемент
                        });
                        cartAdded();
                    } else if (xhr.status >= 400 && xhr.status < 500) {
                        var errorElement = btn.closest('.product-description').querySelector('[data-id="add-to-cart-error-compact"]');
                        errorElement.innerHTML = response.errors;
                    }
                };
                xhr.onerror = function () {
                    console.error('Error occurred during the request');
                };
                xhr.onloadend = function () {
                    btn.disabled = false;
                    btn.classList.remove('clicked');
                    span.innerHTML = btnText;
                };
                xhr.send(new URLSearchParams(new FormData(form)).toString());
            });
        });
    }
}
