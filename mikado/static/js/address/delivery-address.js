var set_address_form = $('#set_address');

// инициализация адреса
$(document).ready(function () {
    var addressCockie = Cookies.get('line1');
    if (addressCockie){
        $(address_line1).attr('readonly', true);
        $(address_line1).attr('captured', true);
        createMap(addressCockie);
    }
});


$(set_address_form).submit(function () {
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
