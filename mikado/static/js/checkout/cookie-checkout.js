var order_note = $('#id_order_note');
var notes = $('#id_notes');
window.onbeforeunload = function() {
    if ($(line1).attr('captured') == 'true'){
        Cookies.set('line1', $(line1).val());
        Cookies.set('line2', $(line2).val());
        Cookies.set('line3', $(line3).val());
        Cookies.set('line4', $(line4).val());
        Cookies.set('notes', $(notes).val());
    }
    Cookies.set('order_note', $(order_note).val());
}; 