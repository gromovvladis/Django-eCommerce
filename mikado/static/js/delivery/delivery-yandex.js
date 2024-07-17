var line1 = document.querySelector('#id_line1');
var lon = document.querySelector('#id_coords_long');
var lat = document.querySelector('#id_coords_lat');
var hints = $('#line1_hints');
var container = document.querySelector('#suggest_container');
var saveButton = $('#submit_address');
var deliveryControls = $('#delivery_map_controls');

var shipping_method = $('#id_method_code');
var clean_address = $('#clean_address');
var open_map = $('#open_map');
var delivery_time = $('#delivery_time');
var mapContainer = document.querySelector('#map');
var checkoutMapContainer = document.querySelector('.checkout__map');

const DELIVERYBOUNDS = [[56.120657, 92.640634], [55.946021, 93.258483]];
const MAPCENTER = [56.008331, 92.878786];
var suggestParams = {
    boundedBy: DELIVERYBOUNDS,
    strictBounds: true,
    container: container,
    width: container.offsetWidth,
    offset:[0, 5],
    results: 10,
    zIndex: 490,
    // provider: {
    //     suggest: (function (request, options) {
    //         return ymaps.suggest("Красноярск" + ", " + request)
    //     })
    // }
}

var validate = () => {};
var shippingCharge = () => {};
var map;
var placemark;
var addressInfo;
var customControl;
var suggestView;
var cleanButton;
var deliveryZones;
var LayoutPin
var shippingMethod = "zona-shipping";
var offsetBtns = 150;



// ====================  SUGGEST + LAYOUT + MAP CONTROLS  ===========================



// подсказки при поиске запрос в Яндекс
ymaps.ready(function () {
    
    if ($(line1).attr('captured')){
        suggestView = new ymaps.SuggestView(line1, suggestParams);
        suggestView.events.add('select', function(e){suggestViewSelected(e)});
    }

    CustomControlClass = function (options) {
        CustomControlClass.superclass.constructor.call(this, options);
        this._$content = null;
        this._geocoderDeferred = null;
    };
    
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
                        '<span class="delivery-balloon__minutes">{{ properties.order_minutes }}</span>' +
                        '<br>' +
                        '<span class="delivery-balloon__text"> Доставка<br> от&nbsp;{{ properties.min_order }}&nbsp;₽</span>' +
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

// подсказка выбрана
function suggestViewSelected(e){
    $(line1).val(e.get('item').displayName)
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
            $(hints).html(hint);
            $(hints).removeClass('d-none');
        } else  {
            var crd = info.geometry.getCoordinates();
            var adr = info.getAddressLine();
            addressCaptured(crd, adr);
            movePlacemark(crd, adr);
            map.setCenter(crd, 14);
        }
    });
}




// ====================  MAP  ===========================





