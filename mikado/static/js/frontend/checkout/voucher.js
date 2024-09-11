var voucher_form = document.getElementById('voucher_form');
var voucher_btn = voucher_form.querySelector('#voucher_btn');
var remove_form = document.querySelector('[data-id="voucher-remove"]');
var code_input = document.getElementById('id_code');
var voucher_message = document.getElementById('voucher_message');

document.addEventListener('DOMContentLoaded', function () {
    if (remove_form){
        delete_promo(remove_form);
    }
});


function delete_promo(remove_form) {
    remove_form.addEventListener('submit', function (event) {
        event.preventDefault();
        let btn = this.querySelector(".remove_promocode");
        btn.setAttribute("disabled", true);

        fetch(this.getAttribute('action'), {
            method: this.getAttribute('method'),
            body: new URLSearchParams(new FormData(this))
        }).then(response => response.json())
        .then(data => {
            voucher_message.innerHTML = data.message;
            code_input.value = '';
            voucher_func(data);
            btn.removeAttribute("disabled");
        });
    });
}




voucher_form.addEventListener('submit', function (event) {
    event.preventDefault();
    voucher_btn.disabled = true;
    voucher_btn.textContent = 'Проверка';
    voucher_message.innerHTML = '';

    fetch(url_voucher, {
        method: this.getAttribute('method'),
        body: new URLSearchParams(new FormData(this))
    }).then(response => response.json())
    .then(data => {
        voucher_func(data);
        voucher_message.innerHTML = data.message;
        voucher_btn.textContent = 'Применить';
        voucher_btn.disabled = false;
    });

});


function voucher_func(response) {
    if (response.status == 202) {
        document.getElementById('checkout_totals').innerHTML = response.new_totals;
        code_input.value = '';
        remove_form = document.querySelector('[data-id="voucher-remove"]');
        delete_promo(remove_form);
    }
}

code_input.addEventListener('keyup', function(event){
    if (code_input.value !== "" && event.code !== 'Enter') {
        voucher_btn.disabled = false;
    } else {
        voucher_btn.disabled = true;
        voucher_message.innerHTML = "";
    }
});

