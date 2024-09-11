
var notificationsForm = document.querySelector('[data-id="profile-notifications-form"]');

if (notificationsForm) {
    var notificationsLi = notificationsForm.querySelectorAll('[data-id="profile-notifications-item"]');
    var notificationsNums = document.querySelector('[data-id="notifications-nums"]');

    notificationsLi.forEach(function (li) {
        var btn = li.querySelector('button');
        btn.addEventListener('click', function () {
            var dataBehaviours = btn.getAttribute('data-behaviours');
            var dataNotification = btn.getAttribute('data-notification');
            var csrfToken = notificationsForm.querySelector('[name="csrfmiddlewaretoken"]').value;
            var method = notificationsForm.getAttribute('method');
            var actionUrl = notificationsForm.getAttribute('action');

            fetch(actionUrl, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    "data-behaviours": dataBehaviours,
                    "data-notification": dataNotification
                })
            })
            .then(response => response.json())
            .then(data => {
                li.remove();
                if (data.action === "archive") {
                    notificationsNums.textContent = data.num_unread;
                    if (data.num_unread === 0) {
                        document.querySelector('[data-id="notification-empty"]').textContent = 'Список уведомлений пуст';
                    }
                } else {
                    if (data.nums_total === 0) {
                        document.querySelector('[data-id="notification-empty"]').textContent = 'Список уведомлений пуст';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });

            return false;
        });
    });
}
