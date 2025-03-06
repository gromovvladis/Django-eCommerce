let navbarCashModal = document.getElementById('navbarCashModalContent');

document.getElementById('navbarCash').addEventListener('click', function (event) {
    fetch(navbar_cash_url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
        .then(response => response.json())
        .then(data => {
            if (navbarCashModal && data.html) {
                navbarCashModal.innerHTML = data.html;
                navbarCashModal.classList.remove('navbar-loading');
            }
        })
});