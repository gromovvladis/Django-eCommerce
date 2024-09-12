var modal = document.getElementById('modal');
var modalLoaded = false;
var redirectURL;

function loadAuthModal(redirect_url) {
    fetch(url_auth_api, {
        method: 'GET'
    })
    .then(response => response.json()) // Предполагаем, что ответ в формате текста
    .then(responseText => {
        modal.innerHTML = responseText.auth_modal;
        authModalLoaded();
        modal.classList.toggle('d-none');
        document.body.classList.toggle('fixed');
        redirectURL.value = redirect_url;
    })
    .catch(error => {
        console.error('Error fetching auth modal:', error);
    });
}

function authModalLoaded() {
    
    console.log('authModalLoaded')

    var auth_form = document.getElementById('auth_form');
    redirectURL = auth_form.querySelector('#id_redirect_url');
    var btnSms = auth_form.querySelector('#sms_form_btn');
    var btnAuth = auth_form.querySelector('#auth_form_btn');
    var errorSms = auth_form.querySelector('#error_id_username');
    var errorAuth = auth_form.querySelector('#error_id_password');
    var phoneInput = auth_form.querySelector('#id_username');
    var codeInput = auth_form.querySelector('#id_password');
    var passwordGroup = auth_form.querySelector('#auth_id_password');
    
    auth_form.addEventListener('submit', function(event) {
        console.log('auth_form submit');

        event.preventDefault();
        auth_type = event.submitter.name
        btnClickFunc(auth_type);

        let formData = new URLSearchParams(new FormData(this))
        formData.append('action', auth_type);

        fetch(auth_form.getAttribute('action'), {
            method: auth_form.getAttribute('method'),
            body: formData.toString(),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.status == 200) {
                successFunc(auth_type, data);
            } else {
                errorFunc(auth_type, data);
            }
        })
        .catch(error => {
            errorFunc(auth_type, error);
        });
    });

    function btnClickFunc(authType) {
        if (authType == "sms") {
            btnSms.disabled = true;
            btnSms.innerHTML = 'Отправка';
            errorSms.innerHTML = '';
            errorAuth.innerHTML = '';
            codeInput.value = "";
        } else {
            btnAuth.disabled = true;
            btnAuth.innerHTML = 'Загрузка';
            errorAuth.innerHTML = '';
        }
    }

    function successFunc(authType, response) {
        console.log("successFunc", response);
        if (authType == "sms") {
            btnSms.classList.remove('v-auth-modal__repeat-button', 'v-button', 'v-button--main');
            btnSms.classList.add('v-auth-modal__repeat-text');
            passwordGroup.classList.remove('d-none');
            passwordGroup.classList.add('v-input', 'v-input__label-active');
            passwordGroup.querySelector('input').focus();
            btnAuth.classList.remove('d-none');
            btnAuth.classList.add('v-button', 'v-button--main');
            phoneInput.readOnly = true;
            var seconds = 30;
            var intId = setInterval(function() {
                if (seconds > 0) {
                    seconds--;
                    btnSms.textContent = "Повторить SMS: " + seconds;
                } else {
                    clearInterval(intId);
                    btnSms.disabled = false;
                    btnSms.textContent = "Повторить SMS";
                    btnSms.classList.remove('v-auth-modal__repeat-text');
                    btnSms.classList.add('v-auth-modal__repeat-button');
                }
            }, 1000);
        } else {
            window.location.href = response.succeeded;
        }
    }

    function errorFunc(authType, response) {
        console.log("errorFunc", response);
        if (authType == "sms") {
            btnSms.disabled = false;
            btnSms.innerHTML = 'Отправить код';
            errorSms.textContent = response.errors;
        } else {
            btnAuth.disabled = false;
            btnAuth.innerHTML = 'Подтвердить и войти';
            errorAuth.textContent = response.errors;
        }
    }

    let phoneStr = '';
    let formattedStr = '';
    let deleteMode = false;
    
    const defaultFormat = '+7 ({0}{1}{2}) {3}{4}{5}-{6}{7}{8}{9}';

    phoneInput.addEventListener('keydown', (e) => {
        deleteMode = (e.key === 'Backspace');
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
        btnSms.disabled = phoneStr.length !== 10;
    });

    function formatPhoneString() {
        let strArr = phoneStr.split('');
        formattedStr = defaultFormat;
        for (let i = 0; i < strArr.length; i++) {
            formattedStr = formattedStr.replace(`{${i}}`, strArr[i]);
        }
        return formattedStr.indexOf('{') === -1 ? formattedStr : formattedStr.substring(0, formattedStr.indexOf('{'));
    }
    
    function parsePhoneString(str) {
        return str.replace('+7', '').replace(' ', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '');
    }

    codeInput.addEventListener('input', function() {
        codeInput.value = codeInput.value.replace(/\D/g, '');
        btnAuth.disabled = codeInput.value.length !== 4;
    });

    codeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            btnAuth.click();
        }
    });

    modalLoaded = true;
}

function openAuthModal(redirect_url = '') {
    if (modalLoaded) {
        modal.classList.toggle('d-none');
        document.body.classList.toggle('fixed');
        redirectURL.value = redirect_url;
    } else {
        loadAuthModal(redirect_url);
    }
}