$('[data-id="profile-tab"]').each(function(){
    $(this).on('click', function(){
        window.location.href = $(this).attr('data-link');
    });
})