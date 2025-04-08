var open_map = $('#open_map');
var mapContainer = document.querySelector('#map');

const DELIVERYBOUNDS = [[56.120657, 92.640634], [55.946021, 93.258483]];
const MAPCENTER = [56.008331, 92.878786];

var map;
var placemark;
var shippingZones;
var LayoutPin;
var offsetBtns = 150;


// подсказки при поиске запрос в Яндекс
if (window.ymaps) {
    ymaps.ready(function () {

        LayoutPin = ymaps.templateLayoutFactory.createClass(
            '<div class="wrapper-icon-shipping">' +

            '{% if properties.loading  %}' +

            '<svg class="pin-icon pin-icon__loader" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">' +
            '<circle cx="12" cy="12" r="6" stroke-width="8" fill="none" stroke-dasharray="100" stroke-dashoffset="80"></circle>' +
            '<animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 0 0" to="360 0 0" dur="2s" repeatCount="indefinite"></animateTransform>' +
            '</svg>' +

            '{% else %}' +

            '<div class="icon-shipping__title {% if properties.error %}icon-shipping__title_error{% endif %}">' +
            '{% if properties.error %}' +
            '<span>{{ properties.error|default:"Ошибка!" }}</span> ' +
            '{% else %}' +
            '<span class="shipping-balloon__minutes">№{{ properties.number }} - {{ properties.name }}</span>' +
            '<br>' +
            '<span class="shipping-balloon__text">Сумма заказа: {{ properties.order_price }}&nbsp;₽</span>' +
            '<br>' +
            '<span class="shipping-balloon__text">Стоимость доставки: {{ properties.shipping_price }}&nbsp;₽</span>' +
            '<br>' +
            '{% if properties.isHide %}' +
            '<span class="shipping-balloon__text text-danger">Не показывать на карте</span>' +
            '<br>' +
            '{% endif %}' +
            '{% if !properties.isAvailable %}' +
            '<span class="shipping-balloon__text text-warning">Не доступно для заказа</span>' +
            '<br>' +
            '{% endif %}' +
            '{% endif %}' +
            '</div>' +

            '{% endif %}' +

            '<svg class="pin-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
            '<circle cx="12" cy="10" r="10"></circle>' +
            '<circle cx="12" cy="10" r="5" fill="#c21313"></circle>' +
            '</svg>' +

            '</div>'
        )

    });
}

// создаем карту при вводе адреса, при расчете маршрута и предоставим возможность выбора адреса по карте
function createMap(zonaId = null) {
    ymaps.ready(function () {
        if (!map) {
            map = new ymaps.Map(mapContainer, {
                center: MAPCENTER,
                zoom: 12,
                controls: [],
            }, {
                yandexMapDisablePoiInteractivity: true,
                suppressMapOpenBlock: true,
                maxZoom: 18,
                minZoom: 10,
            });

            $.ajax({
                url: url_shipping_zones,
                dataType: 'json',
                success: function (json) {
                    ZonesInit(json, zonaId);
                }
            });

            //кнопки зума
            ZoomLayout = ymaps.templateLayoutFactory.createClass(
                '<div id="zoom-in" class="v-map-custom-controls--zoom-in"><svg viewBox="0 0 24 24" fill="none"><path d="M6 12H18M12 6V18" stroke="#007bff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>' +
                '<div id="zoom-out" class="v-map-custom-controls--zoom-out"><svg viewBox="0 0 24 24" fill="none"><path d="M6 12L18 12" stroke="#007bff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
                ,
                {

                    // Переопределяем методы макета, чтобы выполнять дополнительные действия
                    // при построении и очистке макета.
                    build: function () {
                        // Вызываем родительский метод build.
                        ZoomLayout.superclass.build.call(this);

                        // Привязываем функции-обработчики к контексту и сохраняем ссылки
                        // на них, чтобы потом отписаться от событий.
                        this.zoomInCallback = ymaps.util.bind(this.zoomIn, this);
                        this.zoomOutCallback = ymaps.util.bind(this.zoomOut, this);

                        // Начинаем слушать клики на кнопках макета.
                        $('#zoom-in').bind('click', this.zoomInCallback);
                        $('#zoom-out').bind('click', this.zoomOutCallback);
                    },

                    clear: function () {
                        // Снимаем обработчики кликов.
                        $('#zoom-in').unbind('click', this.zoomInCallback);
                        $('#zoom-out').unbind('click', this.zoomOutCallback);

                        // Вызываем родительский метод clear.
                        ZoomLayout.superclass.clear.call(this);
                    },

                    zoomIn: function () {
                        var map = this.getData().control.getMap();
                        map.setZoom(map.getZoom() + 1, { checkZoomRange: true, duration: 200 });
                    },

                    zoomOut: function () {
                        var map = this.getData().control.getMap();
                        map.setZoom(map.getZoom() - 1, { checkZoomRange: true, duration: 200 });
                    }

                });
            var zoomControl = new ymaps.control.ZoomControl({
                options: {
                    layout: ZoomLayout,
                    position: {
                        bottom: (offsetBtns + 55) + "px",
                        right: '14px',
                    },
                }
            });

            // Добавим элемент управления с собственной меткой геолокации на карте.
            var geolocationControl = new ymaps.control.GeolocationControl({
                options: {
                    layout: ymaps.templateLayoutFactory.createClass(
                        '<div id="geolocation" class="v-map-custom-controls--geolocation"><svg viewBox="-1 -1 26 26" fill="none"><path fill-rule="evenodd" clip-rule="evenodd" d="M19.925 1.78443C21.5328 1.18151 23.1029 2.75156 22.5 4.35933L16.0722 21.5C15.3574 23.4061 12.5838 23.1501 12.23 21.1453L10.8664 13.418L3.1391 12.0544C1.13427 11.7006 0.878261 8.92697 2.78443 8.21216L19.925 1.78443ZM20.6273 3.65708L3.48668 10.0848L11.2139 11.4485C12.0417 11.5945 12.6898 12.2426 12.8359 13.0704L14.1996 20.7977L20.6273 3.65708Z" fill="#007bff"/></svg></div>'
                    ),
                    position: {
                        bottom: offsetBtns + "px",
                        right: '14px'
                    }
                }
            });

            geolocationControl.events.add('locationchange', function (event) {
                var geolocation = ymaps.geolocation;
                geolocation.get({
                    provider: 'browser',
                    mapStateAutoApply: false
                }).then(function (result) {
                    result.geoObjects.options.set('preset', 'islands#geolocationIcon');
                    map.geoObjects.add(result.geoObjects);
                    map.panTo(result.geoObjects.position);
                    map.setZoom(15);
                });
            });

            var controlsPane = new ymaps.pane.StaticPane(map, { zIndex: 420 });
            map.panes.append('customControls', controlsPane);
            var placesPane = map.panes.get('controls').getElement();
            $(placesPane).addClass('v-map-custom-controls d-flex flex-column align-center justify-center');

            map.controls.add(zoomControl);
            map.controls.add(geolocationControl);

            store = new ymaps.Placemark(
                [56.050918, 92.904378], {
                iconCaption: "Mikado",
            }, {
                iconLayout: 'default#image',
                // Своё изображение иконки метки.
                iconImageHref: '/static/svg/webshop/planet/map/store.svg',
                // Размеры метки.
                iconImageSize: [40, 40],
                // Смещение левого верхнего угла иконки относительно
                // её "ножки" (точки привязки).
                iconImageOffset: [-30, -30],
                hasBalloon: false,
            });

            map.geoObjects.add(store);

        }
    });
}

