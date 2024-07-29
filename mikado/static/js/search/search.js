var search_result = $('#search_result')
var search_btn = $('#search_clean_btn')
var search_input = $('[data-id="v-input-search-field"]')

$(document).ready(function() {
    window.autocomplete = new Autocomplete({
    // form_selector: '.autocomplete-me'
    })
    window.autocomplete.setup()
})

function getCsrfToken() {
    // Extract CSRF token from cookies
    var cookies = document.cookie.split(';');
    var csrf_token = null;
    $.each(cookies, function(index, cookie) {
        var cookieParts = $.trim(cookie).split('=');
        if (cookieParts[0] == 'csrftoken') {
            csrf_token = cookieParts[1];
        }
    });
    // Extract from cookies fails for HTML-Only cookies
    if (! csrf_token) {
        csrf_token = $(document.forms.valueOf()).find('[name="csrfmiddlewaretoken"]')[0].value;
    }
    return csrf_token;
};


var Autocomplete = function(options) {
    // this.form_selector = options.form_selector
    this.url = url_suggestions
    this.delay = 500
    this.minimum_length = parseInt(options.minimum_length || 3)
    this.form_elem = null
    this.query_box = null
}

Autocomplete.prototype.setup = function() {
    var self = this

    // this.form_elem = $(this.form_selector)
    this.query_box = search_input

    // Watch the input box.
    this.query_box.on('keyup', function() {
    $(search_result).empty();
    var query = self.query_box.val()

    if(query.length < self.minimum_length) {
        return false
    }
    self.fetch(query)
    })
}

Autocomplete.prototype.fetch = function(query) {
    var self = this;
    $(search_result).empty();
    $(search_result).addClass('search__loading');

    $.ajax({
    headers: { "X-CSRFToken": getCsrfToken() },
    type: 'POST',
    url: this.url
    , data: {
        'q': query
    }
    , success: function(data) {
        $(search_result).removeClass('search__loading');
        self.show_results(data);
    }
    })
}


Autocomplete.prototype.show_results = function(data) {
    $(search_result).html(data.results);
    findNewForms();
}

$(search_btn).on('click', function(){
    $(search_input).val('');
    $(search_result).empty()
})
