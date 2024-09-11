var filter_fields = $('[data-id="v-input-field"]');
let datapicker_filter;

var localLang = {
    days: ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'],
    daysShort: ['Вос', 'Пон', 'Вто', 'Сре', 'Чет', 'Пят', 'Суб'],
    daysMin: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
    months: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
    monthsShort: ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'],
    today: 'Сегодня',
    clear: 'Очистить',
    dateFormat: 'dd.MM.yyyy',
    timeFormat: 'HH:mm',
    firstDay: 1
};

datapicker_filter = new AirDatepicker('#id_date_range', {

    autoClose: false,
    isMobile: true,
    range: true,

    altField: "#id_order_time",
    altFieldDateFormat: "dd.MM.yyyy",

    dateFormat: 'dd.MM.yyyy',

    buttons: ['clear'],

    multipleDatesSeparator: ' - ',

    toggleSelected: false,
    locale: localLang,

});


$(filter_fields).each(function(){
    var wrapper = $(this);
    var input_field = $(this).find('[data-id="order-input"]');
    if($(input_field).val() != ""){
        wrapper.addClass('v-input__label-active')
    }
    $(input_field).focusin(function(){
        wrapper.addClass('v-input__label-active')
    })
    $(input_field).focusout(function(){
        if($(input_field).val() == ""){
            wrapper.removeClass('v-input__label-active')
        }
    })
});