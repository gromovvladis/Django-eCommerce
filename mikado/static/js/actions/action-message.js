var action_message = $('#action_message');

if ($(action_message).length > 0){
    cart_added = function(){
        console.log('Cart updated');
        $.ajax({
            type: 'GET', 
            url: url_action_message,
            success: function (response) {
                $(action_message).empty();
                $(action_message).html(response.upsell_message);
            },
        });
    }
}

