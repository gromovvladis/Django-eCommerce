var profileTabs = document.querySelectorAll('[data-id="profile-tab"]');

profileTabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
        var link = tab.getAttribute('data-link');
        if (link) {
            window.location.href = link;
        }
    });
});