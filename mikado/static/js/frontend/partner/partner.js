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
    console.log('Partner')
    partner_form.addEventListener('submit', function(event) {
        event.preventDefault();
        fetch(partner_form.getAttribute('action'), {
            method: partner_form.getAttribute('method'),
            body: new URLSearchParams(new FormData(this)).toString(),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            successFunc(data);
        })
        .catch(error => {
            errorFunc(error);
        });
    });

    function successFunc(response) {
        console.log("successFunc", response);
        // if (authType == "sms") {
        
        // } else {
        //     window.location.href = response.succeeded;
        // }
    }

    function errorFunc(response) {
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

