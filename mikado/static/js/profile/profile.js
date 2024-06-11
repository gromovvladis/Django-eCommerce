var profile_wrapper = $('[data-id="profile-wrapper"]');

$('[data-id="profile-tab"]').each(function(){
    $(this).on('click', function(){ 
        if (!$(this).hasClass('active')){
            window.location.href = $(this).attr('data-link');
        } else {
            $(profile_wrapper).addClass('open');
            action_back = function(){$(profile_wrapper).removeClass('open');window.scrollTo(0, 0)}
        }
    });
})

if ($(profile_wrapper).hasClass('open')){
    action_back = function(){$(profile_wrapper).removeClass('open');window.scrollTo(0, 0)}
}