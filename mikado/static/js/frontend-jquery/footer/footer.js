var footer_blocks = $('[data-id="footer-block"]');

$(footer_blocks).each(function(){
    var footer_block = $(this);
    var footer_title = $(footer_block).find('[data-id="footer-title"]');
    $(footer_title).on('click', function(){
        if (window.innerWidth < 768){
            $(footer_block).toggleClass('open');
        }
    })
})