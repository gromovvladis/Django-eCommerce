var notifications_li = $('[data-id="profile-notifications-item"]');
var notifications_form = $('[data-id="profile-notifications-form"]');
var notifications_nums = $('[data-id="notifications-nums"]');

$(notifications_li).each(function(){
    var li = $(this);
    var btn = $(this).find('button');
    $(btn).on('click', function(){
        $.ajax({
            data: {
                "data-behaviours": $(btn).attr("data-behaviours"),
                "data-notification": $(btn).attr("data-notification"),
            }, 
            headers: { "X-CSRFToken": $(notifications_form).find('[name="csrfmiddlewaretoken"]').val() },
            type: $(notifications_form).attr('method'), 
            url: $(notifications_form).attr('action'),
            success: function (response) {
                $(li).remove();
                if (response.action == "archive"){
                    $(notifications_nums).html(response.num_unread);
                    if (response.num_unread == 0){
                        $('[data-id="notification-empty"]').html('Список уведолений пуст')
                    }
                } else {
                    if (response.nums_total == 0){
                        $('[data-id="notification-empty"]').html('Список уведолений пуст')
                    }
                }
            },
            error: function (response) {
                console.log('error');
            },
        });
        return false;  
    });
});
