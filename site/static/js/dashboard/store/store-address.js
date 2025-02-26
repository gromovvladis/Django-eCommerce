var line1 = document.querySelector('#id_line1');

var suggests = document.querySelector('#suggest_list');
var cleanAddress = document.querySelector('#clean_address');

var mapContainer = document.querySelector('.delivery__map');
var mapdiv = mapContainer.querySelector('#map');
// var controls = mapContainer.querySelector('#map_controls');

var lon = document.querySelector('#id_coords_long');
var lat = document.querySelector('#id_coords_lat');

const MAPCENTER = [56.0435, 92.9075];
const DELIVERYBOUNDS = [[56.043545, 92.6406], [55.9460, 93.2584]];

var map;
var placemark;
var addressInfo;
var mapControl;
var cleanButton;
var deliveryZones;
var LayoutPin
var offsetBtns = 150;

var selection = -1;
var li_list = [];


// ====================  SUGGEST + LAYOUT + MAP CONTROLS  ===========================


// строка с адресом на карте Яндекс и layout

ymaps.ready(function () {

    // CustomControlClass = function (options) {
    //     CustomControlClass.superclass.constructor.call(this, options);
    //     this._$content = null;
    //     this._geocoderDeferred = null;
    // };

    // ymaps.util.augment(CustomControlClass, ymaps.collection.Item, {
    //     onAddToMap: function (map) {
    //         CustomControlClass.superclass.onAddToMap.call(this, map);
    //         this._lastCenter = null;
    //         this.getParent().getChildElement(this).then(this._readyToEvent, this);
    //     },

    //     onRemoveFromMap: function (oldMap) {
    //         this._lastCenter = null;
    //         if (this._$content) {
    //             this._$content.remove();
    //             this._mapEventGroup.removeAll();
    //         }
    //         CustomControlClass.superclass.onRemoveFromMap.call(this, oldMap);
    //     },

    //     _readyToEvent: function (parentDomContainer) {
    //         // Создаем HTML-элемент с текстом.
    //         this._$content = $(['<div class="v-delivery-map--address"></div>',].join('')).appendTo(document.querySelector('#map_address'));
    //     },

    //     _addressSelected: function (address) {
    //         // Создаем HTML-элемент с текстом.
    //         this._$content.text(address);
    //     },

    // });

    LayoutPin = ymaps.templateLayoutFactory.createClass(
        '<div class="wrapper-icon-delivery">' +

        '{% if properties.loading  %}' +

        '<svg class="pin-icon pin-icon__loader" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">' +
        '<circle cx="12" cy="12" r="6" stroke-width="8" fill="none" stroke-dasharray="100" stroke-dashoffset="80"></circle>' +
        '<animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 0 0" to="360 0 0" dur="2s" repeatCount="indefinite"></animateTransform>' +
        '</svg>' +

        '{% else %}' +

        '<div class="icon-delivery__title {% if properties.error %}icon-delivery__title_error{% endif %}">' +
        '{% if properties.error %}' +
        '<span>{{ properties.error|default:"Адрес вне зоны доставки" }}</span> ' +
        '{% else %}' +
        '<span class="delivery-balloon__minutes">{{ properties.address }}</span>' +
        '<br>' +
        '<span class="delivery-balloon__text">Адрес магазина</span>' +
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

// ================================   MAP   ==========================================


// создаем карту при вводе адреса, при расчете маршрута и предоставим возможность выбора адреса по карте
function createMap(address = null) {
    console.log("createMap");
    ymaps.ready(function () {

        if (!map) {
            map = new ymaps.Map(mapdiv, {
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
                url: url_delivery_zones,
                dataType: 'json',
                success: function (json) {
                    ZonesInit(json);
                    if (address) {
                        ymaps.geocode(address, { results: 1, boundedBy: DELIVERYBOUNDS }).then(function (res) {
                            var coords = res.geoObjects.get(0).geometry.getCoordinates();
                            movePlacemark(coords, res.geoObjects.get(0).properties._data.name, true);
                            map.setCenter(coords, 14);
                            $(lon).val(coords[0]);
                            $(lat).val(coords[1]);
                        });
                    }
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
                        right: '16px',
                    },
                }
            });

            // Добавим элемент управления с собственной меткой геолокации на карте.
            var geolocationControl = new ymaps.control.GeolocationControl({
                options: {
                    layout: ymaps.templateLayoutFactory.createClass(
                        '<div id="geolocation" class="v-map-custom-controls--geolocation"><svg viewBox="0 0 26 26" fill="none"><path fill-rule="evenodd" clip-rule="evenodd" d="M19.925 1.78443C21.5328 1.18151 23.1029 2.75156 22.5 4.35933L16.0722 21.5C15.3574 23.4061 12.5838 23.1501 12.23 21.1453L10.8664 13.418L3.1391 12.0544C1.13427 11.7006 0.878261 8.92697 2.78443 8.21216L19.925 1.78443ZM20.6273 3.65708L3.48668 10.0848L11.2139 11.4485C12.0417 11.5945 12.6898 12.2426 12.8359 13.0704L14.1996 20.7977L20.6273 3.65708Z" fill="#007bff"/></svg></div>'
                    ),
                    position: {
                        bottom: offsetBtns + "px",
                        right: '16px'
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

            map.events.add('click', function (e) {
                movePlacemark(e.get('coords'));
            });

        } else if (address) {
            ymaps.geocode(address, { results: 1, boundedBy: DELIVERYBOUNDS }).then(function (res) {
                movePlacemark(res.geoObjects.get(0).geometry.getCoordinates(), res.geoObjects.get(0).properties._data.name);
            });
        }
    });
}

// переместить плейсмарк
function movePlacemark(coords, address = null, captured = false) {
    console.log("movePlacemark");
    if (placemark) {
        placemark.geometry.setCoordinates(coords);
    } else {
        placemark = new ymaps.Placemark(coords, {}, {
            hasBalloon: false,
            hasHint: false,
            draggable: true,

            iconLayout: 'default#imageWithContent',
            iconImageHref: "",
            iconImageSize: [25, 25],
            iconImageOffset: [-11, -11],
            iconContentLayout: LayoutPin,
        });
        map.geoObjects.add(placemark);
    }
    placemark.properties.set('loading', true);
    showBalloon(coords, address, captured);
}

// Определяем адрес по координатам (обратное геокодирование).
function showBalloon(coords, address = null, captured = false) {
    console.log("showBalloon");
    ymaps.geocode(coords, { results: 1, boundedBy: DELIVERYBOUNDS }).then(function (result) {
        console.log("balloonTime");
        var coords = result.geoObjects.get(0).geometry.getCoordinates();
        var address = result.geoObjects.get(0).properties._data.name;
        $(line1).val(result.geoObjects.get(0).properties._data.name);
        $(lon).val(coords[0]);
        $(lat).val(coords[1]);

        placemark.properties.set({
            'loading': false,
            'error': result.error,
            'address': address,
        });
    });
}

// создание зон доставки
function ZonesInit(json) {
    console.log("ZonesInit");

    // Добавляем зоны на карту.
    deliveryZones = ymaps.geoQuery(json).addToMap(map);
    // Задаём цвет и контент балунов полигонов.
    var color = ""
    deliveryZones.each(function (zona) {
        if (zona.properties.get('available')) {
            color = "#59ff85"
        } else {
            color = "#ed4543"
        }
        zona.options.set({
            fillColor: color,
            strokeColor: color,
            fillOpacity: 0.1,
            strokeWidth: 0,
            strokeOpacity: 0,
        });
        zona.options.set({ 'hasBalloon': false, 'hasHint': false });
        zona.events.add('click', function (e) {
            movePlacemark(e.get('coords'));
        });
    });
}

// кнопка очистить адрес
$(cleanAddress).on('click', function () {
    console.log("cleanAddress");
    $(line1).val('');
    $(lon).val('');
    $(lat).val('');

    if (map) {
        map.geoObjects.remove(placemark);
        map.setCenter(MAPCENTER, 12);
    }
    placemark = null;
})
