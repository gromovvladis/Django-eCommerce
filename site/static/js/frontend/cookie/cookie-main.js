var weUseCookie = document.querySelector('[data-id="cookie"]');
var actionBack = null;

function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length === 2) return parts.pop().split(";").shift();
}

function setCookie(name, value, days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function fetchCookieInfo() {
    fetch(url_get_cookie)
        .then(response => response.json())
        .then(data => {
            weUseCookie.innerHTML = data.cookies;
        })
        .catch(error => console.error('Error fetching cookie info:', error));
}

// Check cookie and fetch if not present
var cookieAgree = getCookie('cookieAgree');
if (!cookieAgree) {
    fetchCookieInfo();
}

// Agree to cookies
function agree_cookie() {
    setCookie('cookieAgree', true, 1000);
    weUseCookie.innerHTML = '';
};

// Go back or execute actionBack
function getBack() {
    if (actionBack) {
        actionBack();
        actionBack = null;
    } else {
        history.back();
    }
};