// let modalContainer = document.querySelector('[data-id="order-modal"]');
let orders = document.querySelector('[data-id="order-status"]');

var modalContainer = $('[data-id="order-modal"]');

document.querySelectorAll('[data-id="order-status"]').forEach(function(order) {
    order.addEventListener('click', function(event) {
        event.preventDefault();
        modalContainer.modal();
        order_number = order.getAttribute('data-number');
        fetch(`${order_modal_url}?order_number=${order_number}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (modalContainer && data.html) {
                modalContainer.html(data.html);
            }
        })        
    });
});

modalContainer.on('hidden.bs.modal', function () {
    modalContainer.html('<div class="modal-dialog" role="document"><div class="modal-content content-loading"></div></div>');
});