
var add_basket_btn = $('#add_to_cart_btn');
var add_basket_errors = $('#add_to_cart_btn_errors');
var add_basket = $('#add_to_basket_form');

var variants_label = $('[data-id="tab-button-label"]');
var variants_block = $('#variant_active_block');

var price = $('[data-id="dish-price-button"]');
var dish_price = $('[data-id="dish-price-main"]');
var dish_old_price = $('[data-id="dish-old-price-main"]');

var additionals = $('[data-id="additional-product"]');
var addit_price = 0;

$(add_basket).submit(function () {
    $(add_basket_btn).prop("disabled", true);
    $(add_basket_btn).addClass('loading');
    $.ajax({
        data: $(this).serialize(), 
        type: $(this).attr('method'), 
        url: $(this).attr('action'),
        success: function (response) {
            $(cart_nums).html(response.cart_nums);
            cart_added();
        },
        error: function (response) {
            $(add_basket_errors).html(response.errors);
        },
        complete: function(){
            $(add_basket_btn).prop("disabled", false);
            $(add_basket_btn).removeClass('loading');
        }
    });
    return false;  
});

if ($(variants_label).length > 0){
    $(variants_label).on('click', function(){
        var d_price = parseInt($(this).find('input').attr('data-price'));
        var d_old_price = $(this).find('input').attr('data-old-price');
        $(price).html((d_price + addit_price));
        $(dish_price).text(d_price);

        dish_price_parent = $(dish_price).parent();
        dish_old_price_parent = $(dish_old_price).parent();

        if(d_old_price){
            $(dish_old_price).text(d_old_price);
            $(dish_old_price_parent).removeClass('d-none');
            $(dish_price_parent).addClass('new-price');
        } else {
            $(dish_old_price_parent).addClass('d-none');
            $(dish_price_parent).removeClass('new-price');    
        }

        $(variants_block).offset({'left':$(this).offset().left});
        $(variants_label).removeClass('active');
        $(this).addClass('active');
    });
    $(window).resize(function() {
        var active_label = $(variants_label).filter('.active');
        $(variants_block).offset({'left':$(active_label).offset().left});
    })
}

if ($(additionals).length > 0){
    $(additionals).each(function(){
        var input_field = $(this).find('input');
        var add_price = parseInt($(this).find('[data-id="additional-product-price"]').text());
        var more = $(this).find('[data-id="order-button-plus"]');
        var less = $(this).find('[data-id="order-button-minus"]');

        more.on('click', function(){
            if ($(input_field).val() < $(input_field).attr('max')){
                $(input_field).val(parseInt($(input_field).val()) + 1);
                addit_price += add_price;
                $(less).prop('disabled', false);
                $(price).text(parseInt($(price).text()) + add_price);
            }
            if ($(input_field).val() == $(input_field).attr('max')) {
                $(this).prop('disabled', true);
            }
        });

        less.on('click', function(){
            if ($(input_field).val() > 0){
                $(input_field).val(parseInt($(input_field).val()) - 1);
                addit_price -= add_price;
                $(more).prop('disabled', false);
                $(price).text(parseInt($(price).text()) - add_price);
            }
            if ($(input_field).val() == 0) {
                $(this).prop('disabled', true);
            }
        });
    })
}