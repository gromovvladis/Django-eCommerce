var profileForm = document.querySelector('#profile_form');
var profileFields = profileForm.querySelectorAll('[data-id="input-wrapper"]');

profileFields.forEach(function (wrapper) {
    var inputField = wrapper.querySelector('[data-id="profile-input"]');

    if (inputField.value !== "") {
        wrapper.classList.add('v-input__label-active');
    }

    inputField.addEventListener('focusin', function () {
        wrapper.classList.add('v-input__label-active');
    });

    inputField.addEventListener('focusout', function () {
        if (inputField.value === "") {
            wrapper.classList.remove('v-input__label-active');
        }
    });
});

profileForm.addEventListener('submit', function (event) {
    event.preventDefault();

    var profileBtn = profileForm.querySelector('button');
    var profileMsg = profileForm.querySelector('[data-id="profile-message"]');

    profileBtn.disabled = true;
    profileBtn.textContent = 'Сохранение';
    profileMsg.textContent = '';

    var formData = new FormData(profileForm);
    var data = new URLSearchParams(formData).toString();

    fetch(profileForm.getAttribute('action'), {
        method: profileForm.getAttribute('method'),
        body: data,
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => response.json())
    .then(responseData => {
        profileMsg.textContent = responseData.message;
        profileBtn.textContent = 'Сохранить настройки';
        profileBtn.disabled = false;
    })
    .catch(error => {
        console.error('Error:', error);
        profileBtn.textContent = 'Сохранить настройки';
        profileBtn.disabled = false;
    });
});