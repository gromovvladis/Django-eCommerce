var partnerLoaded = false;

function loadPartnerModal() {
    fetch(url_partner_api, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        modal.innerHTML = data.partner_modal;
        partnerModalLoaded();
        modal.classList.toggle('d-none');
        document.body.classList.toggle('fixed');
        setCookie("partner", data.partner_default);
    })
    .catch(error => {
        console.error(error);
    });
}

function partnerModalLoaded() {
    
    var partner_form = document.getElementById('partner_form');
    var radioButtons = partner_form.querySelectorAll('input[type="radio"]');

    // Добавляем обработчик события на каждый radio button
    radioButtons.forEach(function(radio) {
        radio.addEventListener('change', function(event) {
            event.preventDefault();
            fetch(partner_form.getAttribute('action'), {
                method: partner_form.getAttribute('method'),
                body: new URLSearchParams(new FormData(partner_form)).toString(),
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            })
            .then(response => response.json())
            .then(data => {
                if(data.refresh){
                    window.location.reload();
                };
            })
            .catch(error => {
                console.log("errorFunc", response);
            });
        });
    });

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