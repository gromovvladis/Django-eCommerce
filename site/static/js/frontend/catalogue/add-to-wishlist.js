
var wishlistForm = document.getElementById('wishlist_form');

if (wishlistForm) {
    var wishlistBtn = wishlistForm.querySelector('#wishlist_btn');
    var url = wishlistForm.action;

    wishlistForm.addEventListener('submit', function (event) {
        event.preventDefault();
        
        wishlistBtn.disabled = true;
        wishlistBtn.classList.add('loading');

        fetch(url, {
            method: wishlistForm.method,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrf_token,
            },
            body: new URLSearchParams(new FormData(wishlistForm)).toString()
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            url = data.url;
            wishlistBtn.innerHTML = data.html;
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        })
        .finally(() => {
            wishlistBtn.disabled = false;
            wishlistBtn.classList.remove('loading');
        });

    });
}