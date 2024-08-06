var navbar = $("[data-id='navbar-primary']") 
var toggler = $("[data-id='navbar-toggler']") 
var navpills = $(navbar).find(".nav-pills") 
var nav_item = $(".nav-item") 

document.addEventListener('click', function(event) {
    var clickNavbar = $(navbar).is(event.target) || $(navbar).has(event.target).length > 0
    var clickToggler = $(toggler).is(event.target) || $(toggler).has(event.target).length > 0
    if (clickToggler && $(navbar).hasClass('open')) {
      closeNav()
    } else if((clickNavbar || clickToggler)) {
      openNav(event.target)
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
  if (!$(navbar).hasClass('open')) {
    var current = $(navbar).find('.current-tab')
    $(current).find('.dropdown-list').removeClass('collapsing');
    $(current).find('.dropdown-list').addClass('show');
    $(current).find('.nav-link').attr('aria-expanded', true);
    console.log(event.offsetTop)
    $(navpills).animate({scrollTop: event.offsetTop - 60 }, 10);
  }
  $(navbar).addClass('open');
}
