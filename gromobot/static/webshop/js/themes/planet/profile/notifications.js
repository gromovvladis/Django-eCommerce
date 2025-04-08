
var notificationsForm = document.querySelector('[data-id="profile-notifications-form"]');

if (notificationsForm) {
    var notificationsLi = notificationsForm.querySelectorAll('[data-id="profile-notifications-item"]');
    var notificationsNums = document.querySelectorAll('[data-id="notifications-nums"]');

    notificationsLi.forEach(function (li) {
        var btn = li.querySelector('button');
        btn.addEventListener('click', function () {
            var dataBehaviours = btn.getAttribute('data-behaviours');
            var dataNotification = btn.getAttribute('data-notification');
            var method = notificationsForm.getAttribute('method');
            var actionUrl = notificationsForm.getAttribute('action');

            fetch(actionUrl, {
                method: method,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrf_token
                },
                body: new URLSearchParams({
                    "data-behaviours": dataBehaviours,
                    "data-notification": dataNotification
                }).toString()
            })
                .then(response => response.json())
                .then(data => {
                    li.remove();
                    if (data.action === "archive") {
                        notificationsNums.forEach(function (element) {
                            element.textContent = data.num_unread;
                        });
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
