var actionMessage = document.getElementById('action_message');

if (actionMessage) {
    var cartAdded = function() {
        // var xhr = new XMLHttpRequest();
        // xhr.open('GET', url_action_message, true);
        // xhr.onload = function() {
        //     if (xhr.status >= 200 && xhr.status < 400) {
        //         var response = JSON.parse(xhr.responseText);
        //         actionMessage.innerHTML = response.upsell_message;
        //     }
        // };
        // xhr.send();
        // fetch(url_action_message,{
        //     headers: {
        //         'Content-Type': 'application/x-www-form-urlencoded',
        //         'X-Requested-With': 'XMLHttpRequest',
        //         'X-CSRFToken': csrf_token,
        //     },
        // })
        fetch(url_action_message)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            actionMessage.innerHTML = data.upsell_message;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
    };
}