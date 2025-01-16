let intervalId; // Объявляем переменную для идентификатора таймера
let orderNum = parseInt(document.querySelector('caption[data-num]').getAttribute('data-num'), 10);
let tableContainer = document.querySelector('[data-id="active-orders"]');

const audio = document.getElementById('order-sound');

const updateTable = () => {
    fetch(`${active_orders_lookup_url}?order_num=${orderNum}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.update){
            if (tableContainer && data.html) {
                tableContainer.innerHTML = data.html;
                orderNum = data.num_orders;
                if (audio) {
                    audio.play();
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
