var line3 = document.getElementById('id_line3');
var line4 = document.getElementById('id_line4');
var orderNote = document.getElementById('id_order_note');
var notes = document.getElementById('id_notes');

// Обработчик для предупреждения при закрытии страницы
window.onbeforeunload = function() {
    if (line1.getAttribute('captured') === 'true') {
        document.cookie = "line1=" + encodeURIComponent(line1.value) + "; path=/";
    }
};