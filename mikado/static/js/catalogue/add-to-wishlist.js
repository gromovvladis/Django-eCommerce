var wishlist_form = $('#wishlist_form');

$(document).ready(function () {

    if($(wishlist_form).length > 0){

        var wishlist_btn = $(wishlist_form).find('#wishlist_btn');
        url = wishlist_form[0].action;
    
        $(wishlist_form).submit(function () {
            $(wishlist_btn).prop("disabled", true);
            $(wishlist_btn).addClass('loading');
            $.ajax({
                data: $(this).serialize(), 
                type: $(this).attr('method'), 
                url: url,
                success: function (response) {
                    url = response.url;
                    $(wishlist_btn).html(response.html);
                    $(wishlist_btn).prop("disabled", false);
                    $(wishlist_btn).removeClass('loading');
                },
                error: function (response) {
                    $(wishlist_btn).prop("disabled", false);
                    $(wishlist_btn).removeClass('loading');
                    console.log('error');
                },
            });
            return false;  
        });
    }
})
