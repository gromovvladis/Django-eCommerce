var we_use_cookie = $('#we_use_cookie');
var action_back = null;

$(document).ready(function () {
  var cookieAgree = Cookies.get('cookieAgree');
  if (!cookieAgree) {
    $.ajax({
      data: $(this).serialize(), 
      type: 'GET', 
      url: url_get_cookie,
      success: function (response) {
          $(we_use_cookie).html(response.cookies);
        },
    });
  }
});

function agree_cookie(){
  Cookies.set('cookieAgree', true, {expires: 1000});
  $(we_use_cookie).empty();
}

function getBack(){
  if (action_back) {
    action_back();
    action_back = null;
  } else {
    history.back();   
  }
}