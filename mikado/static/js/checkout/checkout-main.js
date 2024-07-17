var address_fields = $('#address_fields');
var submit_btn = $('#submit_order'); 

var checkout_errors = $('[data-id="checkout-error-list"]');
var error_address = $(checkout_errors).find('[data-error="address"]');
var error_flat = $(checkout_errors).find('[data-error="flat"]');
var error_enter = $(checkout_errors).find('[data-error="enter"]');
var error_floor = $(checkout_errors).find('[data-error="floor"]');
var error_amount = $(checkout_errors).find('[data-error="amount"]');

var amountValid = true;
var addressValid = true;

var order_time = $('#id_order_time'); 
var delivery_time_btn = $('[data-id="delivery-time"]');
var delivery_time_later = $('#delivery_time_later');

var shipping_method_buttons = $('[data-id="delivery-method-button"]');
var delivery_method_block = $('[data-id="delivery-method-block"]');
var delivery_time_block = $('[data-id="delivery-time-block"]');
var time_title = $('[data-id="order-time-title"]');

var checkout_totals = $('#checkout_totals');
var all_fields = $('[data-id="v-input-field"]');
var payment_method = $('#id_payment_method');
var email_or_change_block = $(all_fields).filter('[data-field="v-email-field"]');
var email_or_change_field = $(email_or_change_block).find('#email_field_label');

const OFFLINE_PAYMENT = ['CASH'];
const ONLINE_PAYMENT = ['SBP', 'CARD'];

// инициализация адреса
$(document).ready(function () {
    var addressInital = $(line1).val();
    if (addressInital) {
        $(line1).attr('readonly', true);
        $(line1).attr('captured', true);
        createMap(addressInital);
    }
    validateCheckout();
});

// смена метода доставки
$(shipping_method_buttons).on('click', function(){
    shippingMethod = this.value;
    $(shipping_method).val(shippingMethod)
    $(delivery_method_block).offset({'left':$(this).offset().left});
    GetTime({address:$(line1).val(), coords:[$(lon).val(), $(lat).val()], shippingMethod: shippingMethod}).then(function(result) {
        timeCaptured(result);
    });
    if (shippingMethod == "self-pick-up"){
        $(address_fields).addClass('d-none');
        $(time_title).html('Время самовывоза');
    } else {
        $(address_fields).removeClass('d-none');
        $(time_title).html('Время доставки');
    }
    getNewTotals(shippingMethod);
})

// выбрана доставка.самовывоз как можно скорее
$(delivery_time_btn).on('click', function(){
    $(delivery_time_block).offset({'left':$(this).offset().left});
    var delivery_time_method = $(this).attr("data-type");
    if (delivery_time_method == "now"){
        GetTime({address:$(line1).val(), coords:[$(lon).val(), $(lat).val()], shippingMethod: shippingMethod}).then(function(result) {
            $(order_time).val(result.timeUTC);
            timeCaptured(result);
        });
        $(delivery_time).removeClass('hidden');
        $(delivery_time).addClass('active');
        $(delivery_time_later).addClass('hidden');
        $(delivery_time_later).removeClass('active');
    } else {
        $(delivery_time_later).removeClass('hidden');
        $(delivery_time_later).addClass('active');
        $(delivery_time).addClass('hidden');
        $(delivery_time).removeClass('active');
    }
});

// обновление итогов
function getNewTotals(selectedMethod, zonaId=null){
    console.log('getNewTotals')
    $.ajax({
        data: {
            'shipping_method': selectedMethod,
            "zona_id": zonaId
        }, 
        type: 'GET', 
        url: url_update_totals,
        success: function (response){
            if (response.status == 202){
                $(checkout_totals).html(response.totals);
                $(error_amount).html(response.min_order);
            }
        },
        complete: function(){
            validateCheckout();
        }
    });
}

