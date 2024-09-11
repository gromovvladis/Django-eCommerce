
let datapicker;
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

let minHours = 10;
let maxHours = 22;
let maxMinutes = 60;
let minMinutes = 0;

var today = new Date();
var hoursMore = 2
if (today.getUTCMinutes() > 20){hoursMore = 3}

var minDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), today.getHours() + hoursMore, 0, 0);
var maxDate = new Date();
maxDate.setUTCDate(minDate.getUTCDate() + 14);
var selectedDate = new Date(minDate);
var selectedTime = new Date(minDate).getTime();

datapicker = new AirDatepicker('#delivery_time_later', {

    autoClose: false,
    isMobile: true,
    timepicker: true,

    altField: "#id_order_time",
    altFieldDateFormat: "dd.MM.yyyy HH:mm",

    dateFormat: 'd MMM',
    timeFormat: 'HH:mm',

    minutesStep: 15,

    toggleSelected: false,
    locale: localLang,

    dateTimeSeparator: " ",

    minHours: minHours,
    maxHours: maxHours,
    maxMinutes: maxMinutes,
    minMinutes: minMinutes,

    selectedDates: selectedDate,
    selectedTime: selectedTime,

    minDate: minDate,
    maxDate: maxDate,

    onShow(isFinished){
        if (isFinished == false){
            console.log('AirDatepickerTime')
            AirDatepickerTime()
        }
    }

});

function AirDatepickerTime(){       
    $.ajax({
        type: 'GET',
        dataType: 'json', 
        url: url_delivery_later,
        success: function (response) {
            minHours = response.datapicker.minHours;
            maxHours = response.datapicker.maxHours;
            minDate = new Date(response.datapicker.minDate);
            maxDate = new Date(response.datapicker.maxDate);
            selectedDate = new Date(minDate);
            selectedTime = new Date(minDate).getTime();

            datapicker.update({        
                minHours: minHours,
                maxHours: maxHours,
                selectedDates: selectedDate,
                selectedTime: selectedTime,
                minDate: minDate,
                maxDate: maxDate,
            });
        },
        error: function (response) {
            console.log('error');
        },
    });
}

AirDatepickerTime();