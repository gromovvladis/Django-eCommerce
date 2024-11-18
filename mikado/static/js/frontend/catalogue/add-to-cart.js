var addBasketForm = document.getElementById('add_to_basket_form');

if (addBasketForm) {

    var addBasketBtn = document.getElementById('add_to_cart_btn');
    var priceUnavailable = document.querySelectorAll('[data-id="dish-price-unavailable"]');
    var priceBtn = addBasketBtn.querySelector('[data-id="dish-price-button"]');
    var addBasketErrors = document.querySelector('[data-id="add-to-cart-errors"]');
    
    var variants = addBasketForm.querySelectorAll('[data-id="tab-variants"]');

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
                addBasketErrors.innerHTML = '<div class="error-badge mt-1 border-r15">' + response.errors + "</div>";
            }
        };
        
        xhr.onloadend = function () {
            addBasketBtn.disabled = false;
            addBasketBtn.classList.remove('loading');
        };

        xhr.send(new URLSearchParams(new FormData(addBasketForm)).toString());
    });
    
    if (variants) {

        var childInput = addBasketForm.querySelector('#id_child_id');
        const childData = JSON.parse(childInput.dataset.childs);
        var selectedValues = {};

        variants.forEach(function (variant) {
            var variantBlock = variant.querySelector('[data-id="variant-active-block"]');
            var variantLabels = variant.querySelectorAll('[data-id="variant-label"]');

            variantLabels.forEach(function (label) {

                const variantName = label.dataset.variant; // Получаем название опции
                const selectedInput = label.querySelector('input:checked'); // Получаем выбранный input

                if (selectedInput) {
                    selectedValues[variantName] = parseInt(selectedInput.value);
                }
                console.log(selectedValues); 
                
                label.addEventListener('click', function () {

                    var selectedInput = label.querySelector('input');
                    selectedValues[label.dataset.variant] = parseInt(selectedInput.value);

                    var selectedChild = childData.find(child => {
                        const [childId, childAttrs] = Object.entries(child)[0];
                        const attrs = childAttrs.attr;
                        return Object.keys(selectedValues).every(key => attrs[key] === selectedValues[key]);
                    });
            
                    // Если найден соответствующий объект, получаем его id
                    if (selectedChild) {
                        const ChildId = Object.keys(selectedChild)[0];
                        childInput.value = ChildId;
                        console.log(ChildId)
                        var dataPrice = parseInt(selectedChild[ChildId].price);
                        var dataOldPrice = parseInt(selectedChild[ChildId].old_price);
                        
                        var dishPriceParent = dishPrice.parentNode;
                        var dishOldPriceParent = dishOldPrice.parentNode;

                        if (dataPrice){
                            priceBtn.innerHTML = (dataPrice + additPrice);
                            dishPrice.textContent = dataPrice;
                            addBasketBtn.disabled = false;
                            priceBtn.parentNode.classList.remove('d-none');
                            dishPrice.parentNode.classList.remove('d-none');
                            priceUnavailable.forEach(function(e) {e.classList.add('d-none');});
                            dishPrice.classList.remove('d-none');
                        
                            if (dataOldPrice) {
                                dishOldPrice.textContent = dataOldPrice;
                                dishOldPriceParent.classList.remove('d-none');
                                dishPriceParent.classList.add('new-price');
                            } else {
                                dishOldPriceParent.classList.add('d-none');
                                dishPriceParent.classList.remove('new-price');
                            }
                        } else {
                            addBasketBtn.disabled = true;
                            priceBtn.parentNode.classList.add('d-none');
                            dishPrice.parentNode.classList.add('d-none');
                            dishOldPriceParent.classList.add('d-none');
                            priceUnavailable.forEach(function(e) {e.classList.remove('d-none');});
                        }
                    }

                    let leftPosition = label.getBoundingClientRect().left - label.parentElement.getBoundingClientRect().left;
                    variantBlock.style.left = `${leftPosition}px`;
                    variantLabels.forEach(function (lbl) { lbl.classList.remove('active'); });
                    label.classList.add('active');
                });

            });
            
            window.addEventListener('resize', function () {
                var activeLabel = Array.from(variantLabels).find(function (lbl) {
                    return lbl.classList.contains('active');
                });
                if (activeLabel) {
                    variantBlock.style.left = (activeLabel.getBoundingClientRect().left - activeLabel.parentElement.getBoundingClientRect().left) + 'px';
                    console.log(variantBlock.style.left)
                }
            });
            
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
                    priceBtn.textContent = parseInt(priceBtn.textContent) + addPrice;
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
                    priceBtn.textContent = parseInt(priceBtn.textContent) - addPrice;
                }
                if (parseInt(inputField.value) == 0) {
                    less.disabled = true;
                }
            });
        });
    }

}
