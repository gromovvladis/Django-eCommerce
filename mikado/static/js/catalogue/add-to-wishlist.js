var wishlist_btn = $('#wishlist_btn');
var wishlist_form = $('#wishlist_form');

$(document).ready(function () {

    url = wishlist_form[0].action;

    $(wishlist_form).submit(function () {
        wishlist_btn_click_func();
        $.ajax({
            data: $(this).serialize(), 
            type: $(this).attr('method'), 
            url: url,
            success: function (response) {
                wishlist_success_func(response);
            },
            error: function (response) {
                wishlist_error_func(response);
            },
        });
        return false;  
    });
})

function wishlist_btn_click_func(){
    $(wishlist_btn).attr("disabled", true);
    $(wishlist_btn).addClass('loading');
}

function wishlist_success_func(response) {
    url = response.url;
    $(wishlist_btn).html(response.html);
    $(wishlist_btn).attr("disabled", false);
    $(wishlist_btn).removeClass('loading');
}

function wishlist_error_func(response) {
    $(wishlist_btn).attr("disabled", false);
    $(wishlist_btn).removeClass('loading');
    console.log('error');
}
