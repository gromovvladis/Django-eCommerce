
var wishlistForm = document.getElementById('wishlist_form');

if (wishlistForm) {
    var wishlistBtn = wishlistForm.querySelector('#wishlist_btn');
    var url = wishlistForm.action;

    wishlistForm.addEventListener('submit', function (event) {
        event.preventDefault();

        wishlistBtn.disabled = true;
        wishlistBtn.classList.add('loading');

        var xhr = new XMLHttpRequest();
        xhr.open(wishlistForm.method, url, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                var response = JSON.parse(xhr.responseText);
                url = response.url;
                wishlistBtn.innerHTML = response.html;
            }
            wishlistBtn.disabled = false;
            wishlistBtn.classList.remove('loading');
        };

        xhr.onerror = function () {
            wishlistBtn.disabled = false;
            wishlistBtn.classList.remove('loading');
            console.log('error');
        };

        xhr.send(new URLSearchParams(new FormData(wishlistForm)).toString());
    });
}