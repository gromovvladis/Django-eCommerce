var storeLoaded = false;

function loadStoreModal() {
    fetch(url_store_api, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    })
        .then(response => response.json())
        .then(data => {
            modal.innerHTML = data.store_modal;
            storeModalLoaded();
            modal.classList.toggle('d-none');
            document.body.classList.toggle('fixed');
        })
        .catch(error => {
            console.error(error);
        });
}

function storeModalLoaded() {

    var store_form = document.getElementById('store_form');
    var radioButtons = store_form.querySelectorAll('input[type="radio"]');

    // Добавляем обработчик события на каждый radio button
    radioButtons.forEach(function (radio) {
        radio.addEventListener('change', function (event) {
            event.preventDefault();
            fetch(store_form.getAttribute('action'), {
                method: store_form.getAttribute('method'),
                body: new URLSearchParams(new FormData(store_form)).toString(),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrf_token,
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.refresh) {
                        window.location.reload();
                    };
                })
                .catch(error => {
                    console.error("errorFunc", response);
                });

        });

        radio.addEventListener('click', function (event) {
            if (radio.checked) {
                modal.classList.toggle('d-none');
                document.body.classList.toggle('fixed');
            }
        });

    });

    authLoaded = false;
    storeLoaded = true;
}

function initStore() {
    if (!getCookie("store")) {
        openStoreModal();
    }
}

function openStoreModal() {
    if (storeLoaded) {
        modal.classList.toggle('d-none');
        document.body.classList.toggle('fixed');
    } else {
        loadStoreModal();
    }
}