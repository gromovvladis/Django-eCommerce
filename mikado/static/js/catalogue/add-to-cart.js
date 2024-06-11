
var add_cart_btn = $('#add_to_cart_btn');
var errors_cart = $('#add_to_cart_btn_errors');
var cart_nums = $('[data-id="cart-nums"]');
var add_form_dalail = $('#add_to_basket_form');

var variants_label = $('[data-id="tab-button-label"]');
var variants_block = $('#variant_active_block');
var dish_price = $('[data-id="dish-price-main"]');
var dish_old_price = $('[data-id="dish-old-price-main"]');

var additioan_products= $('[data-id="additional-product"]');
var price = $('[data-id="dish-price-button"]');
var additional_price = 0;


$(add_form_dalail).submit(function () {
    $(add_cart_btn).attr("disabled", true);
    $(add_cart_btn).addClass('loading');
    $.ajax({
        data: $(this).serialize(), 
        type: $(this).attr('method'), 
        url: url_product,
        success: function (response) {
            $(cart_nums).html(response.cart_nums);
        },
        error: function (response) {
            $(errors_cart).html(response.responseJSON.errors);
        },
        complete: function(){
            $(add_cart_btn).attr("disabled", false);
            $(add_cart_btn).removeClass('loading');
        }
    });
    return false;  
});

$(add_cart_btn).on('click', function(){
    $(add_form_dalail).submit()
})

if (variants_label){
    $(variants_label).on('click', function(){
        var d_price = parseInt($(this).find('input').attr('data-price'));
        var d_old_price = $(this).find('input').attr('data-old-price');
        $(price).html((d_price + additional_price));
        $(dish_price).text(d_price);

        dish_price_parent = $(dish_price).parent()
        dish_old_price_parent = $(dish_old_price).parent()

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

if (additioan_products){
    $(additioan_products).each(function(){
        var input_field = $(this).find('input');
        var add_price = parseInt($(this).find('[data-id="additional-product-price"]').text());
        var more = $(this).find('[data-id="order-button-plus"]');
        var less = $(this).find('[data-id="order-button-minus"]');

        more.on('click', function(){
            if ($(input_field).val() < $(input_field).attr('max')){
                $(input_field).val(parseInt($(input_field).val()) + 1);
                additional_price += add_price;
                $(less).attr('disabled', false);
                $(price).text(parseInt($(price).text()) + add_price);
            }
            if ($(input_field).val() == $(input_field).attr('max')) {
                $(this).attr('disabled', true);
            }
        });

        less.on('click', function(){
            if ($(input_field).val() > 0){
                $(input_field).val(parseInt($(input_field).val()) - 1);
                additional_price -= add_price
                $(more).attr('disabled', false);
                $(price).text(parseInt($(price).text()) - add_price);
            }
            if ($(input_field).val() == 0) {
                $(this).attr('disabled', true);
            }
        });
    })
}
