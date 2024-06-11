
var cart_nums_compact = $('[data-id="cart-nums"]');

function findNewForms(){
    var add_cart_form = $("[data-id='add-to-cart-form-compact']");
    $(add_cart_form).submit(function () {

        var btn = $(this).find('[data-id="add-to-cart-btn-compact"]').get(0)
        var span = $(btn).find('[data-id="add-to-cart-btn-span"]').get(0)
    
        $(btn).attr("disabled", true);
        $(btn).addClass('clicked');
        var textBefore = $(span).html();
        $(span).html('Добавлено');
    
        $.ajax({
            data: $(this).serialize(), 
            type: $(this).attr('method'), 
            url: $(this).attr('action'),
            success: function (response) {
                $(cart_nums_compact).html(response.cart_nums); 
            },
            error: function(response){
                $(btn).parent().parent().parent().parent().find('[data-id="add-to-cart-help-text-compact"]').html(response.responseJSON.errors)
            },
            complete: function (){
                $(btn).attr("disabled", false);
                $(btn).removeClass('clicked');
                $(span).html(textBefore);
            }
        
        });
        return false;  
    });
}

findNewForms();