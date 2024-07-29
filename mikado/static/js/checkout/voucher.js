var voucher_form = $('#voucher_form');
var voucher_btn = $(voucher_form).find('#voucher_btn');
var remove_form = $('.voucher-remove-form');
var code_input = $('#id_code');
var voucher_message = $('#voucher_message');
// var checkout_totals = $('#checkout_totals');

$(document).ready(function () {
    remove_form_added(remove_form);
})

function remove_form_added(remove_form){
    $(remove_form).submit(function () {
        let btn = $(this).find(".remove_promocode");
        $(btn).attr("disabled", true);
        $.ajax({
            data: $(this).serialize(), 
            type: $(this).attr('method'),
            url: $(this).attr('action'),
            complete: function(response) {
                $(voucher_message).html(response.responseJSON.message);
                $(code_input).val('');
                voucher_func(response);
                $(btn).attr("disabled", false);
            },
        });
        return false;  
    });
} 


$(voucher_form).submit(function () {
    $(voucher_btn).prop("disabled", true);
    $(voucher_btn).html('Проверка');
    $(voucher_message).html('');
    $.ajax({
        data: $(this).serialize(), 
        type: $(this).attr('method'), 
        url: url_voucher,
        complete: function (response) {
            voucher_func(response);
            $(voucher_message).html(response.responseJSON.message);
            $(voucher_btn).html('Применить');
            $(voucher_btn).prop("disabled", false);
        },
    });
    return false;  
});

function voucher_func(response) {
    if (response.status == 202){
        $(checkout_totals).html(response.responseJSON.new_totals);
        $(code_input).val('');
        remove_form = $('.voucher_remove_form');
        remove_form_added(remove_form);
    }
}

$(code_input).on('keyup', function(event){
    if ($(code_input).val() != "" && event.code != 'Enter'){
        $(voucher_btn).prop("disabled", false);
    } else {
        $(voucher_btn).prop("disabled", true);
    }
})
