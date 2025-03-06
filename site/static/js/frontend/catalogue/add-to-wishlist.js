
let wishlistForms = document.querySelectorAll('[data-id="wishlist-form"]');

if (wishlistForms) {
    wishlistForms.forEach((wishlistForm) => {
        let wishlistBtn = wishlistForm.querySelector('[data-id="wishlist-btn"]');
        let removeLine = wishlistForm.getAttribute('data-remove');
        let url = wishlistForm.action;

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
                    if (removeLine == "true") {
                        wishlistForm.remove();
                    } else {
                        url = data.url;
                        wishlistBtn.innerHTML = data.html;
                    }
                })
                .catch(error => {
                    console.error('There was a problem with the fetch operation:', error);
                })
                .finally(() => {
                    wishlistBtn.disabled = false;
                    wishlistBtn.classList.remove('loading');
                });

        });
    });
}