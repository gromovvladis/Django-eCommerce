var navbar = $("[data-id='navbar-primary']") 
var toggler = $("[data-id='navbar-toggler']") 
var navpills = $(navbar).find(".nav-pills") 
var nav_item = $(".nav-item") 

document.addEventListener('click', function(event) {
    var clickNavbar = $(navbar).is(event.target) || $(navbar).has(event.target).length > 0
    var clickToggler = $(toggler).is(event.target) || $(toggler).has(event.target).length > 0
    if (clickToggler && $(navbar).hasClass('open')) {
      closeNav()
    } else if(clickNavbar || clickToggler) {
      if (window.innerWidth < 1200){
      openNav(event.target)
      }
    } else {
      closeNav()
    }
});

function closeNav() {
  var mobile = window.matchMedia('(min-width:1200px)');
  if (!mobile.matches){
    $(navbar).removeClass('open');
      $(nav_item).each(function(){
        $(this).find('.dropdown-list').removeClass('show');
        $(this).find('.nav-link').attr('aria-expanded', false);
      })
  }
}

function openNav(event) {
  if (!$(event).is('a')) {
    if (!$(navbar).hasClass('open')) {
      var current = $(navbar).find('.current-tab')
      $(current).find('.dropdown-list').removeClass('collapsing');
      $(current).find('.dropdown-list').addClass('show');
      $(current).find('.nav-link').attr('aria-expanded', true);
      $(navpills).animate({scrollTop: event.offsetTop - 60 }, 10);
    }
    $(navbar).addClass('open');
  }
}

// смена ползунка
// $(".tabs-button__button").on('click', function(){
//   $(this).siblings(".tabs-button__active-block").offset({'left':$(this).offset().left});
// })

$(".tabs-button__button").on('click', function(){
  // Задержка, чтобы дождаться применения новой ширины
  setTimeout(() => {
    // Получаем новое смещение после изменения ширины
    var newOffset = $(this).offset().left;

    // Устанавливаем новое смещение для активного блока
    $(this).siblings(".tabs-button__active-block").offset({'left': newOffset});
  }, 0);
});

$(window).resize(function() {
  $(".tabs-button__button").filter('.active').each(function() {
    var activeLabel = $(this);
    var activeBlock = activeLabel.closest('.tabs-button').find('.tabs-button__active-block');
    if (activeLabel.length > 0 && activeBlock.length > 0) {
      activeBlock.offset({ 'left': activeLabel.offset().left });
    }
  });
});