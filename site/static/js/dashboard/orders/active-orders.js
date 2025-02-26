let intervalId; // Объявляем переменную для идентификатора таймера
let tableContainer = document.querySelector('[data-id="active-orders"]');
let activeNavbar = document.querySelector('[data-id="active-navbar"]');
let activeNavbarNum = activeNavbar.querySelector('div');
let navbarOrders = document.querySelector('[data-id="Заказы"]');
let navbarActiveOrders = document.querySelector('[data-id="Активные заказы"]');
let orderNum = parseInt(document.querySelector('caption[data-num]').getAttribute('data-num'), 10);
const audio = document.getElementById('order-sound');

const updateActiveTable = (force = false) => {
    fetch(`${active_orders_lookup_url}?order_num=${orderNum}&force=${force}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.update || force) {
                if (tableContainer && data.html) {
                    let oldOrderNum = orderNum;
                    orderNum = parseInt(data.num_orders, 10);
                    tableContainer.innerHTML = data.html;
                    activeNavbarNum.innerHTML = orderNum;
                    if (orderNum > 0) {
                        navbarOrders.innerHTML = orderNum;
                        navbarActiveOrders.innerHTML = orderNum;
                        activeNavbar.classList.remove("d-none");
                    } else {
                        navbarOrders.innerHTML = "";
                        navbarActiveOrders.innerHTML = "";
                        activeNavbar.classList.add("d-none");
                    }
                    if (audio && !force && oldOrderNum < orderNum) {
                        audio.play();
                    }
                    if (orderModal) {
                        orderModal();
                    }
                    oscar.dashboard.orders.initTable();
                    badgeChanged(tableContainer.querySelectorAll('span[data-id="order-badge"]'));
                }
            }
        })
        .catch(error => console.error('Error updating table:', error));
};

// Устанавливаем таймер и сохраняем его идентификатор
intervalId = setInterval(updateActiveTable, 5000);

// При выгрузке страницы очищаем таймер
window.addEventListener('beforeunload', () => {
    clearInterval(intervalId); // Очищаем интервал
});
