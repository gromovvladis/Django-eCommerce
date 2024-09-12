var orderNote = document.getElementById('id_order_note');
var notes = document.getElementById('id_notes');
window.onbeforeunload = function() {
    if (line1.getAttribute('captured') === 'true') {
        Cookies.set('line1', line1.value);
        Cookies.set('line2', line2.value);
        Cookies.set('line3', line3.value);
        Cookies.set('line4', line4.value);
        Cookies.set('notes', notes.value);
    }
    Cookies.set('orderNote', orderNote.value);
};