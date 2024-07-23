var set_address_form = $('#set_address');

// инициализация адреса
$(document).ready(function () {
    var adr = Cookies.get('line1');
    if (adr){
        $(line1).prop('readonly', true);
        $(line1).attr('captured', true);
        createMap(adr);
    }
});


$(set_address_form).submit(function () {
    console.log('Form submitted');
    $.ajax({
        data: $(this).serialize(), 
        type: $(this).attr('method'), 
        url: $(this).attr('action'),
    });
    return false;  
});

$(set_address_form).on('keypress', 'input', function(event) {
    if (event.which == 13) {
        event.preventDefault();
    }
});

$(saveButton).on('click', function () {
    setTimeout(function() {
        $(set_address_form).submit();
    }, 0);
});