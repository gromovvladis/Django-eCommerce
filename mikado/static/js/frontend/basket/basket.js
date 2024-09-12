var cartWrapper = document.querySelector('[data-id="cart-wrapper"]');

if (cartWrapper){
    var basketSummary = cartWrapper.querySelector('[data-id="basket-formset"]');
    var upsellMessages = cartWrapper.querySelector('#upsell_messages');
    var cartTotals = document.querySelector('[data-id="cart-info"]');
    var basketTotals = document.querySelectorAll('[data-id="cart-totals"]');
    var modalEmptyCart = document.querySelector('[data-id="modal-empty-cart"]');
    var emptyCart = modalEmptyCart.querySelector('[data-id="empty-cart"]');
    var openCloseModal = document.querySelectorAll('[data-id="modal-open-close"]');
    
    var basketSummary = cartWrapper.querySelector('[data-id="basket-formset"]');
    var forms = basketSummary.querySelectorAll('[data-id="cart-item-form"]');

    forms.forEach(function(form_item) {
        var quantity = form_item.querySelector('[data-id="quantity-input"]');
        var more = form_item.querySelector('[data-id="order-button-plus"]');
        var less = form_item.querySelector('[data-id="order-button-minus"]');
        var clean = form_item.querySelector('[data-id="dish-order-delete-link"]');

        if (quantity.value == quantity.getAttribute('max')) {
            more.disabled = true;
        }

        more.addEventListener('click', function() {
            if (parseInt(quantity.value) < parseInt(quantity.getAttribute('max'))) {
                quantity.value = parseInt(quantity.value) + 1;
                less.disabled = false;
            }
            if (parseInt(quantity.value) == parseInt(quantity.getAttribute('max'))) {
                this.disabled = true;
            }
            form_item.classList.remove('empty');
            basketForm();
        });

        less.addEventListener('click', function() {
            if (parseInt(quantity.value) > 0) {
                quantity.value = parseInt(quantity.value) - 1;
                more.disabled = false;
            }
            if (parseInt(quantity.value) == 0) {
                this.disabled = true;
                form_item.classList.add('empty');
            }
            basketForm();
        });

        clean.addEventListener('click', function() {
            less.disabled = true;
            form_item.classList.add('empty');
            quantity.value = 0;
            basketForm();
        });

        function basketForm() {
            var form = basketSummary;
            form.classList.add('loading');

            const formData = new FormData(form);
            const method = form.getAttribute('method');
            const url = document.URL;

            fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                form.classList.remove('loading');
                if (data.status == 202) {
                    basketTotals.forEach(function(element) {
                        element.innerHTML = data.new_totals;
                    });
                    cartNums.forEach(function(element) {
                        element.innerHTML = data.new_nums;
                    });
                    getUpsellMessages();
                    CartTotalHeight();
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });

    function getUpsellMessages() {
        fetch(url_upsell_masseges, {
            method: 'GET',
        })
        .then(response => response.json())
        .then(html => {
            upsellMessages.innerHTML = html.upsell_messages;
        })
        .catch(error => console.error('Error:', error));
    }

    openCloseModal.forEach(function(element) {
        element.addEventListener('click', function() {
            modalEmptyCart.classList.toggle('d-none');
        });
    });

    emptyCart.addEventListener('click', function() {
        fetch(url_empty_basket, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            window.location.href = data.url;
        })
        .catch(error => console.error('Error:', error));
    });

    function CartTotalHeight() {
        cartWrapper.style.setProperty('--padding-cart', cartTotals.offsetHeight + 'px');
    }

    CartTotalHeight();
}

