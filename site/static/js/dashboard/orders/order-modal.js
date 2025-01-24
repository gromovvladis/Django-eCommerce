let orders = document.querySelector('[data-id="order-status"]');
let modalContainer = $('[data-id="order-modal"]');

const orderModal = () => {
    document.querySelectorAll('[data-id="order-status"]').forEach(function(order) {
        order.addEventListener('click', function(event) {
            event.preventDefault();
            modalContainer.modal();
            order_number = order.getAttribute('data-number');
            order.closest('tr').classList.remove('new-record');
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
                    let next_status = document.querySelector('[data-id="next-status"]');
                    if (next_status){
                        next_status.addEventListener('click', function () {
                            let button = this;
                            button.classList.add('loading');
                            fetch(next_status_url, {
                                method: 'POST',
                                headers: {
                                    'X-Requested-With': 'XMLHttpRequest',
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': csrf_token,
                                },
                                body: JSON.stringify({
                                    "order_number": button.getAttribute('data-number'),
                                    "next_status": button.getAttribute('data-status'),
                                }),
                            })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.next_status) {
                                        button.setAttribute('data-status', data.next_status);
                                        button.textContent = data.next_status;
                                    }
                                    if (data.final) {
                                        button.disabled = true;
                                    }
                                    if (updateTable){
                                        updateTable(true)
                                    }
                                })
                                .catch(error => console.error('Error:', error))
                                .finally(() => {
                                    button.classList.remove('loading'); // Удаляем класс загрузки
                                });
                        });
                    }
                    toggle_table(modalContainer.find(".toggle-row"));
                    badgeChanged(document.querySelectorAll('span[data-id="order-badge"]'));
                }
            })        
        });
    });
    modalContainer.on('hidden.bs.modal', function () {
        modalContainer.html('<div class="modal-dialog"><div class="modal-content content-loading"></div></div>');
        badgeChanged(document.querySelectorAll('span[data-id="order-badge"]'));
    });   
}

orderModal();