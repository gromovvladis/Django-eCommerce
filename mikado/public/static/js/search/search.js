var search_result = $('#search_result')
var search_btn = $('#search_clean_btn')
var search_input = $('[data-id="v-input-search-field"]')

// var search_form = $('#search_form')
// $(search_form).submit(function () {
//     $(search_btn).attr("disabled", true);
//     $(search_btn).addClass('loading');
//     $(search_btn).html('Идет поиск');
//     $.ajax({
//         data: $(this).serialize(), 
//         type: $(this).attr('method'), 
//         url: url_search,
//         success: function (response) {
//             $(search_btn).attr("disabled", false);
//             $(search_btn).removeClass('loading');
//             $(search_btn).html('Поиск');
//             $(search_result).html(response.results);
//         },
//     });
//     return false;  
// });


// Autocomplete.prototype.show_results = function(data) {
//     // Remove any existing results.
//     $('.ac-results').remove()

//     var results = data.results || []
//     var results_wrapper = $('<div class="ac-results"></div>')
//     var base_elem = $('<div class="result-wrapper"><a href="" class="ac-result"></a></div>')

//     console.log(results)

//     if (results.length > 0) {
//         for(var res_offset in results) {
//             var elem = base_elem.clone()
//             // Don't use .html(...) here, as you open yourself to XSS.
//             // Really, you should use some form of templating.
//             elem.find('.ac-result').text(results[res_offset].text)
//             elem.find('.ac-result').attr("href",results[res_offset].url)
        
//             results_wrapper.append(elem)
//         }
//     } else {
//     var elem = base_elem.clone()
//     elem.text("No results found.")
//     results_wrapper.append(elem)
//     }

//     this.query_box.after(results_wrapper)
// }



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


$(document).ready(function() {
    window.autocomplete = new Autocomplete({
    // form_selector: '.autocomplete-me'
    })
    window.autocomplete.setup()
})


$(search_btn).on('click', function(){
    $(search_input).val('');
    $(search_result).empty()
})


