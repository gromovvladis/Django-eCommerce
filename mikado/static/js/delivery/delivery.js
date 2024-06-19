const deliveryBounds = [[56.087235, 92.667760], [55.999819, 93.040049]];
const mapCenter = [56.008331, 92.878786];
var del_time = 0;
var pick_time = 0; 

var address_line1 = document.querySelector('#id_line1');
var save_address_btn = $('#save_address');
var saveButton = $('#submit_address_on_map');
var deliveryControls = $('#delivery_map_controls');
var line1_hints = $('#line1_hints');
var suggest_container = document.querySelector('#suggest_container');


var shipping_method = $('#id_method_code');
var clean_address = $('#clean_address');
var open_map = $('#open_map');
var delivery_time = $('#delivery_time');
var mapContainer = document.querySelector('#map');
var checkoutMapContainer = document.querySelector('.checkout__map');

var map;
var placemark;
var geoObject;
var customControl;
var suggestView;
var cleanButton;
var cleanButtonHTML;
var deliveryZones;
var addressValid;

// подсказки при поиске запрос в Яндекс
ymaps.ready(function () {

    suggestView = new ymaps.SuggestView(address_line1, {
        boundedBy: [[56.120657, 92.640634], [55.946021, 93.258483]],
        strictBounds: true,
        container: suggest_container,
        width: suggest_container.offsetWidth,
        offset:[0, 5],
    });
    suggestView.events.add('select', function(e){suggestViewSelected(e)});

    // Пример реализации собственного элемента управления на основе наследования от collection.Item.
    // Элемент управления отображает название объекта, который находится в центре карты.
    // Создаем собственный класс.
    CustomControlClass = function (options) {
        CustomControlClass.superclass.constructor.call(this, options);
        this._$content = null;
        this._geocoderDeferred = null;
    };
    // И наследуем его от collection.Item.
    ymaps.util.augment(CustomControlClass, ymaps.collection.Item, {
        onAddToMap: function (map) {
            CustomControlClass.superclass.onAddToMap.call(this, map);
            this._lastCenter = null;
            this.getParent().getChildElement(this).then(this._readyToEvent, this);
        },

        onRemoveFromMap: function (oldMap) {
            this._lastCenter = null;
            if (this._$content) {
                this._$content.remove();
                this._mapEventGroup.removeAll();
            }
            CustomControlClass.superclass.onRemoveFromMap.call(this, oldMap);
        },

        _readyToEvent: function (parentDomContainer) {
            // Создаем HTML-элемент с текстом.
            this._$content = $(['<div class="v-delivery-map--address"></div>',].join('')).appendTo(document.querySelector('#delivery_map_address'));
        },

        _addressSelected: function (address) {
            // Создаем HTML-элемент с текстом.
            this._$content.text(address);
        },

    });

});

function suggestViewSelected(e){
    var selected=e.get('item').value;
    ymaps.geocode(selected,{
        results:1,
    }).then(function(res){
        var info=res.geoObjects.get(0);
        switch (info.properties.get('metaDataProperty.GeocoderMetaData.precision')) {
            case 'exact':
                hint = ''
                break;
            case 'number':
            case 'near':
            case 'range':
            case 'street':
                hint = 'Уточните номер дома';
                break;
            case 'other':
            default:
                hint = 'Уточните адрес';
        }

        if (hint) {
            $(line1_hints).html(hint);
            $(line1_hints).removeClass('d-none');
        } else {
            addressCaptured(info);
            customControl._addressSelected(info.getAddressLine());
        }
        
    });
}

