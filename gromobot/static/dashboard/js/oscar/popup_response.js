(function () {
    'use strict';
    var initData = JSON.parse(document.getElementById('popup-response-constants').dataset.popupResponse);
    switch (initData.action) {
        case 'change':
            window.opener.dashboard.dismissChangeRelatedObjectPopup(window, initData.value, initData.obj, initData.new_value);
            break;
        case 'delete':
            window.opener.dashboard.dismissDeleteRelatedObjectPopup(window, initData.value);
            break;
        default:
            window.opener.dashboard.dismissAddRelatedObjectPopup(window, initData.value, initData.obj);
            break;
    }
})();
