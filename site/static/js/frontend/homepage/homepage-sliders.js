var mainSlider = document.querySelector("[data-id='slider-homepage']");

if (mainSlider) {
    var swiperContainer = mainSlider.querySelector('[data-id="slider-swiper"]');
    var swiperNext = mainSlider.querySelector('[data-id="swiper-next"]');
    var swiperPrev = mainSlider.querySelector('[data-id="swiper-prev"]');
    var swiperPagination = document.querySelector("[data-id='slider-pagination']");

    var SaleSlider = new Swiper(swiperContainer, {
        navigation: {
            nextEl: swiperNext,
            prevEl: swiperPrev,
        },
        speed: 300,
        loop: true,
        autoplay: {
            delay: 4000,
        },
        pagination: {
            el: swiperPagination,
        },
    });

    mainSlider.addEventListener('mouseenter', function () {
        SaleSlider.autoplay.stop();
    });

    mainSlider.addEventListener('mouseleave', function () {
        SaleSlider.autoplay.start();
    });

}

var actions = document.querySelectorAll('[data-id="slider-action"]');

if (actions.length > 0) {
    actions.forEach(function (action) {
        var swiperContainer = action.querySelector('[data-id="slider-swiper"]');
        var swiperNext = action.querySelector('[data-id="swiper-next"]');
        var swiperPrev = action.querySelector('[data-id="swiper-prev"]');

        var sliderPerPage = 3;
        var mobile = window.matchMedia('(max-width:1024px)');

        if (action.getAttribute('data-per-page') === '4' && !mobile.matches) {
            sliderPerPage = 4;
        }

        new Swiper(swiperContainer, {
            slidesPerView: sliderPerPage,
            spaceBetween: 15,
            navigation: {
                nextEl: swiperNext,
                prevEl: swiperPrev,
            },
            speed: 200,
            loop: false,
        });
    });
}