// создаем карту при вводе адреса, при расчете маршрута и предоставим возможность выбора адреса по карте
function createMap(address=null) {
    console.log("createMap");
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
                url: url_delivery_zones,
                dataType: 'json',
                success: function(json){
                    ZonesInit(json);
                    if (address) {
                        ymaps.geocode(address, {results: 1}).then(function (res) {
                            var coords = res.geoObjects.get(0).geometry.getCoordinates();
                            movePlacemark(coords, res.geoObjects.get(0).getAddressLine());
                            map.setCenter(coords, 14);
                            $(long).val(coords[0]);
                            $(lat).val(coords[1]);
                        });
                    }
                }
            });

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
                    addressInfo = null;
                    map.geoObjects.remove(placemark);
                    placemark = null;
                    $(checkoutMapContainer).removeClass('open');
                    $(deliveryControls).addClass('d-none');
                    // map.destroy();
                    // map = null;
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
                    cleanAddress();  
                });

                offsetBtns = document.documentElement.clientHeight / 2 - 60;
            }
            
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
                    map.setZoom(map.getZoom() + 1, {checkZoomRange: true, duration: 200});
                },

                zoomOut: function () {
                    var map = this.getData().control.getMap();
                    map.setZoom(map.getZoom() - 1, {checkZoomRange: true, duration: 200});
                }

            });
            var zoomControl = new ymaps.control.ZoomControl({
                options: {
                    layout: ZoomLayout,
                    position: {
                        bottom: (offsetBtns + 55) + "px",
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

            var controlsPane = new ymaps.pane.StaticPane(map, {zIndex: 420});
            map.panes.append('customControls', controlsPane); 
            var placesPane = map.panes.get('controls').getElement();
            $(placesPane).addClass('v-map-custom-controls d-flex flex-column align-center justify-center');

            map.controls.add(zoomControl);
            map.controls.add(geolocationControl);

            $(saveButton).on('click', function () {
                $(checkoutMapContainer).removeClass('open');
                console.log(addressInfo)
                if (addressInfo){
                    $(line1).val(addressInfo.address);
                    addressCaptured(addressInfo.coords, addressInfo.address);
                    // validate();
                    addressInfo = null;
                }
            });

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

            map.events.add('click', function (e) {
                movePlacemark(e.get('coords'));
            });
        } else if (address) {
            ymaps.geocode(address, {results: 1}).then(function (res) {
                movePlacemark(res.geoObjects.get(0).geometry.getCoordinates(), res.geoObjects.get(0).getAddressLine());
            });
        }

        if ($(line1).attr('captured')){
            $(saveButton).attr('disabled', true);
        } else {
            $(deliveryControls).addClass('d-none');
            $(saveButton).attr('disabled', false);
        }
    });
}

// переместить плейсмарк
function movePlacemark(coords, address=null) {
    console.log("movePlacemark");
    if (placemark) {
        placemark.geometry.setCoordinates(coords);
    } else {
        placemark = new ymaps.Placemark(coords, {}, {
            hasBalloon: false,
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
    showBalloon(coords, address); 
}

// Определяем адрес по координатам (обратное геокодирование).
function showBalloon(coords, address=null) {
    console.log("showBalloon");
    var zonaId = getZonaId(coords)
    if (zonaId){
        console.log("in zona");
        GetTime({coords: coords, address: address, shippingMethod: "zona-shipping", zonaId:zonaId}).then(function(result) {
           
            if (address){
                timeCaptured(result);
            }

            placemark.properties.set({
                'loading': false,
                'error': result.error,
                'order_minutes': result.order_minutes,
                'min_order': result.min_order,
            });

            if (result.error){
                $(deliveryControls).addClass('d-none');
                $(saveButton).attr('disabled', true);
            } else {
                addressInfo = {"address": result.address, "coords": result.coords.split(",")};
                customControl._addressSelected(result.address);
                $(deliveryControls).removeClass('d-none');
                $(saveButton).attr('disabled', false);
            } 
        });
    } else {
        console.log("no in zona");

        addressInfo = null;
        $(deliveryControls).addClass('d-none');
        customControl._addressSelected("");
        $(saveButton).attr('disabled', true);
        // $(line1).attr('valid', false);

        placemark.properties.set({
            'error': "Адрес вне зоны доставки",
            'loading': false,
        });

        if (address){
            timeCaptured({"error": "Адрес вне зоны доставки"});
        }
    }
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
            strokeOpacity:0,
        });
        zona.options.set({'hasBalloon': false, 'hasHint': false});
        zona.events.add('click', function (e) {
            movePlacemark(e.get('coords'));
        });
    });
}



// ====================  ADDRESS RESOLVER  ===========================




