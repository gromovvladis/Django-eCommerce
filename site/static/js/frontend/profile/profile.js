var profileWrapper = document.querySelector('[data-id="profile-wrapper"]');

if (profileWrapper) {
    var profileTabs = document.querySelectorAll('[data-id="profile-tab"]');
    profileTabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
            if (!tab.classList.contains('active')) {
                window.location.href = tab.getAttribute('data-link');
            } else {
                if (profileWrapper) {
                    profileWrapper.classList.add('open');
                    actionBack = function () {
                        profileWrapper.classList.remove('open');
                        window.scrollTo(0, 0);
                    };
                }
            }
        });
    });

    if (profileWrapper && profileWrapper.classList.contains('open')) {
        actionBack = function () {
            profileWrapper.classList.remove('open');
            window.scrollTo(0, 0);
        };
    }
}