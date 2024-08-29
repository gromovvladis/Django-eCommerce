
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

document.addEventListener('DOMContentLoaded', function() {

  var dateRangePickers = document.querySelectorAll('.daterange');
  var datePickers = document.querySelectorAll('.date');
  var datetimePickers = document.querySelectorAll('.datetime');

  dateRangePickers.forEach(function(picker) {
      // Найти input внутри текущего .datetime
      var input = picker.querySelector('input');
      var button = picker.querySelector('.datetime-btn');

      // Инициализация Air Datepicker для текущего input
      var datepicker = new AirDatepicker(input, {

            autoClose: false,
            range: true,
        
            dateFormat: 'dd.MM.yyyy',
        
            buttons: ['clear'],
        
            multipleDatesSeparator: ' - ',
        
            toggleSelected: false,
            locale: localLang,

      });

      // Открытие календаря при нажатии на кнопку
      button.addEventListener('click', function() {
          datepicker.show();
      });

  });

  datePickers.forEach(function(picker) {
      // Найти input внутри текущего .datetime
      var input = picker.querySelector('input');
      var button = picker.querySelector('.datetime-btn');

      // Инициализация Air Datepicker для текущего input
      var datepicker = new AirDatepicker(input, {
          autoClose: true,
          isMobile: false,

          dateFormat: 'dd.MM.yyyy',

          toggleSelected: false,
          locale: localLang,

          container: '.modal-body',

          // position({$datepicker, $target, $pointer, done}) {
          //   let popper = createPopper($target, $datepicker, {
          //       placement: 'top',
          //       modifiers: [
          //           {
          //               name: 'flip',
          //               options: {
          //                   padding: {
          //                       top: 64
          //                   }
          //               }
          //           },
          //           {
          //               name: 'offset',
          //               options: {
          //                   offset: [0, 20]
          //               }
          //           },
          //           {
          //               name: 'arrow',
          //               options: {
          //                   element: $pointer
          //               }
          //           }
          //       ]
          //   })
          // }

      });

      // Открытие календаря при нажатии на кнопку
      button.addEventListener('click', function() {
          datepicker.show();
      });

  });

  datetimePickers.forEach(function(picker) {
      // Найти input внутри текущего .datetime
      var input = picker.querySelector('input');
      var button = picker.querySelector('.datetime-btn');

      // Инициализация Air Datepicker для текущего input
      var datepicker = new AirDatepicker(input, {
          autoClose: false,
          isMobile: true,
          timepicker: true,

          dateFormat: 'dd.MM.yyyy',
          timeFormat: 'HH:mm',

          minutesStep: 5,

          toggleSelected: false,
          locale: localLang,

          dateTimeSeparator: " ",
          
          container: '.modal-body',

      });

      // Открытие календаря при нажатии на кнопку
      button.addEventListener('click', function() {
          datepicker.show();
      });
  });

});
