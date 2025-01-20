function toggle_table(toggle_row){
  if ($(toggle_row).length > 0) {
    $(toggle_row).each(function(){
      var row = $(this)
      var btn = $(row).find(".btn");
      var tr = $(row).parent();
      $(btn).click(function() {
        $(tr).toggleClass('mobile-open');
        $(row).toggleClass('mobile-open');
      });
    })
  }
}

toggle_table($(".toggle-row"));