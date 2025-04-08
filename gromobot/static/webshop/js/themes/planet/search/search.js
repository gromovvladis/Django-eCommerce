
var searchInput = document.querySelector('[data-id="input-search-field"]');
if (searchInput) {
    var searchResult = document.getElementById('search_result');
    var searchBtn = document.getElementById('search_clean_btn');
    
    var Autocomplete = function (options) {
        this.url = url_suggestions;
        this.delay = 500;
        this.minimum_length = parseInt(options.minimum_length || 3);
        this.form_elem = null;
        this.query_box = null;
    }
    
    Autocomplete.prototype.setup = function () {
        var self = this;
        this.query_box = document.querySelector('[data-id="input-search-field"]');
    
        if (this.query_box) {
            this.query_box.addEventListener('keyup', function () {
                searchResult.innerHTML = '';
                var query = self.query_box.value;
                if (query.length < self.minimum_length) {
                    return;
                }
                self.fetch(query);
            });
        }
    }
    
    Autocomplete.prototype.fetch = function (query) {
        var self = this;
        searchResult.innerHTML = '';
        searchResult.classList.add('search__loading');
    
        fetch(this.url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrf_token,
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
    
    Autocomplete.prototype.show_results = function (data) {
        searchResult.innerHTML = data.results;
        findNewForms();
    }
    
    document.addEventListener('DOMContentLoaded', function () {
        window.autocomplete = new Autocomplete({
        });
        window.autocomplete.setup();
    });
    
    if (searchBtn) {
        searchBtn.addEventListener('click', function () {
            searchInput.value = '';
            searchResult.innerHTML = '';
        });
    }
}