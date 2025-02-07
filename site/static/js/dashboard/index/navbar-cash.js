let modalContainer = document.getElementById('navbarCashModal')
let modalContent = document.getElementById('navbarCashModalContent')

document.getElementById('navbarCash').addEventListener('click', function(event) {
    fetch(navbar_cash_url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (modalContent && data.html) {
            modalContent.innerHTML = data.html;
            modalContent.classList.remove('navbar-loading');
        }
    })        
});