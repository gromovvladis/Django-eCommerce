var line3 = $('#id_line3');
var line4 = $('#id_line4');
var order_note = $('#id_order_note');
var notes = $('#id_notes');

window.onbeforeunload = function() {
    if ($(line1).attr('captured') == 'true'){        
        Cookies.set('line1', $(line1).val());
    }
}; 
