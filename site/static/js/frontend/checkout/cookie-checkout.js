var orderNote = document.getElementById('id_order_note');
var notes = document.getElementById('id_notes');
window.onbeforeunload = function() {
    if (line1.getAttribute('captured') === 'true') {
        setCookie('line1', line1.value);
        setCookie('line2', line2.value);
        setCookie('line3', line3.value);
        setCookie('line4', line4.value);
        setCookie('notes', notes.value);
    }
    setCookie('orderNote', orderNote.value);
};