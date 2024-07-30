var cart_nums = $('[data-id="cart-nums"]');
var cart_added = () => {};

$(document).ready(function () {
    findNewForms();
});

function findNewForms(){
    var add_cart_form = $("[data-id='add-to-cart-form-compact']");
    if ($(add_cart_form).length > 0) {
        $(add_cart_form).submit(function () {
    
            var btn = $(this).find('[data-id="add-to-cart-btn-compact"]').get(0)
            var span = $(btn).find('[data-id="add-to-cart-btn-span"]').get(0)
            $(btn).prop("disabled", true);
            $(btn).addClass('clicked');
            var textBefore = $(span).html();
            $(span).html('Добавлено');
        
            $.ajax({
                data: $(this).serialize(), 
                type: $(this).attr('method'), 
                url: $(this).attr('action'),
                success: function (response) {
                    $(cart_nums).html(response.cart_nums); 
                    cart_added();
                },
                error: function(response){
                    $(btn).closest('.product-description').find('[data-id="add-to-cart-help-text-compact"]').html(response.errors)
                },
                complete: function (){
                    $(btn).prop("disabled", false);
                    $(btn).removeClass('clicked');
                    $(span).html(textBefore);
                }        
            });
            return false;  
        });
    }
}