// создаем карту при вводе адреса, при расчете маршрута и предоставим возможность выбора адреса по карте
function createMap(addressInfo=null) {
    ymaps.ready(function () {

        if (!map) {
            map = new ymaps.Map(mapContainer, {
                center: mapCenter,
                bounds: deliveryBounds,
                zoom: 12,
                controls: [],
            }, {suppressMapOpenBlock: true});

            //кнопки зума
            ZoomLayout = ymaps.templateLayoutFactory.createClass(
                '<div id="zoom-in" class="v-map-custom-controls--zoom-in"><svg viewBox="0 0 24 24" fill="none"><path d="M6 12H18M12 6V18" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>' +
                '<div id="zoom-out" class="v-map-custom-controls--zoom-out"><svg viewBox="0 0 24 24" fill="none"><path d="M6 12L18 12" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
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
                        right:'14px',
                    },
                }
            });

            // Добавим элемент управления с собственной меткой геолокации на карте.
            var geolocationControl = new ymaps.control.GeolocationControl({
                options: {
                    layout: ymaps.templateLayoutFactory.createClass(
                        '<div id="geolocation" class="v-map-custom-controls--geolocation"><svg viewBox="-1 -1 26 26" fill="none"><path fill-rule="evenodd" clip-rule="evenodd" d="M19.925 1.78443C21.5328 1.18151 23.1029 2.75156 22.5 4.35933L16.0722 21.5C15.3574 23.4061 12.5838 23.1501 12.23 21.1453L10.8664 13.418L3.1391 12.0544C1.13427 11.7006 0.878261 8.92697 2.78443 8.21216L19.925 1.78443ZM20.6273 3.65708L3.48668 10.0848L11.2139 11.4485C12.0417 11.5945 12.6898 12.2426 12.8359 13.0704L14.1996 20.7977L20.6273 3.65708Z" fill="#0F0F0F"/></svg></div>'
                    ),
                    position: {
                        bottom: '190px',
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


            if (mapContainer.getAttribute('data-full-screen')){

                closeButton = new ymaps.control.Button({     
                    options: {
                        // noPlacemark: true,
                        layout: ymaps.templateLayoutFactory.createClass(
                            '<button type="button" data-id="delivery-map-close-btn" class="v-button v-button--small justify-center shrink"><span class="v-button__wrapper"><span class="d-flex"><svg heigh="24px" width="24px" stroke="#000" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M15 7L10 12L15 17" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></span></span></button>'
                        ),
                        float: 'left',
                        position: {
                            top: '8px',
                            left: '14px'
                        }
                    }
                });


                map.controls.add(closeButton);

                closeButton.events.add('click', function () {
                    geoObject = null;
                    $(checkoutMapContainer).removeClass('open');
                    setTimeout(() => {
                        action_back = null;
                      }, 900);
                });
    

                cleanButton = new ymaps.control.Button({     
                    options: {
                        // noPlacemark: true,
                        layout: ymaps.templateLayoutFactory.createClass(
                            '<button type="button" data-id="delivery-map-clean-btn" class="v-button v-button--small justify-center shrink"><span class="v-button__wrapper"><span class="d-flex"><svg width="22" height="22" stroke="#b60808" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 7H20" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 10L7.70141 19.3578C7.87432 20.3088 8.70258 21 9.66915 21H14.3308C15.2974 21 16.1257 20.3087 16.2986 19.3578L18 10" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M9 5C9 3.89543 9.89543 3 11 3H13C14.1046 3 15 3.89543 15 5V7H9V5Z" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></span></span></button>'
                        ),
                        float: 'right',
                        position: {
                            top: '8px',
                            right: '14px'
                        }
                    },            
                });

                map.controls.add(cleanButton);
                cleanButton.events.add('click', function () {
                    cleanSelected();  
                });

                geolocationControl.options.set('position', {bottom: '265px', right: '10px'})
                zoomControl.options.set('position', {bottom: '320px', right: '10px'})
            }

            $(saveButton).on('click', function () {
                $(checkoutMapContainer).removeClass('open');
                if (geoObject){
                    $(address_line1).val(geoObject.getAddressLine());
                    addressCaptured(geoObject);
                    geoObject = null;
                }
            });

            if ($(address_line1).attr('captured')){
                $(deliveryControls).removeClass('d-none');
            }
            
            store = new ymaps.Placemark(
                [56.050918, 92.904378], {
                    iconCaption: "Mikado",
                },{
                    iconLayout: 'default#image',
                    // Своё изображение иконки метки.
                    iconImageHref: '/static/svg/map/pin-pickup.svg',
                    // Размеры метки.
                    iconImageSize: [40, 40],
                    // Смещение левого верхнего угла иконки относительно
                    // её "ножки" (точки привязки).
                    iconImageOffset: [-30, -30],
                    hasBalloon: false,
                });
            map.geoObjects.add(store);
            customControl = new CustomControlClass();
            map.controls.add(customControl, {
                float: 'none',
                position: {
                    bottom: 40,
                    left: 400,
                }
            });

            $.ajax({
                url: url_delivery_zones,
                dataType: 'json',
                success: function(json){
                    ZonesInit(json, addressInfo)
                }
            });

        } 
        // Если карта есть, то выставляем новый центр карты и меняем данные и позицию метки в соответствии с найденным адресом.
        if (addressInfo) {
            var coords;
            ymaps.geocode(addressInfo, {results: 1}).then(function (res) {
                coords = res.geoObjects.get(0).geometry.getCoordinates();
                if (placemark){
                    map.setCenter(coords, 14);
                    placemark.geometry.setCoordinates(coords);
                    placemark.properties.set({iconCaption: addressInfo, balloonContent: addressInfo});
                    customControl._addressSelected(addressInfo);
                } else {
                    placemark = new ymaps.Placemark(
                        coords, {
                            //iconContent: addressInfo,
                        }, {
                            //preset: 'islands#darkOrangeStretchyIcon'.charAt,
                            draggable: true,
                            hasBalloon: false,
                            hasHint: false,

                            iconLayout: 'default#imageWithContent',
                            iconImageHref: '/static/svg/map/pin-location.svg',
                            iconImageSize: [40, 40],
                            iconImageOffset: [-19, -39],
                            // iconContentOffset: [15, 15],
                        });
                    // Слушаем событие окончания перетаскивания на метке.
                    placemark.events.add('dragend', function () {
                        getAddress(placemark.geometry.getCoordinates());
                    });
                    map.geoObjects.add(placemark);
                }
                createPlacemark(coords);
            });
        }

        if ($(address_line1).attr('captured')){
            $(saveButton).attr('disabled', true);
        } else {
            $(deliveryControls).addClass('d-none');
            $(saveButton).attr('disabled', false);
        }
    
    });
}

// создание зон доставки
function ZonesInit(json, initAddress=null) {
    // Добавляем зоны на карту.
    deliveryZones = ymaps.geoQuery(json).addToMap(map);
    // Задаём цвет и контент балунов полигонов.
    deliveryZones.each(function (obj) {
        obj.options.set({
            fillColor: obj.properties.get('fill'),
            fillOpacity: obj.properties.get('fill-opacity'),
            strokeColor: obj.properties.get('stroke'),
            strokeWidth: obj.properties.get('stroke-width'),
            strokeOpacity: obj.properties.get('stroke-opacity')
        });
        obj.options.set({'hasBalloon': false, 'hasHint': false});
        
        
        obj.events.add('click', function (e) {
            var coords = e.get('coords');
            // Если метка уже создана – просто передвигаем ее.
            if (placemark) {
                placemark.geometry.setCoordinates(coords);
            }
            // Если нет – создаем.
            else {
                placemark = createPlacemark(coords);
                map.geoObjects.add(placemark);
                // Слушаем событие окончания перетаскивания на метке.
                placemark.events.add('dragend', function () {
                    getAddress(placemark.geometry.getCoordinates());
                    highlightResult(placemark);
                });
            }
            getAddress(coords); 
        });
    });

    if (initAddress){
        ymaps.geocode(initAddress, {results: 1}).then(function (res) {
            AjaxTime(res.geoObjects.get(0).geometry.getCoordinates(), true); 
        });
    }
}

// проверка адреса в зоне доставки
function AddressInZones(coords) {
    return deliveryZones.searchContaining(coords).get(0);
}

// создать плейсмарк
function createPlacemark(coords) {
    return new ymaps.Placemark(coords, {}, {
        draggable: true,
        hasBalloon: false,
        hasHint: false,

        iconLayout: 'default#imageWithContent',
        iconImageHref: '/static/svg/map/pin-location.svg',
        iconImageSize: [35, 35],
        iconImageOffset: [-17, -37],
    });
}

// Определяем адрес по координатам (обратное геокодирование).
function getAddress(coords) {
    ymaps.geocode(coords).then(function (res) {
        var firstGeoObject = res.geoObjects.get(0);
        placemark.properties
            .set({
                // Формируем строку с данными об объекте.
                iconCaption: [
                    // Название населенного пункта или вышестоящее административно-территориальное образование.
                    firstGeoObject.getLocalities().length ? firstGeoObject.getLocalities() : firstGeoObject.getAdministrativeAreas(),
                    // Получаем путь до топонима, если метод вернул null, запрашиваем наименование здания.
                    firstGeoObject.getThoroughfare() || firstGeoObject.getPremise()
                ].filter(Boolean).join(', '),
                // В качестве контента балуна задаем строку с адресом объекта.
                balloonContent: firstGeoObject.getAddressLine()
            });
        geoObject = firstGeoObject;
        customControl._addressSelected(geoObject.getAddressLine());
        $(deliveryControls).removeClass('d-none');
        if (geoObject.properties.get('metaDataProperty.GeocoderMetaData.precision') == "exact"){
            $(saveButton).attr('disabled', false);
        } else {
            $(saveButton).attr('disabled', true);
        }
    });
}

// адрес получен
function addressCaptured(info){
    $(deliveryControls).removeClass('d-none');
    $(address_line1).attr('readonly', true);
    $(address_line1).attr('captured', true);
    createMap(info.getAddressLine());
    AjaxTime(info.geometry.getCoordinates());
    $(address_line1).blur();
    if (suggestView){
        suggestView.destroy();
        suggestView = null;
    }
    $(saveButton).attr('disabled', true);
}

// выбор метода запроса в зависимости от 
function AjaxTime(coords=null, captured=false){
    if ($(shipping_method).val() == 'self-pick-up'){
        AjaxPickUpTime();
    } else {
        if ($(address_line1).attr('captured') == "true" || captured){
            if (AddressInZones(coords)) {
                $(line1_hints).html("");
                $(line1_hints).addClass('d-none');
                AjaxDeliveryTime(coords);
            } else {
                $(line1_hints).html('На данный адрес доставка недоступна');
                $(deliveryControls).addClass('d-none');
                $(line1_hints).removeClass('d-none');
                $(delivery_time).html("");
                $(delivery_time).removeClass('active');
                if (save_address_btn){
                    $(save_address_btn).attr("disabled", true);
                    $(save_address_btn).html("Укажите другой адрес");
                }
            }
        } else {
            $(delivery_time).html("");
            $(delivery_time).removeClass('active');
            if (save_address_btn){
                $(save_address_btn).attr("disabled", true);
                $(save_address_btn).html("Укажите адрес");
            }
        }
    } 
}

// запрос самовывоза на сервер
function AjaxPickUpTime() {
    $.ajax({
        data: {
            "order": 'data'
        }, 
        type: 'POST', 
        headers: { "X-CSRFToken": csrf_token },
        url: url_pickup,
        error: function (response) {
            console.log('error AjaxPickUpTime');
        },
        success: function (response) {
            console.log('success AjaxPickUpTime');
            pick_time = response.pickup_time;
            $(delivery_time).addClass('active');
            $(delivery_time).html("Самовывоз через " + pick_time + " мин.");
            if (save_address_btn){
                $(save_address_btn).attr("disabled", false);
                $(save_address_btn).html("Сохранить");
            }
        },
    });
}

// запрос времени доставки в яндекс и на сервер
function AjaxDeliveryTime(address) {
    $(line1_hints).html('');
    $(line1_hints).addClass('d-none');
    ymaps.ready(function () {
        ymaps.route([[56.050918, 92.904378], address]).then(function (route) {
            if (route){
                $.ajax({
                    data: {
                        "yandex_time": route.getJamsTime(),
                        "yandex_distant": route.getLength(),
                    }, 
                    type: 'POST', 
                    headers: { "X-CSRFToken": csrf_token },
                    url: url_delivery,
                    error: function (response) {
                        console.log('error AjaxDeliveryTime');
                        $(delivery_time).removeClass('active');
                    },
                    success: function (response) {
                        del_time = response.delivery_time;
                        console.log('success AjaxDeliveryTime');
                        $(delivery_time).addClass('active');
                        $(delivery_time).html("Доставим через " + del_time + " мин.");
                        if (save_address_btn){
                            $(save_address_btn).attr("disabled", false);
                            $(save_address_btn).html("Сохранить");
                        }
                    },
                });
            }
        }, function (error) {
            console.log('Возникла ошибка: ' + error.message);
        });   
    });
}

// очистить адрес
function cleanSelected(){
    del_time = 0;
    pick_time = 0;
    $(line1_hints).html("");
    $(line1_hints).addClass('d-none');
    $(delivery_time).html("");
    $(delivery_time).removeClass('active');
    if (save_address_btn){
        $(save_address_btn).attr("disabled", true);
        $(save_address_btn).html("Укажите адрес");
    }
    $(address_line1).val('');
    $(address_line1).attr('readonly', false);
    $(address_line1).attr('captured', false);
    if (map){
        map.geoObjects.remove(placemark);
        map.setBounds(deliveryBounds);
        map.setCenter(mapCenter, 12);
        customControl._addressSelected("");
    }
    placemark = null;
    $(deliveryControls).addClass('d-none');
    $(saveButton).attr('disabled', true);
    if (cleanButton){
        cleanButton.state.set({disabled:false});
    }
    if (!suggestView){
        suggestView = new ymaps.SuggestView(address_line1, {
            boundedBy: [[56.120657, 92.640634], [55.946021, 93.258483]],
            strictBounds: true,
            container: suggest_container,
            width: suggest_container.offsetWidth,
            offset:[0, 5],
        });
        suggestView.events.add('select', function(e){suggestViewSelected(e)});
    }
}

// кнопка очистить адрес
$(clean_address).on('click', function(){
    cleanSelected();
    $(address_line1).blur();
})

// кнопка открыть карту
$(open_map).on('click', function(){
    geoObject = null;
    createMap($(address_line1).val());
    $(checkoutMapContainer).addClass('open');
    $(address_line1).blur();
    action_back = function(){}
})

$(window).resize(function(){
    if (suggestView){
        suggestView.options.set('width', suggest_container.offsetWidth);
    }
});
