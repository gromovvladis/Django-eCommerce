var partnerLoaded = false;

function loadPartnerModal() {
    fetch(url_partner_api, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        console.log('Partner modal data:', data);
        modal.innerHTML = data.partner_modal;
        partnerModalLoaded();
        modal.classList.toggle('d-none');
        document.body.classList.toggle('fixed');
        setCookie("partner", data.partner_default);
    })
    .catch(error => {
        console.error('Error fetching partner modal:', error);
    });
}

function partnerModalLoaded() {

    var partner_form = document.getElementById('partner_form');
    
    auth_form.addEventListener('submit', function(event) {
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

    authLoaded = false;
    partnerLoaded = true;
}

function initPartner(basketPartner=null) {
    if (!basketPartner && !(getCookie("partner"))) {
        openPartnerModal();
    }
}

function openPartnerModal() {
    if (partnerLoaded) {
        modal.classList.toggle('d-none');
        document.body.classList.toggle('fixed');
    } else {
        loadPartnerModal();
    }
}

