var address_fields = $('#address_fields');

var delivery_time_btn = $('[data-id="delivery-time"]');
var delivery_time_now_btn = $(delivery_time_btn).find('#delivery_time_now');
var delivery_time_later_btn = $(delivery_time_btn).find('#delivery_time_later');

var delivery_time_later = $('#delivery_time_later');

var order_time = $('#id_order_time'); 
var submit_btn = $('#submit_order'); 

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
    var addressInital = $(address_line1).val();
    if (addressInital) {
        $(address_line1).attr('readonly', true);
        $(address_line1).attr('captured', true);
        createMap(addressInital);
    }
});

// смена метода доставки
$(shipping_method_buttons).on('click', function(){
    var selectedMethod = this.value;
    $(shipping_method).val(selectedMethod)
    $(delivery_method_block).offset({'left':$(this).offset().left});
    AjaxTimeFromAddress($(address_line1).val());
    if (selectedMethod == "self-pick-up"){
        $(address_fields).addClass('d-none');
        $(time_title).html('Время самовывоза');
    } else {
        $(address_fields).removeClass('d-none');
        $(time_title).html('Время доставки');
    }
    getNewTotals(selectedMethod)
})

// обновление итогов
function getNewTotals(selectedMethod){
    $.ajax({
        data: {'shipping_method': selectedMethod}, 
        type: 'GET', 
        url: url_update_totals,
        success: function (response){
            if (response.status == 202){
                $(checkout_totals).html(response.totals);
            }
        },
    });
}

// не отправлять форму enter-ом
$('#place_order_form').on('keypress', 'input', function(event) {
    if (event.which == 13) {
        event.preventDefault();
    }
});

// время для адреса из адресной книги
function AjaxTimeFromAddress(initAddress){
    if (initAddress != ""){
        ymaps.ready(function () {
            ymaps.geocode(initAddress, {results: 1}).then(function (res) {
                AjaxTime(res.geoObjects.get(0).geometry.getCoordinates(), true); 
            });
        });
    } else {
        AjaxPickUpTime();
    }
}

// выбрана доставка.самовывоз как можно скорее
$(delivery_time_btn).on('click', function(){
    $(delivery_time_block).offset({'left':$(this).offset().left});
    var delivery_time_method = $(this).attr("data-type");
    if (delivery_time_method == "now"){
        var Time = new Date();
        Time.setUTCMinutes(Time.getMinutes() + del_time);
        $(order_time).val(Time.toLocaleString());
        AjaxTimeFromAddress($(address_line1).val());
        $(delivery_time).removeClass('hidden');
        $(delivery_time_later).addClass('hidden');
    } else {
        $(delivery_time_later).removeClass('hidden');
        $(delivery_time).addClass('hidden');
    }

});

// лейблы при заполнении текста
$(all_fields).each(function(){
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
    })
})

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