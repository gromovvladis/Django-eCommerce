var additionalProducts = document.querySelectorAll('[data-id="additional-product"]');
var priceElement = document.querySelector('[data-id="dish-price-button"]');

if (additionalProducts.length > 0) {
    additionalProducts.forEach(function (product) {
        var inputField = product.querySelector('input');
        var addPrice = parseInt(product.querySelector('[data-id="additional-product-price"]').textContent);
        var moreButton = product.querySelector('[data-id="order-button-plus"]');
        var lessButton = product.querySelector('[data-id="order-button-minus"]');

        moreButton.addEventListener('click', function () {
            if (parseInt(inputField.value) < parseInt(inputField.max)) {
                inputField.value = parseInt(inputField.value) + 1;
                lessButton.disabled = false;
                priceElement.textContent = parseInt(priceElement.textContent) + addPrice;
            }
            if (parseInt(inputField.value) == parseInt(inputField.max)) {
                moreButton.disabled = true;
            }
        });

        lessButton.addEventListener('click', function () {
            if (parseInt(inputField.value) > 0) {
                inputField.value = parseInt(inputField.value) - 1;
                moreButton.disabled = false;
                priceElement.textContent = parseInt(priceElement.textContent) - addPrice;
            }
            if (parseInt(inputField.value) == 0) {
                lessButton.disabled = true;
            }
        });
    });
}