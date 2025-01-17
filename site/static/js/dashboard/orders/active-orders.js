let intervalId; // Объявляем переменную для идентификатора таймера
let tableContainer = document.querySelector('[data-id="active-orders"]');
let orderNum = parseInt(document.querySelector('caption[data-num]').getAttribute('data-num'), 10);
const audio = document.getElementById('order-sound');

const updateTable = (force=false) => {
    fetch(`${active_orders_lookup_url}?order_num=${orderNum}&force=${force}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.update || force){
            if (tableContainer && data.html) {
                tableContainer.innerHTML = data.html;
                orderNum = data.num_orders;
                if (audio && !force) {
                    audio.play();
                }
                if (orderModal){
                    orderModal();
                }
            }
        }
    })
    .catch(error => console.error('Error updating table:', error));
};

// Устанавливаем таймер и сохраняем его идентификатор
intervalId = setInterval(updateTable, 5000);

// При выгрузке страницы очищаем таймер
window.addEventListener('beforeunload', () => {
    clearInterval(intervalId); // Очищаем интервал
});
