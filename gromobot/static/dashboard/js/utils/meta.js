document.addEventListener('DOMContentLoaded', function () {
    var seoTab = document.getElementById('seo');
    if (seoTab) {
        function setupCharCount(inputId, maxChars) {
            var inputField = seoTab.querySelector('#' + inputId);
            var inputLabel = seoTab.querySelector('label[for="' + inputId + '"]');
            if (inputField && inputLabel) {
                var charCountDiv = document.createElement('span');
                charCountDiv.style.marginLeft = '.5rem';
                charCountDiv.style.fontSize = '.8rem';
                inputLabel.parentNode.insertBefore(charCountDiv, inputLabel.nextSibling);
                function updateCharCount() {
                    var charCount = inputField.value.length;
                    charCountDiv.textContent = `${charCount} / ${maxChars}`;
                    if (charCount > maxChars) {
                        inputField.classList.add('border-danger');
                    } else {
                        inputField.classList.remove('border-danger');
                    }
                }
                inputField.addEventListener('input', updateCharCount);
                updateCharCount();
            }
        }
        setupCharCount('id_meta_title', 60);
        setupCharCount('id_meta_description', 160);
    }
});