// сдача или чек
$(payment_method).change(function(){
    if (OFFLINE_PAYMENT.includes(this.value)){
        $(email_or_change_field).html('Нужна сдача с ...');
        $(email_or_change_block).removeClass('d-none-i');
    } else if (ONLINE_PAYMENT.includes(this.value)) {
        $(email_or_change_field).html('E-mail для получения чеков');
        $(email_or_change_block).removeClass('d-none-i');
    } else {
        $(email_or_change_block).addClass('d-none-i');
    }
})

// лейблы при заполнении текста
$(all_fields).each(function(){
    var wrapper = $(this);
    var input_field = $(this).find('.v-input');
    if($(input_field).val() != ""){
        wrapper.addClass('v-input__label-active');
    }
    $(input_field).focusin(function(){
        wrapper.addClass('v-input__label-active');
    })
    $(input_field).focusout(function(){
        if($(input_field).val() == ""){
            wrapper.removeClass('v-input__label-active');
        }
        validateAddress();
        checkValid();
    })
})

// не отправлять форму enter-ом
$('#place_order_form').on('keypress', 'input', function(event) {
    if (event.which == 13) {
        event.preventDefault();
    }
});

validate = () => {
    validateCheckout();
}

// валидаия по мин заказу и адрессу
function validateCheckout(){
    console.log('validateCheckout')
    validateAddress();
    validateTotals();
    checkValid();
}


function checkValid (){
    console.log('checkValid')
    if (amountValid && addressValid){
        console.log('checkValid VALID')
        $(submit_btn).attr("disabled", false);
        $(checkout_errors).addClass('d-none');
    } else {
        console.log('checkValid NO VALID')
        $(submit_btn).attr("disabled", true);
        $(checkout_errors).removeClass('d-none');    
    }
}

// Валидация по адреса
function validateAddress(){
    addressValid = true
    shippingMethod = $(shipping_method).val();
    if (shippingMethod == "zona-shipping"){

        if (!$(line1).val() || $(line1).attr('captured') == "false" || $(line1).attr('valid') == "false"){
            addressValid = false;
            error_address.removeClass('d-none');
            $(line1_container).addClass("not-valid");
        } else {
            error_address.addClass('d-none');
            $(line1_container).removeClass("not-valid");
        }

        if ($(line2).val() > 1000 || $(line2).val() < 1){
            addressValid = false;
            error_flat.removeClass('d-none');
            $(line2).addClass("not-valid");
        } else {
            error_flat.addClass('d-none');
            $(line2).removeClass("not-valid");
        }

        if ($(line3).val() > 100 || $(line3).val() < 1){
            addressValid = false;
            error_enter.removeClass('d-none');
            $(line3).addClass("not-valid");
        } else {
            error_enter.addClass('d-none');
            $(line3).removeClass("not-valid");
        }

        if ($(line4).val() > 100 || $(line4).val() < 1){
            addressValid = false;
            error_floor.removeClass('d-none');
            $(line4).addClass("not-valid");
        } else {
            error_floor.addClass('d-none');
            $(line4).removeClass("not-valid");
        }
    }
}

// Валидация по сумме заказа
function validateTotals(){
    amountValid = true;
    if ($(checkout_totals).find('[data-min-order]').attr("data-min-order") == "false" && shippingMethod == "zona-shipping"){
        amountValid = false;
        $(error_amount).removeClass('d-none')
    } else {
        $(error_amount).addClass('d-none') 
    }
}

// начисляем стоимость доствки в зависмости от зоны
function shippingCharge(zonaId=null){
    console.log("ShippingCharge");
    getNewTotals(shippingMethod, zonaId);
}

// loading spiner
$(submit_btn).on('click', function(){
    $(this).addClass('sending');
})

// таймер обновления времени доставки к адрессу каждые 5 минут
// function updateTimes(){
//     int_id = setInterval(function() {
//         console.log('upd timer')
//         GetTime({adrs:$(line1).val(), shippingMethod:shippingMethod}).then(function(result) {
//             timeCaptured(result);
//         });
//     }, 300000);  
// }
// updateTimes();