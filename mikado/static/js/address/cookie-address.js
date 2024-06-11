var address_line3 = $('#id_line3');
var address_line4 = $('#id_line4');
var order_note = $('#id_order_note');
var notes = $('#id_notes');

window.onbeforeunload = function() {
    if ($(address_line1).attr('captured') == 'true'){
        Cookies.set('line1', $(address_line1).val(), {expires: 1000});
    } else {
        Cookies.remove('line1');
        Cookies.remove('line2');
        Cookies.remove('line3');
        Cookies.remove('line4');
        Cookies.remove('notes');
    }
}; 
