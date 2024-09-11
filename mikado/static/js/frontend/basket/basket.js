// var modal_empty_cart = $('[data-id="modal-empty-cart"]');
// var empty_cart = $(modal_empty_cart).find('[data-id="empty-cart"]');
// var open_close_modal = $('[data-id="modal-open-close"]');


// var upsell_messages = $(cartWrapper).find('#upsell_messages');


// var cartWrapper = $('[data-id="cart-wrapper"]');
// var basket_summary = $(cartWrapper).find('[data-id="basket-formset"]');
// var cartTotals = $('[data-id="cart-info"]');
// var basket_totals = $('[data-id="cart-totals"]');

// if ($(basket_summary).length > 0){
//     var forms = $(basket_summary).find('[data-id="cart-item-form"]');
//     $(forms).each(function(){
//         var form_item = $(this)
//         var input_field = $(form_item).find('[data-id="quantity-input"]');
//         var more = $(form_item).find('[data-id="order-button-plus"]');
//         var less = $(form_item).find('[data-id="order-button-minus"]');
//         var clean = $(form_item).find('[data-id="dish-order-delete-link"]');

//         if ($(input_field).val() == $(input_field).attr('max')) {
//             more.prop('disabled', true);
//         }

//         more.on('click', function(){
            
//             if ($(input_field).val() < parseInt($(input_field).attr('max'))){
//                 $(input_field).val(parseInt($(input_field).val()) + 1);
//                 $(less).prop('disabled', false);
//             }
//             if ($(input_field).val() == $(input_field).attr('max')) {
//                 $(this).prop('disabled', true);
//             }
//             $(form_item).removeClass('empty');
//             $(basket_summary).submit()
//         });

//         less.on('click', function(){
//             if ($(input_field).val() > 0){
//                 $(input_field).val(parseInt($(input_field).val()) - 1);
//                 $(more).prop('disabled', false);
//             }
//             if ($(input_field).val() == 0) {
//                 $(this).prop('disabled', true);
//                 $(form_item).addClass('empty');
//             }
//             $(basket_summary).submit()
//         });

//         clean.on('click', function(){
//             $(less).prop('disabled', true);
//             $(form_item).addClass('empty');
//             $(input_field).val(0)
//             $(basket_summary).submit()
//         });
//     })

//     $(basket_summary).submit(function () {
//         var form = $(this);
//         $(form).addClass('loading');
//         $.ajax({
//             data: $(this).serialize(), 
//             type: $(this).attr('method'), 
//             url: document.URL,
//             success: function (response){
//                 $(form).removeClass('loading');
//                 if (response.status == 202){
//                     $(basket_totals).html(response.new_totals);
//                     $(cart_nums).html(response.new_nums);
//                     getUpsellMaseeges();
//                     CartTotalHeight();
//                 }
//             },
//             error: function (response){
//                 console.log(response)
//             }
//         });
//         return false;  
//     });

// }

// function getUpsellMaseeges(){
//     $.ajax({
//         data: $(this).serialize(), 
//         type: 'GET', 
//         url: url_upsell_masseges,
//         success: function (response){
//             $(upsell_messages).empty();
//             $(upsell_messages).html(response.upsell_messages);
//         },
//     });
// }

// $(open_close_modal).on('click', function(){
//     $(modal_empty_cart).toggleClass('d-none');
// });

// $(empty_cart).on('click', function(){
//     $.ajax({
//         data: $(this).serialize(), 
//         type: 'POST', 
//         url: url_empty_basket,
//         success: function (response){
//             window.location.href = response.url;
//         },
//     });
// })

// function CartTotalHeight(){
//     $(cartWrapper).css('--padding-cart', $(cartTotals).outerHeight(true) + "px");
// }









var cartWrapper = document.querySelector('[data-id="cart-wrapper"]');
if (cartWrapper){
    var basket_summary = cartWrapper.querySelector('[data-id="basket-formset"]');
    var upsell_messages = cartWrapper.querySelector('#upsell_messages');
    var cartTotals = document.querySelector('[data-id="cart-info"]');
    var basket_totals = document.querySelectorAll('[data-id="cart-totals"]');
    var modal_empty_cart = document.querySelector('[data-id="modal-empty-cart"]');
    var empty_cart = modal_empty_cart.querySelector('[data-id="empty-cart"]');
    var open_close_modal = document.querySelectorAll('[data-id="modal-open-close"]');
    
    var basket_summary = cartWrapper.querySelector('[data-id="basket-formset"]');
    var forms = basket_summary.querySelectorAll('[data-id="cart-item-form"]');

    forms.forEach(function(form_item) {
        var input_field = form_item.querySelector('[data-id="quantity-input"]');
        var more = form_item.querySelector('[data-id="order-button-plus"]');
        var less = form_item.querySelector('[data-id="order-button-minus"]');
        var clean = form_item.querySelector('[data-id="dish-order-delete-link"]');

        if (input_field.value == input_field.getAttribute('max')) {
            more.disabled = true;
        }

        more.addEventListener('click', function() {
            if (parseInt(input_field.value) < parseInt(input_field.getAttribute('max'))) {
                input_field.value = parseInt(input_field.value) + 1;
                less.disabled = false;
            }
            if (parseInt(input_field.value) == parseInt(input_field.getAttribute('max'))) {
                this.disabled = true;
            }
            form_item.classList.remove('empty');
            basketForm();
        });

        less.addEventListener('click', function() {
            if (parseInt(input_field.value) > 0) {
                input_field.value = parseInt(input_field.value) - 1;
                more.disabled = false;
            }
            if (parseInt(input_field.value) == 0) {
                this.disabled = true;
                form_item.classList.add('empty');
            }
            basketForm();
        });

        clean.addEventListener('click', function() {
            less.disabled = true;
            form_item.classList.add('empty');
            input_field.value = 0;
            basketForm();
        });

        function basketForm() {
            var form = basket_summary;
            form.classList.add('loading');

            const formData = new FormData(form);
            const method = form.getAttribute('method');
            const url = document.URL;

            fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                form.classList.remove('loading');
                if (data.status == 202) {
                    basket_totals.forEach(function(element) {
                        element.innerHTML = data.new_totals;
                    });
                    cart_nums.forEach(function(element) {
                        element.innerHTML = data.new_nums;
                    });
                    getUpsellMessages();
                    CartTotalHeight();
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });

    function getUpsellMessages() {
        fetch(url_upsell_masseges, {
            method: 'GET',
        })
        .then(response => response.json())
        .then(html => {
            upsell_messages.innerHTML = html.upsell_messages;
        })
        .catch(error => console.error('Error:', error));
    }

    open_close_modal.forEach(function(element) {
        element.addEventListener('click', function() {
            modal_empty_cart.classList.toggle('d-none');
        });
    });

    empty_cart.addEventListener('click', function() {
        fetch(url_empty_basket, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            window.location.href = data.url;
        })
        .catch(error => console.error('Error:', error));
    });

    function CartTotalHeight() {
        cartWrapper.style.setProperty('--padding-cart', cartTotals.offsetHeight + 'px');
    }

    CartTotalHeight();
}

