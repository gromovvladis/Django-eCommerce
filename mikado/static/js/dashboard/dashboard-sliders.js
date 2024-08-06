var mainSlider = $("[data-id='slider-dashboard']")

var Slider = new Swiper($(mainSlider).find('[data-id="slider-swiper"]').get(0), {
    navigation: {
      nextEl: $(mainSlider).find('[data-id="swiper-next"]').get(0),
      prevEl: $(mainSlider).find('[data-id="swiper-prev"]').get(0),
    },
    speed: 300,
    loop: true,
    spaceBetween: 50,
});