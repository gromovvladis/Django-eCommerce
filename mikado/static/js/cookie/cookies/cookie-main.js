$(document).ready(function () {
  cookieAgree = Cookies.get('cookieAgree');
  we_use_cookie = $('#we_use_cookie');
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

function main_cookie(){
  Cookies.set('cookieAgree', true, {expires: 1000});
  $(we_use_cookie).empty();
}

var action_back = null

function getBack(){
  if (action_back) {
    action_back();
    action_back = null;
  } else {
    history.back();   
  }
}