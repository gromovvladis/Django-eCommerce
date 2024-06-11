$('[data-id="v-input-field"]').each(function(){
    var wrapper = $(this);
    var input_field = $(this).find('.v-input');
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
})