// переместить плейсмарк
function movePlacemark(coords) {
    if (placemark) {
        placemark.geometry.setCoordinates(coords);
    } else {
        placemark = new ymaps.Placemark(coords, {}, {
            hasBalloon: true,
            hasHint: false,
            draggable: false,

            iconLayout: 'default#imageWithContent',
            iconImageHref: "",
            iconImageSize: [25, 25],
            iconImageOffset: [-11, -11],
            iconContentLayout: LayoutPin,
        });
        map.geoObjects.add(placemark);
    }
    placemark.properties.set('loading', true);
    showBalloon(coords);
}

// Определяем адрес по координатам (обратное геокодирование).
function showBalloon(coords) {
    var zonaId = getZonaId(coords);
    $.ajax({
        url: url_shipping_zona,
        type: 'POST',
        headers: { "X-CSRFToken": csrf_token },
        data: { "zona_id": zonaId },
        success: function (responce) {
            if (responce.error) {
                placemark.properties.set({
                    'loading': false,
                    'error': responce.error,
                });
            } else {
                placemark.properties.set({
                    'loading': false,
                    'error': false,
                    'number': zonaId,
                    'name': responce.name,
                    'order_price': responce.order_price,
                    'shipping_price': responce.shipping_price,
                    'isAvailable': responce.isAvailable,
                    'isHide': responce.isHide,
                });
            }
        },
    });

}

// создание зон доставки
function ZonesInit(json, zonaId = null) {
    // Добавляем зоны на карту.
    shippingZones = ymaps.geoQuery(json).addToMap(map);
    // Задаём цвет и контент балунов полигонов.
    var color = ""
    shippingZones.each(function (zona) {
        if (zonaId) {
            if (zona.properties.get('number') == zonaId) {
                color = "#6610f2"
            }
            else {
                color = "#c8e2ff"
            }
        } else {
            if (zona.properties.get('hide')) {
                color = "#a5a5a5"
            } else if (zona.properties.get('available')) {
                color = "#59ff85"
            } else {
                color = "#ed4543"
            }
        }
        zona.options.set({
            fillColor: color,
            strokeColor: color,
            fillOpacity: 0.15,
            strokeWidth: 0,
            strokeOpacity: 0,
        });
        zona.options.set({ 'hasBalloon': false, 'hasHint': false });
        zona.events.add('click', function (e) {
            movePlacemark(e.get('coords'));
        });
    });
}

// проверка адреса в зоне доставки
function getZonaId(coords) {
    var zona = shippingZones.searchContaining(coords).get(0);
    if (!zona) {
        return 0;
    }
    return zona.properties._data.number;
}