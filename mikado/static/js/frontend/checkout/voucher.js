var voucherForm = document.getElementById('voucher_form');
var voucherBtn = voucherForm.querySelector('#voucher_btn');
var removeForm = document.querySelector('[data-id="voucher-remove"]');
var codeInput = document.getElementById('id_code');
var voucherMessage = document.getElementById('voucher_message');

document.addEventListener('DOMContentLoaded', function () {
    if (removeForm){
        delete_promo(removeForm);
    }
});

function delete_promo(removeForm) {
    removeForm.addEventListener('submit', function (event) {
        event.preventDefault();
        let btn = this.querySelector(".remove_promocode");
        btn.setAttribute("disabled", true);

        fetch(this.getAttribute('action'), {
            method: this.getAttribute('method'),
            body: new URLSearchParams(new FormData(this))
        }).then(response => response.json())
        .then(data => {
            voucherMessage.innerHTML = data.message;
            codeInput.value = '';
            voucher_func(data);
            btn.removeAttribute("disabled");
        });
    });
}

voucherForm.addEventListener('submit', function (event) {
    event.preventDefault();
    voucherBtn.disabled = true;
    voucherBtn.textContent = 'Проверка';
    voucherMessage.innerHTML = '';

    fetch(url_voucher, {
        method: this.getAttribute('method'),
        body: new URLSearchParams(new FormData(this))
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
        removeForm = document.querySelector('[data-id="voucher-remove"]');
        delete_promo(removeForm);
    }
}

codeInput.addEventListener('keyup', function(event){
    if (codeInput.value !== "" && event.code !== 'Enter') {
        voucherBtn.disabled = false;
    } else {
        voucherBtn.disabled = true;
        voucherMessage.innerHTML = "";
    }
});