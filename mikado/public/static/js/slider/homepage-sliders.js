var mainSlider = $("[data-id='slider-homepage']")

var SaleSlider = new Swiper($(mainSlider).find('[data-id="slider-swiper"]').get(0), {
    navigation: {
      nextEl: $(mainSlider).find('[data-id="swiper-next"]').get(0),
      prevEl: $(mainSlider).find('[data-id="swiper-prev"]').get(0),
    },
      speed: 300,
      loop: true,
  
     autoplay: {
         delay: 4000,
     },
  
      pagination: {
        el: "[data-id='slider-pagination']",
      },
  
});

jQuery("[data-id='slider-homepage']").on('mouseenter', function(e){
    SaleSlider.autoplay.stop();
});
jQuery("[data-id='slider-homepage']").on('mouseleave', function(e){
    SaleSlider.autoplay.start();
});


var actions = $('[data-id="slider-action"]')
$(actions).each(function(){

  var action = $(this)
  var mobile = window.matchMedia('(max-width:1024px)');
  var slider_per_page = 3;

  if ($(this).attr('data-per-page') == 4){
    if (!mobile.matches){
      slider_per_page = 4;
    }
  }
  
  var ActionSlider = new Swiper($(action).find('[data-id="slider-swiper"]').get(0), {
    slidesPerView: slider_per_page,
    spaceBetween: 15,
    navigation: {
      nextEl: $(action).find('[data-id="swiper-next"]').get(0),
      prevEl: $(action).find('[data-id="swiper-prev"]').get(0),
    },
      speed: 200,
      loop: false,
  });
});
