
var searchResult = document.querySelector('#search_result');
var searchBtn = document.querySelector('#search_clean_btn');
var searchInput = document.querySelector('[data-id="v-input-search-field"]');

// function getCsrfToken() {
//     // Extract CSRF token from cookies
//     // var csrf_token = getCookie('csrftoken');
    
//     // var cookies = document.cookie.split(';');
//     // var csrf_token = null;
//     // cookies.forEach(function(cookie) {
//     //     var cookieParts = cookie.trim().split('=');
//     //     if (cookieParts[0] === 'csrftoken') {
//     //         csrf_token = cookieParts[1];
//     //     }
//     // });

//     // Extract from cookies fails for HTML-Only cookies
//     if (!csrf_token) {
//         var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
//         if (csrfInput) {
//             csrf_token = csrfInput.value;
//         }
//     }
//     return csrf_token;
// }

var Autocomplete = function(options) {
    this.url = url_suggestions;
    this.delay = 500;
    this.minimum_length = parseInt(options.minimum_length || 3);
    this.form_elem = null;
    this.query_box = null;
}

Autocomplete.prototype.setup = function() {
    var self = this;
    this.query_box = document.querySelector('[data-id="v-input-search-field"]');

    if (this.query_box) {
        this.query_box.addEventListener('keyup', function() {
            searchResult.innerHTML = '';
            var query = self.query_box.value;
            if (query.length < self.minimum_length) {
                return;
            }
            self.fetch(query);
        });
    }
}

Autocomplete.prototype.fetch = function(query) {
    var self = this;

    searchResult.innerHTML = '';
    searchResult.classList.add('search__loading');

    fetch(this.url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token
            // 'X-CSRFToken': getCsrfToken()
        },
        body: new URLSearchParams({ 'q': query }).toString() 
    })
    .then(response => response.json())
    .then(data => {
        searchResult.classList.remove('search__loading');
        self.show_results(data);
    })
    .catch(error => {
        console.error('Error:', error);
        searchResult.classList.remove('search__loading');
    });
}

Autocomplete.prototype.show_results = function(data) {
    searchResult.innerHTML = data.results;
    findNewForms();
}

document.addEventListener('DOMContentLoaded', function() {
    window.autocomplete = new Autocomplete({
        // form_selector: '.autocomplete-me'
    });
    window.autocomplete.setup();
});

if (searchBtn) {
    searchBtn.addEventListener('click', function() {
        searchInput.value = '';
        searchResult.innerHTML = '';
    });
}