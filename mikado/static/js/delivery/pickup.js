var mapContainer = document.querySelector('#pickup_map');
const MAPCENTER = [56.04933, 92.90671];
var map;

$(document).ready(function () {
    if (window.ymaps && mapContainer) {
        createPickupMap();
    }
});

function createPickupMap() {
    ymaps.ready(function () {

        if (!map) {
            map = new ymaps.Map(mapContainer, {
                center: MAPCENTER,
                zoom: 14,
                controls: [],
            }, {suppressMapOpenBlock: true});

            //кнопки зума
            ZoomLayout = ymaps.templateLayoutFactory.createClass(
                '<div id="zoom-in" class="v-map-custom-controls--zoom-in"><svg viewBox="0 0 24 24" fill="none"><path d="M6 12H18M12 6V18" stroke="#0a834f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>' +
                '<div id="zoom-out" class="v-map-custom-controls--zoom-out"><svg viewBox="0 0 24 24" fill="none"><path d="M6 12L18 12" stroke="#0a834f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
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
                    map.setZoom(map.getZoom() + 1, {checkZoomRange: true});
                },

                zoomOut: function () {
                    var map = this.getData().control.getMap();
                    map.setZoom(map.getZoom() - 1, {checkZoomRange: true});
                }

            });
            var zoomControl = new ymaps.control.ZoomControl({
                options: {
                    layout: ZoomLayout,
                    position: {
                        bottom: "245px",
                        right:'10px',
                    },
                }
            });

            // Добавим элемент управления с собственной меткой геолокации на карте.
            var geolocationControl = new ymaps.control.GeolocationControl({
                options: {
                    layout: ymaps.templateLayoutFactory.createClass(
                        '<div id="geolocation" class="v-map-custom-controls--geolocation"><svg viewBox="0 0 26 26" fill="none"><path fill-rule="evenodd" clip-rule="evenodd" d="M19.925 1.78443C21.5328 1.18151 23.1029 2.75156 22.5 4.35933L16.0722 21.5C15.3574 23.4061 12.5838 23.1501 12.23 21.1453L10.8664 13.418L3.1391 12.0544C1.13427 11.7006 0.878261 8.92697 2.78443 8.21216L19.925 1.78443ZM20.6273 3.65708L3.48668 10.0848L11.2139 11.4485C12.0417 11.5945 12.6898 12.2426 12.8359 13.0704L14.1996 20.7977L20.6273 3.65708Z" fill="#0a834f"/></svg></div>'
                    ),
                    position: {
                        bottom: '190px',
                        right: '10px'
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
                    map.setZoom(15);
                    map.panTo(result.geoObjects.position);
                });
            });

            var controlsPane = new ymaps.pane.StaticPane(map, { zIndex: 420});
            map.panes.append('customControls', controlsPane); 
            var placesPane = map.panes.get('controls').getElement();
            $(placesPane).addClass('v-map-custom-controls d-flex flex-column align-center justify-center');

            map.controls.add(zoomControl);
            map.controls.add(geolocationControl);


            store = new ymaps.Placemark(
                [56.050918, 92.904378], {
                    iconCaption: "Mikado",
                },{
                    iconLayout: 'default#imageWithContent',
                    iconImageHref: '/static/svg/map/pin-pickup.svg',

                    iconImageSize: [40, 40],
                    iconImageOffset: [-30, -30],

                    hasBalloon: false,
                    hasHint: false,
                });
            map.geoObjects.add(store);

        } 
    });
}
