var actionMessage = document.getElementById('action_message');

if (actionMessage) {
    var cartAdded = function () {
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