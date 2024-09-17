var actionMessage = document.getElementById('action_message');

if (actionMessage) {
    var cartAdded = function() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url_action_message, true);
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 400) {
                var response = JSON.parse(xhr.responseText);
                actionMessage.innerHTML = response.upsell_message;
            }
        };
        xhr.send();
    };
}