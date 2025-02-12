var addVoucherForm = document.querySelector('[data-id="voucher-add"]');
var removeVoucherForm = document.querySelector('[data-id="voucher-remove"]');
var voucherBtn = addVoucherForm.querySelector('[data-id="voucher-btn"]');

var codeInput = document.getElementById('id_code');
var voucherMessage = document.getElementById('[data-id="voucher-message"]');

document.addEventListener('DOMContentLoaded', function () {
    if (removeVoucherForm) {
        delete_promo(removeVoucherForm);
    }
});

function delete_promo(removeForm) {
    removeForm.addEventListener('submit', function (event) {
        event.preventDefault();
        let btn = this.querySelector(".remove_promocode");
        btn.setAttribute("disabled", true);

        fetch(this.getAttribute('action'), {
            method: this.getAttribute('method'),
            body: new URLSearchParams(new FormData(this)),
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrf_token,
            }
        }).then(response => response.json())
            .then(data => {
                voucherMessage.innerHTML = data.message;
                codeInput.value = '';
                voucher_func(data);
                btn.removeAttribute("disabled");
            });
    });
}

addVoucherForm.addEventListener('submit', function (event) {
    event.preventDefault();
    voucherBtn.disabled = true;
    voucherBtn.textContent = 'Проверка';
    voucherMessage.innerHTML = '';

    fetch(url_voucher, {
        method: this.getAttribute('method'),
        body: new URLSearchParams(new FormData(this)),
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token,
        }
    }).then(response => response.json())
        .then(data => {
            voucher_func(data);
            voucherMessage.innerHTML = data.message;
            voucherBtn.textContent = 'Применить';
            voucherBtn.disabled = false;
        });

});

function voucher_func(response) {
    if (response.status == 202) {
        document.getElementById('checkout_totals').innerHTML = response.new_totals;
        codeInput.value = '';
        removeVoucherForm = document.querySelector('[data-id="voucher-remove"]');
        delete_promo(removeVoucherForm);
    }
}

codeInput.addEventListener('keyup', function (event) {
    if (codeInput.value !== "" && event.code !== 'Enter') {
        voucherBtn.disabled = false;
    } else {
        voucherBtn.disabled = true;
        voucherMessage.innerHTML = "";
    }
});