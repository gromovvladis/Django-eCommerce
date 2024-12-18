let phoneInput = document.querySelector('#id_username');
let phoneStr = '';
let formattedStr = '';
let deleteMode = false;

const defaultFormat = '+7 ({0}{1}{2}) {3}{4}{5}-{6}{7}{8}{9}';

if (phoneInput){
    phoneInput.addEventListener('keydown', (e) => {
        deleteMode = (e.key === 'Backspace');
    });
        
    phoneInput.addEventListener('input', (e) => {
        if (deleteMode) {
            phoneInput.value = phoneInput.value;
            phoneStr = parsePhoneString(phoneInput.value);
        } else {
            if (e.inputType == 'insertText' && !isNaN(parseInt(e.data))) {
                if (phoneStr.length <= 10){
                    phoneStr += e.data;
                }
            }
            phoneInput.value = formatPhoneString();
        }
    });
}

if (typeof codeInput !== 'undefined') {
    codeInput.addEventListener('input', function(){
        codeInput.value = codeInput.value.replace (/\D/g, '');
        if (codeInput.value.length == 4){
            $(btn_auth).prop("disabled", false);
        } else {
            $(btn_auth).prop("disabled", true); 
        }
    })
    
    codeInput.addEventListener('keypress', function (e) {
        var key = e.which || e.keyCode;
        if (key === 13) {
            btn_auth.click();
        }
    });
}

function formatPhoneString() {
    let strArr = phoneStr.split('');
    formattedStr = defaultFormat;
    for (let i = 0; i < strArr.length; i++) {
        formattedStr = formattedStr.replace(`{${i}}`, strArr[i]);
    }
    
    if (formattedStr.indexOf('{') === -1)
        return formattedStr;
    else
        return formattedStr.substring(0, formattedStr.indexOf('{'));
    
}

function parsePhoneString(str) {
    return str.replace('+7', '').replace(' ', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '');
}