
var searchResult = document.querySelector('#search_result');
var searchBtn = document.querySelector('#search_clean_btn');
var searchInput = document.querySelector('[data-id="v-input-search-field"]');

// function initSortWidget() {
//     // Auto-submit (hidden) search form when selecting a new sort-by option
//     var sortBy = document.querySelector('#id_sort_by');
//     if (sortBy) {
//         sortBy.addEventListener('change', function() {
//             var form = sortBy.closest('form');
//             if (form) {
//                 form.submit();
//             }
//         });
//     }
// }

// function initFacetWidgets() {
//     // Bind events to facet checkboxes
//     var facetCheckboxes = document.querySelectorAll('.facet_checkbox');
//     facetCheckboxes.forEach(function(checkbox) {
//         checkbox.addEventListener('change', function() {
//             var url = checkbox.nextElementSibling.value;
//             if (url) {
//                 window.location.href = url;
//             }
//         });
//     });
// }


// initFacetWidgets();
// initSortWidget();


function getCsrfToken() {
    // Extract CSRF token from cookies
    var cookies = document.cookie.split(';');
    var csrf_token = null;

    cookies.forEach(function(cookie) {
        var cookieParts = cookie.trim().split('=');
        if (cookieParts[0] === 'csrftoken') {
            csrf_token = cookieParts[1];
        }
    });

    // Extract from cookies fails for HTML-Only cookies
    if (!csrf_token) {
        var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            csrf_token = csrfInput.value;
        }
    }
    return csrf_token;
}

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
            'X-CSRFToken': getCsrfToken()
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















// $(document).ready(function() {
//     if ($(search_result).length > 0) {
//         window.autocomplete = new Autocomplete({
//         // form_selector: '.autocomplete-me'
//         })
//         window.autocomplete.setup()
//     }
// })



// function getCsrfToken() {
//     // Extract CSRF token from cookies
//     var cookies = document.cookie.split(';');
//     var csrf_token = null;
//     $.each(cookies, function(index, cookie) {
//         var cookieParts = $.trim(cookie).split('=');
//         if (cookieParts[0] == 'csrftoken') {
//             csrf_token = cookieParts[1];
//         }
//     });
//     // Extract from cookies fails for HTML-Only cookies
//     if (! csrf_token) {
//         csrf_token = $(document.forms.valueOf()).find('[name="csrfmiddlewaretoken"]')[0].value;
//     }
//     return csrf_token;
// };


// var Autocomplete = function(options) {
//     // this.form_selector = options.form_selector
//     this.url = url_suggestions
//     this.delay = 500
//     this.minimum_length = parseInt(options.minimum_length || 3)
//     this.form_elem = null
//     this.query_box = null
// }

// Autocomplete.prototype.setup = function() {
//     var self = this

//     // this.form_elem = $(this.form_selector)
//     this.query_box = search_input

//     // Watch the input box.
//     this.query_box.on('keyup', function() {
//     $(search_result).empty();
//     var query = self.query_box.val()

//     if(query.length < self.minimum_length) {
//         return false
//     }
//     self.fetch(query)
//     })
// }

// Autocomplete.prototype.fetch = function(query) {
//     var self = this;
//     $(search_result).empty();
//     $(search_result).addClass('search__loading');

//     $.ajax({
//     headers: { "X-CSRFToken": getCsrfToken() },
//     type: 'POST',
//     url: this.url
//     , data: {
//         'q': query
//     }
//     , success: function(data) {
//         $(search_result).removeClass('search__loading');
//         self.show_results(data);
//     }
//     })
// }


// Autocomplete.prototype.show_results = function(data) {
//     $(search_result).html(data.results);
//     findNewForms();
// }

// $(search_btn).on('click', function(){
//     $(search_input).val('');
//     $(search_result).empty()
// })
