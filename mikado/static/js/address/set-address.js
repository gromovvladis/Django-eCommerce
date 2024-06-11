var set_address_form = $('#set_address');

$(set_address_form).submit(function () {
    $(save_address_btn).attr("disabled", true);
    $(save_address_btn).html('Адрес сохранен');
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

// инициализация адреса
$(document).ready(function () {
    var addressCockie = Cookies.get('line1');
    if (addressCockie){
        $(address_line1).attr('readonly', true);
        $(address_line1).attr('captured', true);
        createMap(addressCockie);
    }
});