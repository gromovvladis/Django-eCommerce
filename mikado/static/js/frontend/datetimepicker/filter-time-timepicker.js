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

var inputFields = document.querySelectorAll('[data-id="v-input-field"]');
inputFields.forEach(function(wrapper) {
    var inputField = wrapper.querySelector('[data-id="order-input"]');

    if (inputField.value !== "") {
        wrapper.classList.add('v-input__label-active');
    }

    inputField.addEventListener('focusin', function() {
        wrapper.classList.add('v-input__label-active');
    });

    inputField.addEventListener('focusout', function() {
        if (inputField.value === "") {
            wrapper.classList.remove('v-input__label-active');
        }
    });
});
