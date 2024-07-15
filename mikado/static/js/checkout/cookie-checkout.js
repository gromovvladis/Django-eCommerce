var address_line2 = $('#id_line2');
var address_line3 = $('#id_line3');
var address_line4 = $('#id_line4');
var order_note = $('#id_order_note');
var notes = $('#id_notes');
window.onbeforeunload = function() {
    if ($(address_line1).attr('captured') == 'true'){
        // $.ajax({
        //     data: {
        //         "line1": $(address_line1).val(),
        //         "line2": $(address_line2).val(),
        //         "line3": $(address_line3).val(),
        //         "line4": $(address_line4).val(),
        //     },
        //     type: 'POST', 
        //     headers: { "X-CSRFToken": csrf_token },
        //     url: url_session_address,
        // });
        Cookies.set('line1', $(address_line1).val());
        Cookies.set('line2', $(address_line2).val());
        Cookies.set('line3', $(address_line3).val());
        Cookies.set('line4', $(address_line4).val());
        Cookies.set('notes', $(notes).val());
    }
    Cookies.set('order_note', $(order_note).val());
}; 