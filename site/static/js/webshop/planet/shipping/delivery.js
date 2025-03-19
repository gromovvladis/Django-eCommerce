var line1Container = document.getElementById('line1_container');
var shippingTime = document.getElementById('shipping_time');

if (line1Container) {
    var line1 = line1Container.querySelector('#id_line1');
    var suggests = line1Container.querySelector('#suggest_list');
    var cleanBtn = line1Container.querySelector('#clean_address');
    var open_map = line1Container.querySelector('#open_map');

    var mapContainer = document.querySelector('.shipping__map');
    var mapDiv = mapContainer.querySelector('#map');
    var controls = mapContainer.querySelector('#map_controls');
    var saveButton = mapContainer.querySelector('#submit_address');

    var lon = document.getElementById('id_coords_long');
    var lat = document.getElementById('id_coords_lat');

    var hints = document.getElementById('line1_hints');

    const MAPCENTER = [56.0435, 92.9075];
    const DELIVERYBOUNDS = [[56.043545, 92.6406], [55.9460, 93.2584]];

    var validate = () => { };
    var shippingCharge = () => { };
    var map;
    var placemark;
    var addressInfo;
    var mapControl;
    var cleanButton;
    var shippingZones;
    var LayoutPin
    var shippingMethod = "zona-shipping";
    var offsetBtns = 150;

    var selection = -1;
    var li_list = [];


    // ====================  SUGGEST + LAYOUT + MAP CONTROLS  ===========================


    // подсказки при поиске 2GIS
    document.addEventListener('DOMContentLoaded', function () {
        if (line1) { // проверяем, что элемент существует
            CreateSuggestView();
        }
    });

    // строка с адресом на карте Яндекс и layout
    ymaps.ready(function () {

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
                this._$content = document.querySelector('#map_address')?.appendChild(Object.assign(document.createElement('div'), { className: 'shipping-map--address' }));
            },

            _addressSelected: function (address) {
                // Создаем HTML-элемент с текстом.
                this._$content.textContent = address;
            },

        });

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
            '<span>{{ properties.error|default:"Адрес вне зоны доставки" }}</span> ' +
            '{% else %}' +
            '<span class="shipping-balloon__minutes">{{ properties.order_minutes }}</span>' +
            '<br>' +
            '<span class="shipping-balloon__text"> Доставка<br> от&nbsp;{{ properties.min_order }}&nbsp;₽</span>' +
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

    // Создание suggestView
    function CreateSuggestView() {

        line1.addEventListener('focus', function () {
            suggests.classList.remove('d-none');
        });

        document.addEventListener('mousedown', function (event) {
            if (!line1Container.contains(event.target)) {
                suggests.classList.add('d-none');
                if (selection > -1) {
                    suggests[0].children[selection].classList.remove('hover');
                }
                selection = -1;
            }
        }, false);

        line1.addEventListener('input', function () {
            getSuggestList(this.value);
        });


        // Клик по подсказке
        line1.addEventListener('keydown', function (event) {

            if (event.keyCode === 38) {
                event.preventDefault();
                if (selection > 0) {
                    suggests[0].children[selection].classList.remove('hover');
                    selection--;
                    suggests[0].children[selection].classList.add('hover');
                    scrollToElement(selection, false);
                }
            } else if (event.keyCode === 40) {
                event.preventDefault();
                if (selection < suggests[0].children.length - 1) {
                    if (selection >= 0) {
                        suggests[0].children[selection].classList.remove('hover');
                    }
                    selection++;
                    suggests[0].children[selection].classList.add('hover');
                    scrollToElement(selection, true);
                }
            } else if (event.key === 'Enter' && li_list.length > 0) {
                suggestViewSelected(li_list[selection]);
                selection = 0;
            }
        });

    }

    // сдвиг скролла вниз или вверх при выборе подсказки
    function scrollToElement(element, down) {
        const itemHeight = suggests.children[0].offsetHeight;

        if (element > 4 && down) {
            suggests.scrollTop = suggests.scrollTop + itemHeight;

        } else if (element < 5 && !down) {
            suggests.scrollTop = suggests.scrollTop - itemHeight;

        }
    }

    // выдача списка подсказок
    function getSuggestList(query) {
        if (query.length > 1) {
            fetch('https://catalog.api.2gis.com/3.0/suggests?' + new URLSearchParams({
                q: query,
                sort_point: "92.878786,56.008331",
                polygon: "POLYGON((92.6446 56.1015,92.991165 56.139197,93.1521 55.9991,92.7032 55.9417,92.6446 56.1015))",
                type: "building,street",
                suggest_type: "address",
                fields: "items.point",
                key: '6013c28d-62ae-4764-a509-f403d2ee92c6'
            }), {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    suggests.innerHTML = '';
                    let li_list = [];
                    let selection = -1;
                    if (data.result) {
                        const suggestions = data.result.items;
                        suggestions.forEach(suggestion => {
                            const li = document.createElement('li');
                            li.className = 'search__suggest-item';
                            li.textContent = suggestion.address_name || suggestion.name;

                            li.addEventListener('click', () => {
                                suggestViewSelected(suggestion);
                            });

                            li.addEventListener('mouseover', () => {
                                if (selection >= 0) {
                                    suggests.children[selection].classList.remove('hover');
                                }
                                selection = -1;
                            });

                            suggests.appendChild(li);
                            li_list.push(suggestion);
                        });
                    } else {
                        const li = document.createElement('li');
                        li.className = 'search__suggest-item';
                        li.textContent = 'Адрес не найден';
                        suggests.appendChild(li);
                    }
                })
                .catch(error => {
                    console.error('Error fetching suggestions:', error);
                });
        } else {
            suggests.innerHTML = '';
        }
    }

    // подсказка выбрана
    function suggestViewSelected(suggestion) {
        var hint;
        switch (suggestion.type) {
            case 'building':
            case 'branch':
                hint = ''
                break;
            case 'street':
                hint = 'Уточните номер дома';
                break;
            default:
                hint = 'Уточните адрес';
        }

        var address;
        if (suggestion.address_name) {
            address = suggestion.address_name;
        } else {
            address = suggestion.name;
        }

        if (hint) {
            hints.innerHTML = hint;
            hints.classList.remove('d-none');
            line1.value = address + " ";
            getSuggestList(address);
        } else {
            line1.value = address;
            var coords = [suggestion.point['lat'], suggestion.point['lon']];
            suggests.innerHTML = '';
            addressCaptured(coords, address);
            movePlacemark(coords, address, true);
            map.setCenter(coords, 14);
        }
    }


    // ================================   MAP   ==========================================


    // создаем карту при вводе адреса, при расчете маршрута и предоставим возможность выбора адреса по карте
    function createMap(address = null) {
        ymaps.ready(function () {

            if (!map) {
                map = new ymaps.Map(mapDiv, {
                    center: MAPCENTER,
                    zoom: 12,
                    controls: [],
                }, {
                    yandexMapDisablePoiInteractivity: true,
                    suppressMapOpenBlock: true,
                    maxZoom: 18,
                    minZoom: 10,
                });

                fetch(url_shipping_zones)
                    .then(response => response.json())
                    .then(json => {
                        ZonesInit(json);
                        if (address) {
                            ymaps.geocode(address, { results: 1, boundedBy: DELIVERYBOUNDS })
                                .then(res => {
                                    var coords = res.geoObjects.get(0).geometry.getCoordinates();
                                    movePlacemark(coords, res.geoObjects.get(0).properties._data.name, true);
                                    map.setCenter(coords, 14);
                                    document.querySelector(lon).value = coords[0];
                                    document.querySelector(lat).value = coords[1];
                                });
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching shipping zones:', error);
                    });


                if (mapDiv.getAttribute('data-full-screen')) {

                    closeButton = new ymaps.control.Button({
                        options: {
                            // noPlacemark: true,
                            layout: ymaps.templateLayoutFactory.createClass(
                                '<button type="button" data-id="shipping-map-close-btn" class="button button--small justify-center shrink"><span class="button__wrapper"><span class="d-flex"><svg heigh="24px" width="24px" stroke="#000" viewBox="1 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M15 7L10 12L15 17" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></span></span></button>'
                            ),
                            float: 'left',
                            position: {
                                top: '10px',
                                left: '16px'
                            }
                        }
                    });

                    map.controls.add(closeButton);

                    closeButton.events.add('click', function (event) {


                        mapContainer.classList.remove('open');
                        map.geoObjects.remove(placemark);
                        controls.classList.add('d-none');

                        addressInfo = null;
                        placemark = null;


                        event.preventDefault();
                        event.stopPropagation();

                        setTimeout(() => {
                            actionBack = null;
                        }, 700);
                    });

                    cleanButton = new ymaps.control.Button({
                        options: {
                            // noPlacemark: true,
                            layout: ymaps.templateLayoutFactory.createClass(
                                '<button type="button" data-id="shipping-map-clean-btn" class="button button--small justify-center shrink"><span class="button__wrapper"><span class="d-flex"><svg width="20" height="20" stroke="#b60808" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 7H20" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 10L7.70141 19.3578C7.87432 20.3088 8.70258 21 9.66915 21H14.3308C15.2974 21 16.1257 20.3087 16.2986 19.3578L18 10" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M9 5C9 3.89543 9.89543 3 11 3H13C14.1046 3 15 3.89543 15 5V7H9V5Z" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></span></span></button>'
                            ),
                            float: 'right',
                            position: {
                                top: '10px',
                                right: '16px'
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
                    '<div id="zoom-in" class="map-custom-controls--zoom-in"><svg viewBox="0 0 24 24" fill="none"><path d="M6 12H18M12 6V18" stroke="#0a834f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>' +
                    '<div id="zoom-out" class="map-custom-controls--zoom-out"><svg viewBox="0 0 24 24" fill="none"><path d="M6 12L18 12" stroke="#0a834f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
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
                            document.querySelector('#zoom-in').addEventListener('click', this.zoomInCallback);
                            document.querySelector('#zoom-out').addEventListener('click', this.zoomOutCallback);
                        },

                        clear: function () {
                            // Снимаем обработчики кликов.
                            document.querySelector('#zoom-in').removeEventListener('click', this.zoomInCallback);
                            document.querySelector('#zoom-out').removeEventListener('click', this.zoomOutCallback);

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
                            '<div id="geolocation" class="map-custom-controls--geolocation"><svg viewBox="0 0 26 26" fill="none"><path fill-rule="evenodd" clip-rule="evenodd" d="M19.925 1.78443C21.5328 1.18151 23.1029 2.75156 22.5 4.35933L16.0722 21.5C15.3574 23.4061 12.5838 23.1501 12.23 21.1453L10.8664 13.418L3.1391 12.0544C1.13427 11.7006 0.878261 8.92697 2.78443 8.21216L19.925 1.78443ZM20.6273 3.65708L3.48668 10.0848L11.2139 11.4485C12.0417 11.5945 12.6898 12.2426 12.8359 13.0704L14.1996 20.7977L20.6273 3.65708Z" fill="#0a834f"/></svg></div>'
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
                placesPane.classList.add('map-custom-controls', 'd-flex', 'flex-column', 'align-center', 'justify-center');

                map.controls.add(zoomControl);
                map.controls.add(geolocationControl);

                saveButton.addEventListener('click', function () {
                    mapContainer.classList.remove('open');
                    if (addressInfo) {
                        line1.value = addressInfo.address;
                        addressCaptured(addressInfo.coords, addressInfo.address);
                        addressInfo = null;
                    }
                });

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
                mapControl = new CustomControlClass();
                map.controls.add(mapControl, {
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
                ymaps.geocode(address, { results: 1, boundedBy: DELIVERYBOUNDS }).then(function (res) {
                    movePlacemark(res.geoObjects.get(0).geometry.getCoordinates(), res.geoObjects.get(0).properties._data.name);
                });
            }

            if (line1.hasAttribute('captured')) {
                saveButton.disabled = true;
            } else {
                controls.classList.add('d-none');
                saveButton.disabled = false;
            }

        });
    }

    // переместить плейсмарк
    function movePlacemark(coords, address = null, captured = false) {
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
        showBalloon(coords, address, captured);
    }

    // Определяем адрес по координатам (обратное геокодирование).
    function showBalloon(coords, address = null, captured = false) {
        var zonaId = getZonaId(coords)
        if (zonaId) {
            if (!address) {
                ymaps.geocode(coords, { results: 1, kind: 'house' }).then(function (res) {
                    address = res.geoObjects.get(0).properties._data.name;
                    balloonTime(coords, address, zonaId, captured);
                });
            } else {
                balloonTime(coords, address, zonaId, captured);
            }

        } else {
            addressInfo = null;
            controls.classList.add('d-none');
            mapControl._addressSelected("");
            saveButton.disabled = true;

            placemark.properties.set({
                'error': "Адрес вне зоны доставки",
                'loading': false,
            });

            if (captured) {
                timeCaptured({ "error": "Адрес вне зоны доставки" });
            }
        }
    }

    // показ балуна и захват или нет времени
    function balloonTime(coords, address, zonaId, captured) {
        GetTime({ coords: coords, address: address, shippingMethod: "zona-shipping", zonaId: zonaId }).then(function (result) {
            if (captured) {
                timeCaptured(result);
            }
            placemark.properties.set({
                'loading': false,
                'error': result.error,
                'order_minutes': result.order_minutes,
                'min_order': result.min_order,
            });

            if (result.error) {
                controls.classList.add('d-none');
                saveButton.disabled = true;
            } else {
                addressInfo = { "address": result.address, "coords": result.coords.split(",") };
                mapControl._addressSelected(result.address);
                controls.classList.remove('d-none');
                saveButton.disabled = false;
            }
        });
    }

    // создание зон доставки
    function ZonesInit(json) {
        // Добавляем зоны на карту.
        shippingZones = ymaps.geoQuery(json).addToMap(map);
        // Задаём цвет и контент балунов полигонов.
        var color = ""
        shippingZones.each(function (zona) {
            if (zona.properties.get('available')) {
                color = "#59ff85";
            } else {
                color = "#ed4543";
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


    // ====================  ADDRESS RESOLVER  ===========================


    // проверка адреса в зоне доставки
    function getZonaId(coords) {
        var zona = shippingZones.searchContaining(coords).get(0);
        if (!zona) {
            return 0;
        }
        return zona.properties._data.number;
    }

    // адрес получен
    function addressCaptured(coords, address) {
        line1.readOnly = true;
        suggests.classList.add('d-none');
        line1Container.classList.remove('not-valid');

        GetTime({ coords: coords, address: address, shippingMethod: shippingMethod, zonaId: getZonaId(coords) }).then(function (result) {
            timeCaptured(result);
        });

        saveButton.disabled = true;
        line1.setAttribute('captured', true);
        lon.value = coords[0];
        lat.value = coords[1];

    }


    // ====================  HELPERS  ===========================


    // очистить адрес
    function cleanAddress() {
        line1.value = '';
        line1.readOnly = false;
        hints.classList.add('d-none');
        if (shippingTime) {
            shippingTime.classList.remove('active');
        }
        controls.classList.add('d-none');
        saveButton.disabled = true;
        suggests.classList.add('d-none');

        if (map) {
            map.geoObjects.remove(placemark);
            map.setCenter(MAPCENTER, 12);
            mapControl._addressSelected("");
        }

        if (cleanButton) {
            cleanButton.state.set({ disabled: false });
        }

        hints.innerHTML = "";
        if (shippingTime) {
            shippingTime.innerHTML = "";
        }
        line1.setAttribute('captured', 'false');
        line1.setAttribute('valid', 'false');
        lon.value = '';
        lat.value = '';
        placemark = null;
        shippingCharge();
    }

    // кнопка очистить адрес
    cleanBtn.addEventListener('click', function () {
        cleanAddress();
        validate();
    });

    // кнопка открыть карту
    if (open_map) {
        open_map.addEventListener('click', function () {
            addressInfo = null;
            createMap(line1.value);
            mapContainer.classList.add('open');
            actionBack = function () { };
        });
    }
}

// запрос времени доставки на сервере со временем
function GetTime({ coords = '', address = '', shippingMethod = '', zonaId = '' } = {}) {
    if (Array.isArray(coords)) {
        coords = coords.join(",")
    }
    return fetch(url_time, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token
        },
        body: new URLSearchParams({
            "coords": coords,
            "address": address,
            "shipping_method": shippingMethod,
            "zonaId": zonaId,
        }).toString()
    })
        .then(response => response.json())
        .then(response => {
            return new Promise((resolve, reject) => {
                resolve(response);
            });
        })
        .catch(error => {
            console.error('error GetTime', error);
            if (shippingTime) {
                shippingTime.classList.remove('active');
            }
        });
}

// время можно показывать пользователю на странице и менять в ордер тайм
function timeCaptured(result) {
    if (result.error) {
        if (hints) {
            hints.innerHTML = result.error;
            hints.classList.remove('d-none');
        }
        if (shippingTime) {
            shippingTime.innerHTML = '';
            shippingTime.classList.remove('active');
            shippingTime.classList.add('hidden');
        }
        if (line1) {
            line1.setAttribute('valid', 'false');
        }
        controls.classList.add('d-none');
        validate();
    } else {
        if (hints) {
            hints.innerHTML = "";
            hints.classList.add('d-none');
        }
        if (shippingTime) {
            shippingTime.classList.add('active');
            shippingTime.classList.remove('hidden');
            shippingTime.innerHTML = result.shipping_time_text;
        }
        if (line1) {
            line1.setAttribute('valid', 'true');
            shippingCharge(result.zonaId);
        }
    }
}