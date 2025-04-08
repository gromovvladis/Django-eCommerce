
let datapicker;
var localLang = {
  days: ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'],
  daysShort: ['Вос', 'Пон', 'Вто', 'Сре', 'Чет', 'Пят', 'Суб'],
  daysMin: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
  months: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
  monthsShort: ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'],
  clear: 'Очистить',
  dateFormat: 'dd.MM.yyyy',
  timeFormat: 'HH:mm',
  firstDay: 1
};

document.addEventListener('DOMContentLoaded', function () {

  var dateRangePickers = document.querySelectorAll('.daterange');
  var datePickers = document.querySelectorAll('.date');
  var datetimePickers = document.querySelectorAll('.datetime');
  var timePickers = document.querySelectorAll('.time');

  dateRangePickers.forEach(function (picker) {
    // Найти input внутри текущего .datetime
    var input = picker.querySelector('input');
    //   var button = picker.querySelector('.datetime-btn');

    // Инициализация Air Datepicker для текущего input
    var datepicker = new AirDatepicker(input, {

      autoClose: true,
      range: true,
      isMobile: true,
      dateFormat: 'dd.MM.yyyy',

      buttons: ['clear'],

      multipleDatesSeparator: ' - ',

      toggleSelected: false,
      locale: localLang,

    });

    // Открытие календаря при нажатии на кнопку
    //   button.addEventListener('click', function() {
    //       datepicker.show();
    //   });

  });

  datePickers.forEach(function (picker) {
    // Найти input внутри текущего .datetime
    var input = picker.querySelector('input');
    //   var button = picker.querySelector('.datetime-btn');

    // Инициализация Air Datepicker для текущего input
    var datepicker = new AirDatepicker(input, {
      autoClose: true,
      isMobile: true,

      dateFormat: 'dd.MM.yyyy',

      toggleSelected: false,
      locale: localLang,

      // container: '.modal',

    });

    // Открытие календаря при нажатии на кнопку
    //   button.addEventListener('click', function() {
    //       datepicker.show();
    //   });

  });

  datetimePickers.forEach(function (picker) {
    // Найти input внутри текущего .datetime
    var input = picker.querySelector('input');
    //   var button = picker.querySelector('.datetime-btn');

    // Инициализация Air Datepicker для текущего input
    var datepicker = new AirDatepicker(input, {
      autoClose: true,
      isMobile: true,
      timepicker: true,

      dateFormat: 'dd.MM.yyyy',
      timeFormat: 'HH:mm',

      minutesStep: 5,

      toggleSelected: false,
      locale: localLang,

      dateTimeSeparator: " ",

      // container: '.modal',

    });

    // Открытие календаря при нажатии на кнопку
    //   button.addEventListener('click', function() {
    //       datepicker.show();
    //   });
  });

  timePickers.forEach(function (picker) {
    // Найти input внутри текущего .datetime
    var input = picker.querySelector('input');
    //   var button = picker.querySelector('.datetime-btn');

    // Инициализация Air Datepicker для текущего input
    var datepicker = new AirDatepicker(input, {
      autoClose: true,
      isMobile: true,
      timepicker: true,
      datapicker: false,

      timeFormat: 'HH:mm',

      minutesStep: 15,

      toggleSelected: false,
      locale: localLang,

      dateTimeSeparator: " ",

      // container: '.modal',

    });

    // Открытие календаря при нажатии на кнопку
    //   button.addEventListener('click', function() {
    //       datepicker.show();
    //   });
  });

});
