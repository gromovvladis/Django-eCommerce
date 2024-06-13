var empty_cart = $('[data-id="empty-cart"]');
var modal_empty_cart = $('[data-id="modal-empty-cart"]');
var open_close_modal = $('[data-id="modal-open-close"]');

var basket_summary = $('[data-id="basket-formset"]');
var basket_totals = $('[data-id="cart-totals"]');
var upsell_messages = $('#upsell_messages');
var cart_nums = $('[data-id="cart-nums"]');

if (basket_summary){
    var forms = $(basket_summary).find('[data-id="cart-item-form"]');
    $(forms).each(function(){
        var form_item = $(this)
        var input_field = $(form_item).find('[data-id="quantity-input"]');
        var more = $(form_item).find('[data-id="order-button-plus"]');
        var less = $(form_item).find('[data-id="order-button-minus"]');
        var clean = $(form_item).find('[data-id="dish-order-delete-link"]');

        more.on('click', function(){
            
            if ($(input_field).val() < parseInt($(input_field).attr('max'))){
                $(input_field).val(parseInt($(input_field).val()) + 1);
                $(less).attr('disabled', false);
            }
            if ($(input_field).val() == $(input_field).attr('max')) {
                $(this).attr('disabled', false);
            }
            $(form_item).removeClass('empty');
            $(basket_summary).submit()
        });

        less.on('click', function(){
            if ($(input_field).val() > 0){
                $(input_field).val(parseInt($(input_field).val()) - 1);
                $(more).attr('disabled', false);
            }
            if ($(input_field).val() == 0) {
                $(this).attr('disabled', true);
                $(form_item).addClass('empty');
            }
            $(basket_summary).submit()
        });

        clean.on('click', function(){
            $(less).attr('disabled', true);
            $(form_item).addClass('empty');
            $(input_field).val(0)
            $(basket_summary).submit()
        });
    })

    $(basket_summary).submit(function () {
        var form = $(this);
        $(form).addClass('loading');
        $.ajax({
            data: $(this).serialize(), 
            type: $(this).attr('method'), 
            url: document.URL,
            success: function (response){
                $(form).removeClass('loading');
                if (response.status == 202){
                    $(basket_totals).html(response.new_totals);
                    $(cart_nums).html(response.new_nums);
                    getUpsellMaseeges();
                }
            },
            error: function (response){
                console.log(response)
            }
        });
        return false;  
    });
}

function getUpsellMaseeges(){
    $.ajax({
        data: $(this).serialize(), 
        type: 'GET', 
        url: url_upsell_masseges,
        success: function (response){
            $(upsell_messages).empty();
            $(upsell_messages).html(response.upsell_messages);
        },
    });
}

$(open_close_modal).on('click', function(){
    $(modal_empty_cart).toggleClass('d-none');
});


$(empty_cart).on('click', function(){
    $.ajax({
        data: $(this).serialize(), 
        type: 'POST', 
        url: url_empty_basket,
        success: function (response){
            window.location.href = response.url;
        },
    });
})