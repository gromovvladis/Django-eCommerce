var auth_modal = $('#auth_modal');
var modalLoaded = false;
var redirectURL;

function loadAuthModal(redirect_url) {
    $.ajax({
        type: 'GET', 
        url: url_auth_api,
        success: function (response) {
            $(auth_modal).html(response.auth_modal);
            authModalLoaded();
            $(auth_modal).toggleClass('d-none');
            $(document.body).toggleClass('fixed');
            redirectURL.value = redirect_url;
        },
    });
}

function authModalLoaded(){
    var btn_sms = $('#sms_form_btn');
    var btn_auth = $('#auth_form_btn');
    
    var error_sms = $('#error_id_username')
    var error_auth = $('#error_id_password')
    
    var phoneInput = document.querySelector('#id_username');
    var codeInput = document.querySelector('#id_password');
    redirectURL = document.querySelector('#id_redirect_url');
    var password_groug = $('#auth_id_password')
    
    $('#auth_form').submit(function () {
        
        var auth_type = $(this).find('#auth_type')[0].value;
        btn_click_func(auth_type);
    
        $.ajax({
            data: $(this).serialize(), 
            type: $(this).attr('method'), 
            url: $(this).attr('action'),
            success: function (response) {
                success_func(auth_type, response);
            },
            error: function (response) {
                error_func(auth_type, response);
            },
        });
        return false;  
    });
    
    
    function btn_click_func(auth_type){
        if (auth_type == "sms") {
            $(btn_sms).attr("disabled", true);
            btn_sms.html('Отправка');
            error_sms.html('');
            error_auth.html('');
            codeInput.value = "";
        } else {
            $(btn_auth).attr("disabled", true);
            btn_auth.html('Загрузка');
            error_auth.html('');
        }
    }
    
    
    function success_func(auth_type, response) {
        if (auth_type == "sms") {
            $(btn_sms).removeClass('v-auth-modal__repeat-button')
            $(btn_sms).removeClass('v-button v-button--main')
            $(btn_sms).addClass('v-auth-modal__repeat-text')
            password_groug.removeClass('d-none');
            password_groug.addClass('v-input v-input__label-active');
            btn_auth.removeClass('d-none');
            btn_auth.addClass('v-button v-button--main');
            // phoneInput.setAttribute("readonly", "readonly");
            phoneInput.readOnly = true;
            var _Seconds = 30;
            int_id = setInterval(function() {
                if (_Seconds > 0) {
                _Seconds--; 
                $(btn_sms).text("Повторить SMS: " + _Seconds);
                } else {
                clearInterval(int_id);
                $(btn_sms).attr("disabled", false);
                $(btn_sms).text("Повторить SMS");
                $(btn_sms).removeClass('v-auth-modal__repeat-text')
                $(btn_sms).addClass('v-auth-modal__repeat-button')
                }
            }, 1000);  
        } else {
            window.location.href = response.secceded; 
        }
    }
    
    function error_func(auth_type, response) {
        if (auth_type == "sms") {
            $(btn_sms).attr("disabled", false);
            btn_sms.html('Отправить код');
            error_sms.text(response.responseJSON.errors);
        } else {
            $(btn_auth).attr("disabled", false);
            btn_auth.html('Подтвердить и войти');
            error_auth.text(response.responseJSON.errors);
        }
    }
    
    let phoneStr = '';
    let formattedStr = '';
    let deleteMode = false;
    
    const defaultFormat = '+7 ({0}{1}{2}) {3}{4}{5}-{6}{7}{8}{9}';
    
    phoneInput.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace')
            deleteMode = true;
        else
            deleteMode = false;
            
        });
        
        phoneInput.addEventListener('input', (e) => {
        if (deleteMode) {
            phoneInput.value = phoneInput.value;
            phoneStr = parsePhoneString(phoneInput.value);
        } else {
            if (e.inputType == 'insertText' && !isNaN(parseInt(e.data))) {
                if (phoneStr.length <= 10){
                    phoneStr += e.data;
                }
            }
            phoneInput.value = formatPhoneString();
        }
        if (phoneStr.length == 10){
            $(btn_sms).attr("disabled", false);
        } else {
            $(btn_sms).attr("disabled", true);
        }
    });
    
    function formatPhoneString() {
        let strArr = phoneStr.split('');
        formattedStr = defaultFormat;
        for (let i = 0; i < strArr.length; i++) {
            formattedStr = formattedStr.replace(`{${i}}`, strArr[i]);
        }
        
        if (formattedStr.indexOf('{') === -1)
            return formattedStr;
        else
            return formattedStr.substring(0, formattedStr.indexOf('{'));
        
    }
    
    function parsePhoneString(str) {
        return str.replace('+7', '').replace(' ', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '');
    }
    
    codeInput.addEventListener('input', function(){
        codeInput.value = codeInput.value.replace (/\D/g, '');
        if (codeInput.value.length == 4){
            $(btn_auth).attr("disabled", false);
        } else {
            $(btn_auth).attr("disabled", true); 
        }
    })
    
    codeInput.addEventListener('keypress', function (e) {
        var key = e.which || e.keyCode;
        if (key === 13) {
            btn_auth.click();
        }
    });

    modalLoaded = true;
}

function openAuthModal(redirect_url=''){
    if (modalLoaded){
        $(auth_modal).toggleClass('d-none');
        $(document.body).toggleClass('fixed');
        redirectURL.value = redirect_url;
    } else {
        loadAuthModal(redirect_url)
    }
}
