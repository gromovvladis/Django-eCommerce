var address_line3 = $('#id_line3');
var address_line4 = $('#id_line4');
var order_note = $('#id_order_note');
var notes = $('#id_notes');

window.onbeforeunload = function() {
    if ($(address_line1).attr('captured') == 'true'){        
        // $.ajax({
        //     data: {"line1": $(address_line1).val()},
        //     type: 'POST', 
        //     headers: { "X-CSRFToken": csrf_token },
        //     url: url_session_address,
        // });
        Cookies.set('line1', $(address_line1).val());
    }
}; 
