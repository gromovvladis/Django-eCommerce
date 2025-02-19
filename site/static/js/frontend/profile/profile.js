var profileWrapper = document.querySelector('[data-id="profile-wrapper"]');

if (profileWrapper) {
    var profileTabs = document.querySelectorAll('[data-id="profile-tab"]');
    var isProfileLink = document.getElementById('app').classList.contains('app---profile-link');
    console.log(isProfileLink)
    profileTabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
            if (!tab.classList.contains('active') || isProfileLink) {
                window.location.href = tab.getAttribute('data-link');
            } else {
                profileWrapper.classList.add('open');
                actionBack = function () {
                    profileWrapper.classList.remove('open');
                    window.scrollTo(0, 0);
                };
            }
        });
    });

    if (profileWrapper.classList.contains('open') && !isProfileLink) {
        actionBack = function () {
            profileWrapper.classList.remove('open');
            window.scrollTo(0, 0);
        };
    }
}