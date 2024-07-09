var saveAddress = $('#save_address');
var address_line2 = $('#id_line2');
var address_line3 = $('#id_line3');
var address_line4 = $('#id_line4');
var checkout_errors = $('[data-id="checkout-error-list"]');
var error_address = $(checkout_errors).find('[data-error="address"]');
var error_flat = $(checkout_errors).find('[data-error="flat"]');
var error_enter = $(checkout_errors).find('[data-error="enter"]');
var error_floor = $(checkout_errors).find('[data-error="floor"]');

$('[data-id="v-input-field"]').each(function(){
    var wrapper = $(this);
    var input_field = $(this).find('.v-input');
    if($(input_field).val() != ""){
        wrapper.addClass('v-input__label-active')
    }
    $(input_field).focusin(function(){
        wrapper.addClass('v-input__label-active')
    })
    $(input_field).focusout(function(){
        if($(input_field).val() == ""){
            wrapper.removeClass('v-input__label-active')
        }
        validateAddress();
    })
})


// не отправлять форму enter-ом
$('#edit-address').on('keypress', 'input', function(event) {
    if (event.which == 13) {
        event.preventDefault();
    }
});


// инициализация адреса
$(document).ready(function () {
    var addressInital = $(address_line1).val();
    if (addressInital) {
        $(address_line1).attr('readonly', true);
        $(address_line1).attr('captured', true);
        createMap(addressInital);
    }
});

validate = () => {
    validateAddress();
}

// Валидация по адреса
function validateAddress(){
    console.log("validate")
    var Addressvalideted = true

    if (!$(address_line1).val() || $(address_line1).attr('captured') == "false"){
        Addressvalideted = false;
        error_address.removeClass('d-none');
    } else {
        error_address.addClass('d-none');
    }

    if ($(address_line2).val() > 1000 || $(address_line2).val() < 1){
        Addressvalideted = false;
        error_flat.removeClass('d-none');
    } else {
        error_flat.addClass('d-none');
    }

    if ($(address_line3).val() > 100 || $(address_line3).val() < 1){
        Addressvalideted = false;
        error_enter.removeClass('d-none');
    } else {
        error_enter.addClass('d-none');
    }

    if ($(address_line4).val() > 100 || $(address_line4).val() < 1){
        Addressvalideted = false;
        error_floor.removeClass('d-none');
    } else {
        error_floor.addClass('d-none');
    }

    console.log('validateAddress' + Addressvalideted)

    if (Addressvalideted){
        $(saveAddress).attr("disabled", false);
        $(checkout_errors).addClass('d-none');
    } else {
        $(saveAddress).attr("disabled", true);
        $(checkout_errors).removeClass('d-none');    
    }
}
