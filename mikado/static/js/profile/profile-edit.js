var profile_form = $('#profile_form');
var all_fields = $(profile_form).find('[data-id="input-wrapper"]');

$(all_fields).each(function(){
    var wrapper = $(this);
    var input_field = $(this).find('[data-id="profile-input"]');
    if($(input_field).val() != ""){
        wrapper.addClass('v-input__label-active')
    }
    $(input_field).focusin(function(){
        wrapper.addClass('v-input__label-active')
    })
    $(input_field).focusout(function(){
        if($(input_field).val() == ""){
            wrapper.removeClass('v-input__label-active')
        }
    })
});

$(profile_form).submit(function () {
    var profile_btn = $(this).find('button')
    var profile_msg = $(this).find('[data-id="profile-message"]')
    $(profile_btn).attr("disabled", true);
    $(profile_btn).html('Сохранение');
    $(profile_msg).html('');
    $.ajax({
        data: $(this).serialize(), 
        type: $(this).attr('method'), 
        url: $(this).attr('action'),
        complete: function (response) {
            console.log(response)
            $(profile_msg).html(response.responseJSON.message);
            $(profile_btn).html('Сохранить настройки');
            $(profile_btn).attr("disabled", false);
        },
    });
    return false;  
});

