var addBasketForm = document.getElementById('add_to_basket_form');

if (addBasketForm) {

    var addBasketBtn = document.getElementById('add_to_cart_btn');
    var priceElement = addBasketBtn.querySelector('[data-id="dish-price-button"]');
    var addBasketErrors = document.getElementById('add_to_cart_btn_errors');
    
    var variantsLabels = addBasketForm.querySelectorAll('[data-id="tab-button-label"]');

    var dishPrice = document.querySelector('[data-id="dish-price-main"]');
    var dishOldPrice = document.querySelector('[data-id="dish-old-price-main"]');

    var additionals = document.querySelectorAll('[data-id="additional-product"]');
    var additPrice = 0;

    addBasketForm.addEventListener('submit', function (event) {
        event.preventDefault();
        
        addBasketBtn.disabled = true;
        addBasketBtn.classList.add('loading');

        var xhr = new XMLHttpRequest();
        xhr.open(addBasketForm.method, addBasketForm.action, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

        xhr.onload = function () {
            var response = JSON.parse(xhr.responseText);
            if (xhr.status >= 200 && xhr.status < 300) {
                cartNums.forEach(function(element) {
                    element.innerHTML = response.cart_nums; // Вставляем HTML в каждый элемент
                });
                cartAdded();
            } else {
                addBasketErrors.innerHTML = response.errors;
            }
        };
        
        xhr.onloadend = function () {
            addBasketBtn.disabled = false;
            addBasketBtn.classList.remove('loading');
        };

        xhr.send(new URLSearchParams(new FormData(addBasketForm)).toString());
    });
    
    if (variantsLabels) {
        var variantsBlock = document.getElementById('variant_active_block');
        variantsLabels.forEach(function (label) {
            label.addEventListener('click', function () {
                var dataPrice = parseInt(label.querySelector('input').getAttribute('data-price'));
                var dataOldPrice = label.querySelector('input').getAttribute('data-old-price');
                
                priceElement.innerHTML = (dataPrice + additPrice);
                dishPrice.textContent = dataPrice;
                
                var dishPriceParent = dishPrice.parentNode;
                var dishOldPriceParent = dishOldPrice.parentNode;
    
                if (dataOldPrice) {
                    dishOldPrice.textContent = dataOldPrice;
                    dishOldPriceParent.classList.remove('d-none');
                    dishPriceParent.classList.add('new-price');
                } else {
                    dishOldPriceParent.classList.add('d-none');
                    dishPriceParent.classList.remove('new-price');
                }
                let leftPosition = label.getBoundingClientRect().left - label.parentElement.getBoundingClientRect().left;
                variantsBlock.style.left = `${leftPosition}px`;
                variantsLabels.forEach(function (lbl) { lbl.classList.remove('active'); });
                label.classList.add('active');
            });
        });
    
        window.addEventListener('resize', function () {
            var activeLabel = Array.from(variantsLabels).find(function (lbl) {
                return lbl.classList.contains('active');
            });
            if (activeLabel) {
                variantsBlock.style.left = activeLabel.getBoundingClientRect().left + 'px';
            }
        });
    }
    
    if (additionals) {
        additionals.forEach(function (additional) {
            var inputField = additional.querySelector('input');
            var addPrice = parseInt(additional.querySelector('[data-id="additional-product-price"]').textContent);
            var more = additional.querySelector('[data-id="order-button-plus"]');
            var less = additional.querySelector('[data-id="order-button-minus"]');
    
            more.addEventListener('click', function () {
                if (parseInt(inputField.value) < parseInt(inputField.getAttribute('max'))) {
                    inputField.value = parseInt(inputField.value) + 1;
                    additPrice += addPrice;
                    less.disabled = false;
                    priceElement.textContent = parseInt(priceElement.textContent) + addPrice;
                }
                if (parseInt(inputField.value) == parseInt(inputField.getAttribute('max'))) {
                    more.disabled = true;
                }
            });
    
            less.addEventListener('click', function () {
                if (parseInt(inputField.value) > 0) {
                    inputField.value = parseInt(inputField.value) - 1;
                    additPrice -= addPrice;
                    more.disabled = false;
                    priceElement.textContent = parseInt(priceElement.textContent) - addPrice;
                }
                if (parseInt(inputField.value) == 0) {
                    less.disabled = true;
                }
            });
        });
    }

}
