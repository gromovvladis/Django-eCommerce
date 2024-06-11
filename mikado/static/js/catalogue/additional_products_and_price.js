
var additioan_products= $('[data-id="additional-product"]');
var price = $('[data-id="dish-price-button"]');

if (additioan_products){
    $(additioan_products).each(function(){
        var input_field = $(this).find('input');
        var add_price = parseInt($(this).find('[data-id="additional-product-price"]').text());
        var more = $(this).find('[data-id="order-button-plus"]');
        var less = $(this).find('[data-id="order-button-minus"]');

        more.on('click', function(){
            if ($(input_field).val() < $(input_field).attr('max')){
                $(input_field).val(parseInt($(input_field).val()) + 1);
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
                $(more).attr('disabled', false);
                $(price).text(parseInt($(price).text()) - add_price);
            }
            if ($(input_field).val() == 0) {
                $(this).attr('disabled', true);
            }
        });
    })
}