// время можно показывать пользователю на странице и менять в ордер тайм
function timeCaptured(result){
    console.log("timeCaptured");
    
    if (result.error){
        $(hints).html(result.error);
        $(hints).removeClass('d-none');
        $(delivery_time).html('');
        $(delivery_time).removeClass('active');
        $(deliveryControls).addClass('d-none');
        $(line1).attr('valid', false);
        validate();
    } else {
        $(hints).html("");
        $(hints).addClass('d-none');
        $(delivery_time).addClass('active');
        $(delivery_time).html(result.delivery_time_text);
        $(line1).attr('valid', true);
        shippingCharge(result.zonaId);
    }
    
    
}

// запрос времени доставки на сервере 
function GetTime({coords, address, shippingMethod, zonaId} = {}){
    console.log('GetTime')

    var roteTime;
    
    if (Array.isArray(coords)){
        coords = coords.join(",")
    }

    var rote_crt;
    if (coords){
        rote_crt = coords;
    } else {
        rote_crt = address;
    }

    return ymaps.route([[56.050918, 92.904378], rote_crt]).then(function (route) {
        roteTime = route.getJamsTime();
        console.log(roteTime);
        return $.ajax({
            data: {
                "coords": coords,
                "address": address,
                "shipping_method": shippingMethod,
                "zonaId": zonaId,
                "roteTime": roteTime,
            }, 
            type: 'POST', 
            headers: { "X-CSRFToken": csrf_token },
            url: url_time,
            error: function (response) {
                console.log('error GetTime');
                $(delivery_time).removeClass('active');
            },
            success: function (response) {
                var deferred = $.Deferred();
                switch (response.status) {
                    case 200:
                        deferred.resolve(response);
                        break;
                    default:
                        deferred.reject();
                        break;
                }
                console.log('GetTime success')
                return deferred.promise();
            },
        }); 
    });

}

// проверка адреса в зоне доставки
function getZonaId(coords) {
    console.log("getZonaId");
    var zona = deliveryZones.searchContaining(coords).get(0);
    if (!zona) {
        return 0;
    }
    return zona.properties._data.number;
}

// адрес получен
function addressCaptured(coords, address){
    console.log("addressCaptured");

    if (suggestView){
        suggestView.destroy();
        suggestView = null;
    }

    $(line1).attr('readonly', true);


    GetTime({coords: coords, address: address, shippingMethod: shippingMethod, zonaId:getZonaId(coords)}).then(function(result) {
        timeCaptured(result);
    });

    // $(deliveryControls).addClass('d-none');
    $(saveButton).attr('disabled', true);
    $(line1).attr('captured', true);
    $(long).val(coords[0]);
    $(lat).val(coords[1]);

}



// ====================  HELPERS  ===========================




// очистить адрес
function cleanAddress(){
    console.log("cleanAddress");
    $(line1).val('');
    $(line1).attr('readonly', false);
    $(hints).addClass('d-none');
    $(delivery_time).removeClass('active');
    $(deliveryControls).addClass('d-none');
    $(saveButton).attr('disabled', true);

    if (!suggestView){
        suggestView = new ymaps.SuggestView(line1, suggestParams);
        suggestView.events.add('select', function(e){suggestViewSelected(e)});
    }

    if (map){
        map.geoObjects.remove(placemark);
        map.setCenter(MAPCENTER, 12);
        customControl._addressSelected("");
    }

    if (cleanButton){
        cleanButton.state.set({disabled:false});
    }

    $(hints).html("");
    $(delivery_time).html("");
    $(line1).attr('captured', false);
    $(line1).attr('valid', false);
    $(long).val('');
    $(lat).val('');
    placemark = null;
    shippingCharge();
}

// кнопка очистить адрес
$(clean_address).on('click', function(){
    cleanAddress();
    validate();
})

// кнопка открыть карту
$(open_map).on('click', function(){
    console.log("map open");
    addressInfo = null;
    createMap($(line1).val());
    $(checkoutMapContainer).addClass('open');
    action_back = function(){};
})

// изменение ширины seggestview
$(window).resize(function(){
    if (suggestView){
        suggestView.options.set('width', container.offsetWidth);
    }
});

