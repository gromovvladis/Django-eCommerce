
var waiting_payment = $('[data-id="waiting-payment"]');
var payment_status = $('[data-id="payment-status"]');
var payment_svg = $('[data-id="payment-icon-svg"]');
var waiting_seconds = 15;

interval = setInterval(function() {
    if (waiting_seconds > 0) {
        waiting_seconds = waiting_seconds - 3; 
        get_payment_info();
    } else {
        closeModal();
        $(payment_status).html("Ответ от банка не получен. Обновите страницу")
    }
}, 3000);  


function get_payment_info(){
    $.ajax({
        type: 'GET', 
        headers: { "X-CSRFToken": csrf_token },
        url: update_payment_url,
        success: function (response){
            console.log(response.status)
            closeModal(response);
        },
    });
}

function closeModal(response=null){
    if (response){
        $(payment_status).html(response.status);
        if (response.status == "Ожидает оплаты"){
            $(payment_svg).html('<use xlink:href="#svg-order-pending"></use>');
        } else if (response.status == "Отменен") {
            $(payment_svg).html('<use xlink:href="#svg-order-cancel"></use>');
        } else {
            $(payment_svg).html('<use xlink:href="#svg-order-success"></use>');
        }
    }
    clearInterval(interval);
    $(waiting_payment).addClass('d-none');
}
