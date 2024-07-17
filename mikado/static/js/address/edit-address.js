var saveAddress = $('#save_address');
var line2 = $('#id_line2');
var line3 = $('#id_line3');
var line4 = $('#id_line4');
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
    var adr = $(line1).val();
    if (adr) {
        $(line1).attr('readonly', true);
        $(line1).attr('captured', true);
        createMap(adr);
    }
    validateAddress()
});

validate = () => {
    validateAddress();
}

// Валидация по адреса
function validateAddress(){

    var valid = true;
    
    console.log("validate " + valid);

    if (!$(line1).val() || $(line1).attr('captured') == "false" || $(line1).attr('valid') == "false"){
        console.log('line1 invalid')
        valid = false;
        error_address.removeClass('d-none');
        $(line1_container).addClass("not-valid");
    } else {
        error_address.addClass('d-none');
        $(line1_container).removeClass("not-valid");
    }

    if ($(line2).val() > 1000 || $(line2).val() < 1){
        console.log('line2 invalid')
        valid = false;
        error_flat.removeClass('d-none');
        $(line2).addClass("not-valid");
    } else {
        error_flat.addClass('d-none');
        $(line2).removeClass("not-valid");
    }

    if ($(line3).val() > 100 || $(line3).val() < 1){
        console.log('line3 invalid')
        valid = false;
        error_enter.removeClass('d-none');
        $(line3).addClass("not-valid");
    } else {
        error_enter.addClass('d-none');
        $(line3).removeClass("not-valid");
    }

    if ($(line4).val() > 100 || $(line4).val() < 1){
        console.log('line4 invalid')
        valid = false;
        error_floor.removeClass('d-none');
        $(line4).addClass("not-valid");
    } else {
        error_floor.addClass('d-none');
        $(line4).removeClass("not-valid");
    }

    console.log("validate " +  valid)

    if (valid){
        $(saveAddress).attr("disabled", false);
        $(checkout_errors).addClass('d-none');
    } else {
        $(saveAddress).attr("disabled", true);
        $(checkout_errors).removeClass('d-none');    
    }
}

